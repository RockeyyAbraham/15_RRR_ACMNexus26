# ⚡ QUICK FIX - Backend Not Starting

## The Issue:
The backend wasn't starting due to Python import path issues. **This is now fixed.**

## ✅ What Was Fixed:
1. Added `sys.path` fix to `backend/api/main.py`
2. Created import test script
3. Updated startup scripts

---

## 🚀 Start Backend Now:

### **Option 1: Use the fixed startup script**
```cmd
start.bat
```

### **Option 2: Manual start (to see errors)**
```cmd
cd backend
python api/main.py
```

You should now see:
```
================================================================================
SENTINEL BACKEND STARTING
================================================================================
Error logs: C:\...\backend\logs\error.log
...
* Running on http://127.0.0.1:8000
```

---

## ✅ Verify Backend is Running:

```powershell
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "online",
  "engines": ["hashing", "matching", "audio", ...],
  "timestamp": "..."
}
```

---

## 🎯 Once Backend Starts:

1. **Refresh your browser** at `http://localhost:5173`
2. The "Fingerprint generation failed" error will disappear
3. You'll see **real data** instead of mock data

---

## If Still Not Working:

Check the **Sentinel Backend** terminal window for errors. Common issues:

### Missing dependencies:
```cmd
cd backend
pip install flask flask-cors flask-sock opencv-python imagehash pillow numpy reportlab groq librosa redis python-dotenv requests soundfile fakeredis
```

### Port 8000 in use:
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

**The fix is applied. Just run `start.bat` again!**
