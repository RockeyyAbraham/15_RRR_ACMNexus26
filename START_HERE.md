# 🚀 START SENTINEL - ONE COMMAND

## Windows Users (Recommended)

### **Option 1: Double-click the file**
Just double-click: **`start.bat`**

### **Option 2: Run from terminal**
```cmd
start.bat
```

### **Option 3: PowerShell**
```powershell
.\start.ps1
```

---

## What Happens:

1. ✅ Checks Python and Node.js are installed
2. ✅ Installs all backend dependencies
3. ✅ Installs all frontend dependencies
4. ✅ Starts backend in a new window
5. ✅ Starts frontend in a new window

---

## After Running:

You'll see **2 new terminal windows** open:

### **Window 1: Backend**
```
================================================================================
SENTINEL BACKEND STARTING
================================================================================
* Running on http://127.0.0.1:8000
```

### **Window 2: Frontend**
```
VITE v5.x.x ready in xxx ms
➜ Local: http://localhost:5173/
```

---

## Access the Application:

- **Frontend UI:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Health Check:** http://localhost:8000/health
- **Detailed Docs:** `docs/README.md`

---

## If You See Errors:

### **"Python not found"**
Install Python 3.10+ from: https://www.python.org/downloads/

### **"Node.js not found"**
Install Node.js 18+ from: https://nodejs.org/

### **Backend errors**
Check: `backend\logs\error.log`

### **Port already in use**
Kill the process:
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## To Stop:

Close both terminal windows or press `Ctrl+C` in each window.

---

## Manual Start (if script fails):

### Terminal 1:
```cmd
cd backend
pip install -r requirements.txt
python api/main.py
```

### Terminal 2:
```cmd
cd frontend
npm install
npm run dev
```

---

**That's it! Just run `start.bat` and you're good to go!** 🎉
