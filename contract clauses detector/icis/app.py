"""
ICIS — Contract Workbench (Flask + OCR + Vanilla Frontend)

Run:
  python -m venv .venv
  # Windows: .venv\\Scripts\\activate
  # macOS/Linux: source .venv/bin/activate
  pip install -r requirements.txt
  python app.py
Open: http://127.0.0.1:5000

System deps (required):
  macOS:  brew install tesseract poppler
  Ubuntu: sudo apt-get install -y tesseract-ocr poppler-utils
  Windows: Install Tesseract (add to PATH) + Poppler; set POPPLER_PATH to its 'bin' dir if needed.
"""

from __future__ import annotations
import os, re, shutil, sys, tempfile
from datetime import datetime
from typing import List, Dict, Any, Iterable

from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename
from db import db
from models import Draft

# ----- Fail fast: OCR deps -----
TESS_OK = shutil.which("tesseract") is not None
POPPLER_BIN = os.environ.get("POPPLER_PATH")  # optional on Windows
PDFTOPPM_OK = bool(POPPLER_BIN) or (shutil.which("pdftoppm") is not None)
if not TESS_OK:
    sys.stderr.write(
        "\n[OCR ERROR] Tesseract not found.\n"
        "Install:\n  macOS: brew install tesseract\n  Ubuntu: sudo apt-get install tesseract-ocr\n"
        "  Windows: Install UB Mannheim build and add to PATH\n\n"
    ); sys.exit(2)
if not PDFTOPPM_OK:
    sys.stderr.write(
        "\n[OCR ERROR] Poppler not found.\n"
        "Install:\n  macOS: brew install poppler\n  Ubuntu: sudo apt-get install poppler-utils\n"
        "  Windows: Download Poppler and set POPPLER_PATH to its 'bin'\n\n"
    ); sys.exit(2)

# ----- OCR libs -----
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".pdf"}

# ----- Flask -----
app = Flask(__name__, static_url_path="/static", static_folder="static", template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///icis.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
db.init_app(app)
with app.app_context(): db.create_all()

# ----- Parsing helpers -----
HEADING_RE = re.compile(r"""
^\s*( (?:Section|Clause|Article)\s+\d+ | \d+(?:\.\d+){0,3} | [A-Z][\.)]\s+ |
[IVXLC]+\.\s+ | [A-Z][a-zA-Z\s]{2,30}:? )\s*$
""", re.IGNORECASE | re.VERBOSE | re.MULTILINE)
BULLET_RE = re.compile(r"^\s*[-•*]\s+", re.MULTILINE)

def _split_lines(text: str) -> List[str]:
    text = re.sub(r"\r\n?", "\n", text); text = re.sub(r"[ \t]+"," ", text)
    return [ln.strip() for ln in text.split("\n")]

def extract_sections(text: str) -> List[Dict[str, Any]]:
    lines = _split_lines(text); sections = []; curr_title=None; curr_body=[]
    def flush():
        if curr_title or curr_body:
            raw = (curr_title or "") + "\n" + "\n".join(curr_body)
            sections.append({"title": (curr_title or "Untitled").strip(),
                             "body": "\n".join(curr_body).strip(), "raw": raw.strip()})
    for ln in lines:
        if not ln: 
            if curr_body and curr_body[-1]!="": curr_body.append(""); continue
        if HEADING_RE.match(ln): flush(); curr_title=ln; curr_body=[]; continue
        if BULLET_RE.match(ln) and curr_body: curr_body.append(ln); continue
        curr_body.append(ln)
    flush()
    if len(sections)==1 and sections[0]["title"].lower()=="untitled":
        paras=[p.strip() for p in sections[0]["body"].split("\n\n") if p.strip()]
        sections=[{"title":f"Para {i+1}","body":p,"raw":p} for i,p in enumerate(paras)]
    return sections

# ----- Rules -----
RISK_RULES = [
  {"id":"uncapped_liability","label":"Uncapped Liability","severity":"High","party":"Vendor",
   "pattern": re.compile(r"(unlimited|uncapped|no\s+cap).*liabilit(y|ies)|liability\s+shall\s+be\s+unlimited", re.I|re.S),
   "suggestion":"Cap aggregate liability (e.g., 12 months of fees) and exclude indirect damages except carve-outs (IP, confidentiality).",
   "where":["liability","limitation","limitation of liability"]},
  {"id":"broad_indemnity","label":"Broad/Asymmetric Indemnity","severity":"Medium","party":"Customer",
   "pattern": re.compile(r"(customer|licensee|employer).{0,40}shall\s+indemnif(y|ies).{0,60}(any|all)\s+claims", re.I|re.S),
   "suggestion":"Narrow to third-party IP claims; make indemnity mutual; exclude misuse and unauthorized modifications.",
   "where":["indemnity","indemnification"]},
  {"id":"ambiguous_t4c","label":"Ambiguous Termination for Convenience","severity":"Low","party":"Shared",
   "pattern": re.compile(r"terminate\s+for\s+convenience(?!.*\d{1,2}\s*day)", re.I|re.S),
   "suggestion":"Define notice period (e.g., 30 days) and any early termination fees or specify none.",
   "where":["termination","term","termination for convenience"]},
  {"id":"narrow_force_majeure","label":"Narrow Force Majeure","severity":"Medium","party":"Shared",
   "pattern": re.compile(r"force\s+majeure(?!.*(epidemic|pandemic|government\s+restriction|quarantine))", re.I|re.S),
   "suggestion":"Include epidemics/pandemics and government restrictions; require notice and mitigation.",
   "where":["force majeure","excusable delay"]},
  {"id":"payment_ambiguity","label":"Ambiguous Payment Schedule","severity":"High","party":"Contractor",
   "pattern": re.compile(r"(payment|remittance|consideration).{0,80}(due|within)\s*(\d+)?\s*(days|day)?", re.I|re.S),
   "negate_if": re.compile(r"(milestone|stage|schedule|retention|bank\s+details|invoice\s+date|net\s+\d+)", re.I),
   "suggestion":"Specify milestone schedule, due dates, invoice reference, bank details; define retention and release trigger.",
   "where":["payment","commercials","fees"]},
  {"id":"uncapped_lds","label":"Uncapped Liquidated Damages","severity":"High","party":"Employer",
   "pattern": re.compile(r"(liquidated\s+damages|ld[’']?s?).{0,80}(unlimited|uncapped|no\s+cap)", re.I|re.S),
   "suggestion":"Introduce bilateral cap (e.g., 10% of Contract Price); state LDs are sole remedy for delay.",
   "where":["liquidated damages","delay","performance security"]},
  {"id":"confidentiality_no_carveout","label":"Confidentiality Missing Carve-outs","severity":"Low","party":"Shared",
   "pattern": re.compile(r"confidential(ity)?(?!.*(public|already\s+known|independent|third\s+party)).{0,200}", re.I|re.S),
   "suggestion":"Add carve-outs: public/known, independently developed, or rightfully received from third parties.",
   "where":["confidentiality","nda"]},
  {"id":"ip_assignment_asymmetry","label":"Asymmetric IP Assignment","severity":"Medium","party":"Vendor",
   "pattern": re.compile(r"(assign|transfer).{0,40}all\s+ip\s+rights(?!.*license\s+back)", re.I|re.S),
   "suggestion":"Use license grant or assignment with license-back; clarify pre-existing IP ownership.",
   "where":["intellectual property","ownership","ip"]},
]

def _guess_title(sec): 
    t = re.sub(r"^\d+(?:\.\d+)*[\.)]?\s*", "", (sec.get("title") or "")).strip()
    return (t or (sec.get("body") or "").split(".")[0][:40] or "Clause")[:60]

def _ctx(sec, where): return any(w.lower() in (sec.get("raw") or "").lower() for w in where)

def analyze_text(text: str) -> Dict[str, Any]:
    sections = extract_sections(text); issues=[]
    for sec in sections:
        raw = sec.get("raw", "")
        for rule in RISK_RULES:
            if "where" in rule and not _ctx(sec, rule["where"]): continue
            if not rule["pattern"].search(raw): continue
            if "negate_if" in rule and rule["negate_if"].search(raw): continue
            issues.append({"id": f"{rule['id']}-{len(issues)+1}",
                           "clause": _guess_title(sec), "issue": rule["label"],
                           "risk": rule["severity"], "party": rule["party"],
                           "suggestion": rule["suggestion"]})
    hi=sum(i["risk"]=="High" for i in issues); med=sum(i["risk"]=="Medium" for i in issues); low=sum(i["risk"]=="Low" for i in issues)
    return {"summary": f"{len(issues)} issues detected ({hi} High, {med} Medium, {low} Low).", "issues": issues}

def synthesize_draft(base_text: str, issues: List[Dict[str, Any]], author: str) -> str:
    header = f"\n\n— — —\nADDENDUM — Risk-Refined Draft (Author: {author})\n"
    body = "\n".join([f"A{idx}. Clause: {i['clause']}\nIssue: {i['issue']}\nChange: {i['suggestion']}\n"
                      for idx,i in enumerate(issues,1)])
    return f"{base_text}{header}{body}\nNotes: Machine-assisted. Review with counsel."

# ----- OCR helpers -----
def allowed_file(name:str)->bool: return os.path.splitext(name.lower())[1] in ALLOWED_EXTS
def ocr_image(path:str, lang="eng")->str:
    with Image.open(path) as im:
        return pytesseract.image_to_string(im.convert("L"), lang=lang)
def ocr_pdf(path:str, lang="eng")->str:
    pages = convert_from_path(path, fmt="png", dpi=300, poppler_path=POPPLER_BIN)
    return "\n\n".join(pytesseract.image_to_string(p.convert("L"), lang=lang) for p in pages)

# ----- Routes -----
@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "ts": datetime.utcnow().isoformat()+"Z"})

@app.post("/api/analyze")
def api_analyze():
    data = request.get_json(silent=True) or {}; text = (data.get("text") or "").strip()
    if not text:
        text = ("3. Payment Terms\nPayment is due promptly. Retention later.\n\n"
                "7. Limitation of Liability\nLiability shall be unlimited in all cases.\n")
    return jsonify(analyze_text(text))

@app.post("/api/analyze_file")
def api_analyze_file():
    if "file" not in request.files: return jsonify({"error":"file required"}), 400
    f = request.files["file"]; name = secure_filename(f.filename or "")
    if not name: return jsonify({"error":"empty filename"}), 400
    if not allowed_file(name): return jsonify({"error":"unsupported file type"}), 400
    lang = request.form.get("lang","eng")
    _,ext = os.path.splitext(name.lower())
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        f.save(tmp.name); path = tmp.name
    try:
        text = ocr_pdf(path, lang) if ext==".pdf" else ocr_image(path, lang)
        analysis = analyze_text(text or "")
        return jsonify({"extracted_text": text, "analysis": analysis})
    finally:
        try: os.remove(path)
        except OSError: pass

@app.post("/api/create-draft")
def api_create_draft():
    d = request.get_json(force=True) or {}
    return jsonify({"draft_text": synthesize_draft(d.get("base_text",""), d.get("issues", []), d.get("author","ICIS"))})

@app.post("/api/drafts")
def api_save_draft():
    d = request.get_json(force=True) or {}
    title = d.get("title", f"Draft v{int(datetime.utcnow().timestamp())}")
    content = d.get("content","")
    if not content.strip(): return jsonify({"error":"content required"}), 400
    draft = Draft(title=title, content=content, issues=d.get("issues", []))
    db.session.add(draft); db.session.commit()
    return jsonify(draft.to_dict())

@app.get("/api/drafts")
def api_list_drafts():
    drafts = Draft.query.order_by(Draft.created_at.desc()).all()
    return jsonify([x.to_dict() for x in drafts])

@app.get("/api/drafts/<int:did>")
def api_get_draft(did:int):
    d = Draft.query.get_or_404(did); return jsonify(d.to_dict())

if __name__ == "__main__":
    app.run(debug=True)
