# 🔍 Error Checking Guide

## Where to Find Error Logs

### Backend Errors
```bash
# Main error log (all errors with stack traces)
cat backend/logs/error.log

# Or on Windows
type backend\logs\error.log

# Watch errors in real-time
tail -f backend/logs/error.log  # Linux/macOS
Get-Content backend\logs\error.log -Wait  # Windows PowerShell
```

### Frontend Errors
Frontend errors appear in:
1. **Browser Console** (F12 → Console tab)
2. **Terminal** where `npm run dev` is running

---

## Quick Error Check Commands

### Check if backend is running:
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "online",
  "engines": ["hashing", "matching", "audio", "generator", "ai", "redis"],
  "timestamp": "2026-03-28T03:17:00"
}
```

### Check for Python errors:
```bash
# View last 50 lines of error log
tail -n 50 backend/logs/error.log  # Linux/macOS
Get-Content backend\logs\error.log -Tail 50  # Windows
```

### Check for missing dependencies:
```bash
cd backend
pip list | grep -E "flask|opencv|imagehash|groq|librosa"
```

---

## Common Errors & Solutions

### ❌ "ModuleNotFoundError: No module named 'X'"
**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### ❌ "ffmpeg not found"
**Solution:**
```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### ❌ "Redis connection failed"
**Don't worry!** The system automatically uses `fakeredis` as fallback. Check logs:
```bash
grep -i redis backend/logs/error.log
```

### ❌ "Groq API error"
**Solution:** AI features are optional. Either:
1. Add API key to `.env`:
   ```bash
   GROQ_API_KEY=your_key_here
   ```
2. Or ignore - core detection works without it

### ❌ Port 8000 already in use
**Solution:**
```bash
# Find and kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### ❌ Frontend won't start
**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## Real-Time Error Monitoring

### Terminal 1 - Backend with logs:
```bash
cd backend
python api/main.py 2>&1 | tee logs/access.log
```

### Terminal 2 - Watch error log:
```bash
# Linux/macOS
tail -f backend/logs/error.log

# Windows PowerShell
Get-Content backend\logs\error.log -Wait
```

### Terminal 3 - Frontend:
```bash
cd frontend
npm run dev
```

---

## Error Log Format

Errors are logged with:
- **Timestamp**: When the error occurred
- **Level**: ERROR, WARNING, INFO
- **Module**: Which component failed
- **Message**: Error description
- **Stack Trace**: Full traceback for debugging

**Example:**
```
2026-03-28 03:17:45,123 - backend.api.main - ERROR - Error uploading protected content: ffmpeg not found
Traceback (most recent call last):
  File "api/main.py", line 675, in upload_protected
    result = process_protected_video(...)
  ...
```

---

## Health Check Endpoints

```bash
# System health
curl http://localhost:8000/health

# Metrics summary
curl http://localhost:8000/metrics/summary

# Recent detections
curl http://localhost:8000/detections?limit=10
```

---

## Debug Mode

The backend runs in **debug mode** by default, which means:
- ✅ Detailed error messages
- ✅ Auto-reload on code changes
- ✅ Stack traces in responses
- ⚠️ Don't use in production!

To disable debug mode:
```python
# In backend/api/main.py, change:
app.run(debug=False, port=8000)
```

---

## Getting Help

If errors persist:
1. Check `backend/logs/error.log` for stack traces
2. Verify all dependencies: `pip list`
3. Test with: `python backend/tests/test_sentinel.py`
4. Check browser console (F12) for frontend errors

**Log files location:**
- Backend errors: `backend/logs/error.log`
- Backend access: `backend/logs/access.log`
- Frontend: Browser console + terminal output
