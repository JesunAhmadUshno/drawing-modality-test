# 🚀 QUICK START GUIDE - Drawing Modality Test Environment

**Location:** `C:\Users\Jesun\Downloads\Project\Mentaiimage\Drawing_Modality_Test_1`  
**Date:** March 1, 2026  
**Status:** ✅ READY TO TEST

---

## ⚡ Start in 30 Seconds

### Step 1: Navigate to folder
```powershell
cd C:\Users\Jesun\Downloads\Project\Mentaiimage\Drawing_Modality_Test_1
```

### Step 2: Run launcher
```powershell
.\START_TEST_ENVIRONMENT.ps1
```

### Step 3: Done! 🎉
- Frontend opens automatically: http://localhost:8000
- Backend running: http://localhost:5000
- Start drawing!

---

## 📊 Complete Workflow Test

### 1. **Open Frontend**
- Browser will open automatically
- Or visit: http://localhost:8000

### 2. **Complete Drawing Tasks**
Choose from 7 tasks:
- ✏️ Two-Pentagon Copy
- 🏠 House Drawing Copy
- 🕐 Clock Drawing
- 📝 Word Writing (BIODEGRADABLE)
- ✍️ Cursive Sentence
- ➰ Loop Drawing (Right Hand)
- ➰ Loop Drawing (Left Hand)

### 3. **Export & Analyze**
- Click **"Export Session Data"** button
- ZIP file downloads automatically
- Backend analyzes in real-time
- **Results popup shows:**
  - Overall Score (0-100)
  - Grade (A, B+, C, etc.)
  - Efficiency & Quality scores
  - Total metrics extracted

### 4. **View Results**
Results displayed automatically in popup:
```
🎯 Analysis Complete!

Overall Score:    85/100
Grade:            B+
Efficiency:       42
Quality:          43

Total Metrics:    32
Valid Session:    ✅ Yes
```

---

## 🔍 Verify It's Working

### Check Backend Health
Visit: http://localhost:5000/api/health

Should see:
```json
{
  "status": "healthy",
  "service": "Drawing Modality Analysis",
  "version": "3.0",
  "features": {
    "dynamic": "enabled",
    "static": "enabled"
  }
}
```

### Check Console
In browser console (F12), you should see:
```
📊 Sending session to backend for analysis...
✅ Analysis complete: {status: 'success', ...}
```

---

## 🛠️ Troubleshooting

### "Port already in use"
```powershell
# Kill process on port 5000
Get-NetTCPConnection -LocalPort 5000 | ForEach-Object { taskkill /PID $_.OwningProcess /F }

# Kill process on port 8000
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { taskkill /PID $_.OwningProcess /F }
```

### "Backend not responding"
1. Check if backend window is still open
2. Look for errors in backend terminal
3. Restart with launcher script

### "Analysis failed"
Make sure:
- ✅ Backend is running (check http://localhost:5000/api/health)
- ✅ You've drawn at least one stroke
- ✅ Frontend is on http://localhost:8000 (not file://)

---

## 📁 What's Included

```
Drawing_Modality_Test_1/
├── backend_api.py              ⚙️  Backend server
├── integration_pipeline.py     🔧 Analysis engine
├── frontend/                   🌐 Drawing interface
│   ├── index.html
│   ├── taskManager.js          ← Modified to call API
│   ├── drawingCapture.js
│   └── taskConfig.js
├── features/                   📊 Feature extraction
│   ├── dynamic_features.py     (20+ metrics)
│   └── static_features.py      (12+ metrics)
├── tests/                      🧪 Test suite
└── START_TEST_ENVIRONMENT.ps1  🚀 One-click launcher
```

---

## ✅ Test Checklist

Complete this checklist to verify everything works:

- [ ] Launcher script runs without errors
- [ ] Backend starts on port 5000
- [ ] Frontend starts on port 8000
- [ ] Browser opens automatically
- [ ] Drawing interface loads correctly
- [ ] Can draw on canvas
- [ ] Can complete a task
- [ ] Export button works
- [ ] ZIP file downloads
- [ ] Backend receives request (check console)
- [ ] Analysis completes successfully
- [ ] Results popup appears
- [ ] Score is reasonable (0-100)
- [ ] Full results in browser console

---

## 🎯 Next Steps After Testing

1. **Validate Scores**: Check if scores make sense
2. **Test Edge Cases**: Empty drawings, single stroke, etc.
3. **Performance**: Test with multiple tasks
4. **Documentation**: Update final docs
5. **Prepare for Monday**: March 2 delivery!

---

## 📞 Getting Help

If something doesn't work:

1. **Check Backend Terminal**: Look for error messages
2. **Check Browser Console**: F12 → Console tab
3. **Verify Ports**: Make sure 5000 and 8000 are free
4. **Restart Environment**: Close all, run launcher again

---

## 🎉 Success Indicators

You'll know it's working when:

✅ Backend shows: `Starting server on http://localhost:5000`  
✅ Frontend shows drawing interface  
✅ Drawing creates visible strokes  
✅ Export downloads ZIP file  
✅ Backend console shows: `📊 Analyzing session: assessment-...`  
✅ Browser shows: `✅ Analysis complete`  
✅ Popup displays score and grade  

---

**Ready?** Run `.\START_TEST_ENVIRONMENT.ps1` and start testing! 🚀

---

*Last Updated: March 1, 2026*  
*Sprint 3 - Final Integration Test*
