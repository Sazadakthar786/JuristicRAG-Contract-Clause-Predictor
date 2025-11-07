const el = (q) => document.querySelector(q);
const els = (q) => Array.from(document.querySelectorAll(q));

const pages = els('[data-page]');
const nav = el('#nav');
const themeToggle = el('#themeToggle');

const state = { clauses: [], selected: null, history: [] };

// Theme
const savedTheme = localStorage.getItem('icis-theme');
if(savedTheme==='light') document.documentElement.classList.add('light');
themeToggle.checked = document.documentElement.classList.contains('light');
themeToggle.addEventListener('change', () => {
  document.documentElement.classList.toggle('light');
  localStorage.setItem('icis-theme', document.documentElement.classList.contains('light')?'light':'dark');
});

// Tabs
function show(tab){
  els('.nav button').forEach(b=>b.classList.toggle('active', b.dataset.tab===tab));
  pages.forEach(p=>p.classList.toggle('hidden', p.dataset.page!==tab));
}
nav.addEventListener('click', (e)=>{ const btn = e.target.closest('button[data-tab]'); if(!btn) return; show(btn.dataset.tab); });
els('[data-jump]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.jump)));

// Toast
let __t; function toast(msg, ok){
  const t = el('#toast'); t.textContent = msg; t.classList.add('show');
  t.style.color = ok ? '#10b981' : 'inherit'; clearTimeout(__t); __t=setTimeout(()=>t.classList.remove('show'),1500);
}

// Analyze (text)
const contractText = el('#contractText');
const runBtn = el('#run'); const copyBtn = el('#copyIn');
copyBtn.addEventListener('click', async ()=>{ await navigator.clipboard.writeText(contractText.value||''); toast('Copied input', true); });
runBtn.addEventListener('click', async ()=>{
  if(!contractText.value){ /* allow empty -> sample on server */ }
  runBtn.disabled = true; runBtn.textContent = 'Analyzing…';
  const res = await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:contractText.value||''})});
  const data = await res.json();
  state.clauses = data.issues||[]; state.selected = state.clauses[0]||null;
  renderClauses(); renderClauseDetail(); show('results'); toast(data.summary||'Analysis complete', true);
  runBtn.disabled = false; runBtn.textContent = 'Run Analysis';
});

// Analyze (OCR file)
const fileInput = el('#file'), fileName = el('#fileName'), drop = el('#drop'), runFile = el('#runFile'), ocrLang = el('#ocrLang');
function setFileName(name){ fileName.textContent = name ? 'Selected: '+name : ''; }
fileInput.addEventListener('change', e=> setFileName(e.target.files?.[0]?.name || ''));
drop.addEventListener('dragover', e=>{ e.preventDefault(); drop.classList.add('is-hover'); });
drop.addEventListener('dragleave', ()=> drop.classList.remove('is-hover'));
drop.addEventListener('drop', e=>{ e.preventDefault(); drop.classList.remove('is-hover'); const f=e.dataTransfer.files?.[0]; if(f){ fileInput.files=e.dataTransfer.files; setFileName(f.name);} });
runFile.addEventListener('click', async ()=>{
  const f = fileInput.files?.[0]; if(!f){ toast('Choose a file first'); return; }
  const fd = new FormData(); fd.append('file', f); fd.append('lang', ocrLang.value||'eng');
  runFile.disabled=true; runFile.textContent='OCR…';
  try{
    const res = await fetch('/api/analyze_file',{ method:'POST', body: fd });
    const data = await res.json(); if(!res.ok) throw new Error(data.error || 'OCR failed');
    contractText.value = data.extracted_text || '';
    state.clauses = (data.analysis && data.analysis.issues) || []; state.selected = state.clauses[0]||null;
    renderClauses(); renderClauseDetail(); show('results'); toast('OCR + analysis complete', true);
  }catch(e){ console.error(e); toast(e.message || 'OCR failed'); }
  finally{ runFile.disabled=false; runFile.textContent='Analyze File (OCR)'; }
});

// Results rendering
const clausesEl = el('#clauses'); const detailEl = el('#clauseDetail'); const createDraftBtn = el('#createDraft');
function badge(sev){ if(sev==='High') return '<span class="badge b-high">High</span>'; if(sev==='Medium') return '<span class="badge b-med">Medium</span>'; return '<span class="badge b-low">Low</span>'; }
function renderClauses(){
  if(!state.clauses.length){ clausesEl.innerHTML = '<div class="muted">No results yet. Run analysis.</div>'; return;}
  clausesEl.innerHTML = state.clauses.map(c=>`
   <div class="clause ${state.selected?.id===c.id?'active':''}" data-id="${c.id}">
     <div class="row" style="justify-content:space-between"><strong>${c.clause}</strong>${badge(c.risk)}</div>
     <div class="muted" style="margin-top:6px">${c.issue}</div>
     <div class="row" style="margin-top:8px;gap:6px;flex-wrap:wrap"><span class="chip">${c.suggestion}</span></div>
   </div>`).join('');
}
function renderClauseDetail(){
  const c = state.selected; if(!c){ detailEl.textContent='Select a clause to view details.'; return; }
  detailEl.innerHTML = `
   <div class="row" style="justify-content:space-between;align-items:center">
     <div class="row"><strong>${c.clause}</strong></div>${badge(c.risk)}
   </div>
   <div class="card" style="margin-top:8px">${c.issue}</div>
   <div style="margin-top:8px"><div><strong>Suggested Fix</strong></div><ul><li>${c.suggestion}</li></ul></div>`;
}
clausesEl.addEventListener('click', (e)=>{ const item = e.target.closest('.clause'); if(!item) return; state.selected = state.clauses.find(x=>x.id===item.dataset.id); renderClauses(); renderClauseDetail(); });

// Draft + History
const draftText = el('#draftText'); const saveVersion = el('#saveVersion'); const historyEl = el('#history');
createDraftBtn.addEventListener('click', async ()=>{
  const res = await fetch('/api/create-draft',{method:'POST',headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ base_text: el('#contractText').value || '', issues: state.clauses, author:'ICIS' })});
  const data = await res.json(); draftText.value = data.draft_text || ''; show('draft'); toast('Draft generated from findings.', true);
});
saveVersion.addEventListener('click', async ()=>{
  const text = draftText.value.trim(); if(!text){ toast('Nothing to save.'); return; }
  const resp = await fetch('/api/drafts',{method:'POST',headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ title:`Draft v${Date.now()}`, content:text, issues: state.clauses })});
  if(!resp.ok){ const e=await resp.json(); toast(e.error||'Save failed'); return;}
  await refreshHistory(); toast('Version saved to History.', true);
});
async function refreshHistory(){
  const r = await fetch('/api/drafts'); const arr = await r.json();
  historyEl.innerHTML = arr.map(d=>`
   <div class="card">
     <div class="row" style="justify-content:space-between">
       <strong>${esc(d.title)}</strong><span class="chip">${new Date(d.created_at).toLocaleString()}</span>
     </div>
     <div class="muted" style="margin-top:6px;white-space:pre-wrap">${esc((d.content||'').slice(0,160))}${(d.content||'').length>160?'…':''}</div>
   </div>`).join('');
}
function esc(s){ return String(s||'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }
refreshHistory();

// Export PDF
el('#exportPdf').addEventListener('click', async ()=>{
  const main = el('#main'); toast('Exporting to PDF…');
  const canvas = await html2canvas(main, {scale:2});
  const { jsPDF } = window.jspdf; const pdf = new jsPDF({ unit:'pt', format:'a4' });
  const w = pdf.internal.pageSize.getWidth(); const h = (canvas.height * w) / canvas.width;
  pdf.addImage(canvas.toDataURL('image/png'),'PNG',0,0,w,h); pdf.save('ICIS-draft.pdf'); toast('Exported PDF.', true);
});
