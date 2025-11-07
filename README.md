✅ Data-Driven Failure Detection and Automatic Recovery using Reinforcement Learning  
*A Real-Time Self-Healing System for Software Failures*

---

📌 Overview  
This project is a **web-based intelligent monitoring and auto-recovery system** that detects software failures, identifies the cause, and repairs the issue using **Reinforcement Learning (RL)**.

Instead of using a fixed dataset, the system **collects real-time computer metrics** (CPU, memory, disk, running processes) and automatically learns the best recovery actions over time.

The dashboard displays:  
- ✅ Live system metrics  
- ✅ Failure type  
- ✅ Affected application  
- ✅ Suggested recovery solution  
- ✅ RL actions and logs  
- ✅ Real-time alerts on failures  

---

✨ Key Features  

🔍 1. Real-Time Failure Detection  
- Monitors CPU, memory, and disk usage using `psutil`  
- Identifies failure types:  
  - CPU Overload  
  - Memory Leak  
  - Disk Full  
  - Normal State  

🧠 2. Intelligent Root Cause Identification  
- Detects which process or application causes abnormal behavior  
- Displays the exact application name on the dashboard  

🛠️ 3. Automatic Recovery Using Reinforcement Learning  
- Built with **Stable Baselines3 (PPO/DQN)**  
- RL Agent automatically selects the best recovery action:  
  - 🔁 Restart service  
  - ⚙️ Scale up resources  
  - ✅ Do nothing (if stable)  
- Improves continuously through feedback and rewards  

🌐 4. Live Web Dashboard  
Developed using **HTML + CSS + JavaScript + Chart.js**, featuring:  
- System health indicators  
- Live performance charts  
- Failure details  
- Affected process  
- Suggested recovery solution  
- RL action logs  
- Popup alerts  
- Buttons: Train AI, Simulate Failure, Recover  

💾 5. Local Database Storage  
Uses **SQLite** (via SQLAlchemy) to log:  
- Historical system metrics  
- Failure events  
- RL actions and rewards  
- Suggested fixes  

---

🗂️ Project Structure  
DataDrivenFailureDetection/  
├── app.py              (Flask backend - API + UI)  
├── rl_agent.py         (Reinforcement learning logic)  
├── simulator.py        (Real-time metric generator using psutil)  
├── database.py         (SQLite setup using SQLAlchemy)  
├── models.py           (ORM Models - Metric, Action, Event)  
├── requirements.txt  
├── static/  
│   ├── style.css       (Dashboard design - neon/glow theme)  
│   └── script.js       (Frontend JS logic + API calls)  
└── templates/  
    └── index.html      (Web dashboard - UI)  

---

🧰 Technologies Used  

⚙️ Backend  
- Python 3.11+  
- Flask 3.x  
- psutil  
- SQLAlchemy  
- Stable Baselines3 (RL)  
- SQLite  

💻 Frontend  
- HTML5  
- CSS3 (Neon / Glow UI)  
- JavaScript (Fetch + Chart.js)  

---

🚀 How to Run  

1️⃣ Clone the Repository  
git clone https://github.com/<your-username>/DataDrivenFailureDetection.git  
cd DataDrivenFailureDetection  

2️⃣ Create a Virtual Environment  
python -m venv venv  
source venv/bin/activate   (Mac/Linux)  
venv\Scripts\activate      (Windows)  

3️⃣ Install Dependencies  
pip install -r requirements.txt  

4️⃣ Run the Flask App  
python app.py  

5️⃣ Open in Browser  
http://127.0.0.1:5000  

Now you’ll see your **live monitoring dashboard** 🎯  

---

🧪 Usage Guide  

▶️ Train AI  
Click the Train AI button — the RL agent starts learning optimal recovery strategies.  

⚠️ Simulate Failure  
Creates artificial system stress (CPU, memory, or disk).  

🔄 Auto-Recovery  
Click Recover — the trained RL agent selects the best corrective action.  

📊 Live Monitoring  
Charts refresh every 5 seconds showing real-time health.  

---

🧠 Internal Workflow  

✅ Step 1 — Collect Real-Time Metrics  
Uses `psutil` to get:  
- CPU %  
- Memory %  
- Disk usage  
- Active process list  

✅ Step 2 — Detect Failures  
Rule-based classification:  

Condition → Failure Type  
CPU > 90% → CPU Overload  
Memory > 85% → Memory Leak  
Disk > 90% → Disk Full  
Else → Normal  

✅ Step 3 — Identify Affected App  
Detects the process using max CPU or memory.  

✅ Step 4 — Suggest Fix  
Maps failure → recommended recovery (restart, scale, etc.).  

✅ Step 5 — RL Chooses Action  
State → Action → Reward → Policy Update (using PPO or DQN).  

✅ Step 6 — Log All Data  
Stores everything in SQLite for history/training.  

---

📊 Example Dashboard Layout  

Metric → Example  
CPU Usage → 94% (Overload)  
Memory Usage → 88% (Leak)  
Disk Usage → 60% (Normal)  
Failure Type → CPU Overload  
Affected App → chrome.exe  
Suggested Fix → Restart Service  
RL Action → Action: Restart  

---

🔮 Future Improvements  
- 🤖 Continuous (Online) RL training  
- ☁️ Multi-agent RL for distributed clusters  
- 🔍 Predictive failure detection using LSTM or Random Forest  
- 💬 LLM-based root cause explanations  
- 📱 Mobile app or web extension  
- 🔒 Add network/security failure monitoring  

---

💡 Why This Project Matters  
- Software systems fail due to overload or resource leaks.  
- Manual recovery is slow and reactive.  
- Traditional monitoring uses static thresholds.  
- This project enables **self-healing AI infrastructure** — auto-detect, auto-repair, auto-learn.  
- Reduces downtime, improves system reliability, and supports AIOps transformation.  

---

❤️ Contributors  
Shaik Sazad Akthar — AI Engineer & Developer  

---

📜 License  
This project is licensed under the MIT License.  
You can freely use, modify, and distribute it.  

---

⚙️ requirements.txt  
Flask==3.0.3  
SQLAlchemy==2.0.30  
psutil==5.9.8  
stable-baselines3==2.3.2  
gymnasium==0.29.1  
numpy==1.26.4  
pandas==2.2.2  
matplotlib==3.9.0  
chart-studio==1.1.0  
torch==2.2.2  

(These versions are stable and compatible with your RL + Flask integration as of 2025.)

---

🧱 Recommended Repo Layout  
DataDrivenFailureDetection/  
├── app.py  
├── rl_agent.py  
├── simulator.py  
├── database.py  
├── models.py  
├── requirements.txt  
├── README.md  
├── static/  
│   ├── style.css  
│   └── script.js  
└── templates/  
    └── index.html  

Then initialize Git:  
git add .  
git commit -m "Initial commit - Data-Driven Failure Detection System"  
git push origin main  
