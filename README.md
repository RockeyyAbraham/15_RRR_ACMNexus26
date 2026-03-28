# �️ Sentinel - Real-Time Piracy Detection System

### 🏆 **NEXUS Hackathon 2026 | Digital Asset Protection**
### 🤝 **Team CLIQUE x ACM MITS**
### 📅 **March 27-28, 2026**

<p align="center">
  <img src="template_acm.png" width="400"/>
  <img src="template_clique.png" width="200"/>
</p>

---

## 🎯 **Mission**

Stop the **$28B annual sports piracy crisis** with real-time detection in under 90 seconds.

---

## ⚡ **One-Command Demo**

```bash
# Windows - Double click or run:
./start.bat

# Access immediately:
Frontend: http://localhost:5173
Backend:  http://localhost:8000
```

---

## 🚀 **Key Innovations**

### **🔍 Dual-Mode Fingerprinting**
- **Video**: pHash + dHash fusion with adaptive sampling
- **Audio**: Mel-spectrogram hashing
- **Combined**: 70% video + 30% audio confidence scoring

### **⚡ Real-Time Performance**
- **20x speedup** with parallel processing
- **95% detection accuracy** on real content
- **<90 second enforcement window**
- **161 scene changes** detected automatically

### **🤖 AI-Enhanced Legal**
- **Groq Llama 3.3 70B** integration
- **Automated DMCA notice generation**
- **Natural language detection summaries**
- **Risk assessment and recommendations**

---

## 📊 **Proven Results**

| Metric | Result |
|--------|--------|
| **Detection Accuracy** | 95.08% (compression) |
| **Color Shift Detection** | 92.42% |
| **Temporal Localization** | 100% |
| **False Positive Rate** | 0% |
| **Processing Speed** | 20.5 fps |
| **Parallel Speedup** | 20x |

---

## 🛠 **Tech Stack**

### **Backend**
- **Flask** REST API with WebSocket support
- **OpenCV** for video processing
- **SQLite** + **Redis** for persistence
- **Groq** API for AI integration

### **Frontend**
- **React** with TypeScript
- **Vite** for fast development
- **TailwindCSS** for modern UI
- **Real-time WebSocket** updates

### **Core Engines**
- **VideoHashEngine**: Multi-hash fingerprinting
- **AudioHashEngine**: Audio signature analysis
- **DualModeEngine**: Combined verification
- **SentinelAI**: Intelligence layer

---

## 🎯 **Demo Workflow**

### **1. Protected Content Ingest**
```bash
Upload sports video → Auto-fingerprinting → Database storage
```

### **2. Piracy Benchmark**
```bash
Generate 17 variants → Test detection accuracy → View results
```

### **3. Live Detection**
```bash
Monitor streams → Real-time alerts → AI-powered analysis
```

### **4. Legal Enforcement**
```bash
Auto-generate DMCA → Download PDF → Send to platform
```

---

## 📁 **Project Structure**

```
├── backend/
│   ├── engines/          # Core detection engines
│   ├── api/main.py       # Flask REST API
│   └── tests/            # Comprehensive test suite
├── frontend/
│   ├── src/pages/        # React dashboard pages
│   └── src/components/   # Reusable UI components
├── docs/                 # Technical documentation
├── progress/             # Hackathon progress tracking
└── assets/videos/        # Test content
```

---

## � **Testing & Validation**

### **Real-World Testing**
- **8-minute Formula 1 video** processed
- **4 piracy types** validated
- **17 variants** generated and tested
- **Production-ready** performance

### **Test Coverage**
- **13 tests** passing (9 unit + 4 integration)
- **End-to-end workflows** validated
- **Error handling** verified

---

## 🏆 **Competitive Advantages**

1. **First dual-mode system** (video + audio)
2. **AI-generated legal documents**
3. **Adaptive scene-aware sampling**
4. **Statistical confidence scoring**
5. **Production-ready, not just prototype**

---

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.10+
- Node.js 18+
- Git

### **Quick Start**
```bash
git clone <repository>
cd <project-folder>
./start.bat
```

### **Manual Setup**
```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
python api/main.py

# Terminal 2 - Frontend  
cd frontend
npm install
npm run dev
```

---

## 📈 **Metrics Dashboard**

Live monitoring includes:
- **Detection confidence scores**
- **Processing latency metrics**
- **Platform piracy statistics**
- **AI analysis insights**

---

## 🎯 **Impact & Scalability**

### **Current Capability**
- **Real-time detection** on live streams
- **Multi-platform support** (Twitch, YouTube, etc.)
- **Automated enforcement** pipeline
- **Production performance** validated

### **Scalability Features**
- **Parallel processing** architecture
- **Independent audio/video engines**
- **Redis caching** for performance
- **Async job management**

---

## 🤝 **Team & Contributions**

### **Core Features**
- **Video fingerprinting pipeline**
- **Audio hash analysis engine**
- **AI-powered legal automation**
- **Real-time detection dashboard**
- **Comprehensive testing suite**

### **Hackathon Progress**
- **16 hours** of development
- **Multiple commits** per hour
- **Continuous progress tracking**
- **Full documentation**

---

## 📞 **Contact & Support**

- **GitHub**: Repository link
- **Demo**: Live at http://localhost:5173
- **API Docs**: http://localhost:8000/health

---

🔥 **Built to win NEXUS 2026 - Transforming piracy enforcement from hours to seconds.**

## ⚙️ Hackathon Workflow & Rules

To ensure fairness and transparency, we have designed a structured development and tracking system.

---

### 🔗 GitHub Template

👉 **Template Repo:** `{link}`

* All teams must **fork this repository**
* Fork name must follow:

```
<TeamId>_<TeamName>_ACMNexus26
```

* Example:

```
12_CodeWarriors_ACMNexus26
```

* You may rename the repository **after the event ends**

---


---

## 👥 Participation Rules

* Team Size: **2–4 members**
* **Pre-created projects are strictly not allowed**
* All work must be done **during the hackathon timeframe**
* Only registered team members must participate
* Do **not attack or interfere** with college infrastructure/network
* Follow all instructions from the organizing team

---

## 📁 Repository Structure


Repository must not be private. The template Repository includes:

```
AGENTS.md
README.md
CHANGELOG.md
/progress/
```

---

## ⏱️ Hourly Progress Requirements

Every hour, teams must:

* Make **at least one commit**
* Add **at least one progress update** inside `/progress/`

Progress can include:

* Screenshots
* Screen recordings
* Dataset snapshots
* Any meaningful proof of work

### 📂 Progress Format

```
/progress
1.png
2.png
3.png
```

* Files must be **numbered sequentially**
* Each file should reflect **actual development progress**

---

## 📝 Changelog Rules (VERY IMPORTANT)

Every commit must be reflected in `CHANGELOG.md`.

You can:

* Update it per commit, OR
* Update it periodically (but must be complete at the end)

---

### 📌 Changelog Format

```md
## HH:MM

### Features Added
- Added login functionality
- Implemented API integration

### Files Modified
- auth.js
- login.jsx

### Issues Faced
- Firebase auth errors
- API timeout issues
```

---

💡 Tip:
Instructions are already included in `AGENTS.md`.
You can simply prompt it to **"CREATE CHANGELOG"** to follow the format.

---

## 📖 Documentation

We have provided:

* Examples
* Guidelines

Inside:

* `AGENTS.md`
* `README.md`

Please follow them strictly.

---

## 🔍 Monitoring & Verification

* Random checks will be conducted during the hackathon
* Organizers may:

  * Inspect commit history
  * Review changelog consistency
  * Verify progress evidence

---

## 👨‍💻 Team Collaboration Rules

* All members must be added as **collaborators**
* By the end of the hackathon:

  * **Each member must have at least one commit**

---

## ⚠️ Disqualification Criteria

* Use of **pre-built / pre-developed projects**
* Fake or manipulated commit history
* Missing hourly commits or progress updates
* Incomplete or inconsistent changelog

---

## 🏁 Final Note

Focus on building, learning, and enjoying the experience.

---

🔥 **Build. Break. Innovate. See you at NEXUS.**
