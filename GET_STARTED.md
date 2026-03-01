# Quick Start Guide - PulseKey Assessment System v3.1

## 🚀 Getting Started (2 Minutes)

### Step 1: Start the Backend Server
```powershell
cd C:\Users\Jesun\Downloads\Project\Mentaiimage\Drawing_Modality_Test_1
python backend_api.py
```

### Step 2: Start the Frontend Server
```powershell
cd C:\Users\Jesun\Downloads\Project\Mentaiimage\Drawing_Modality_Test_1\frontend
python -m http.server 8000
```

### Step 3: Open in Browser
Navigate to: **http://localhost:8000**

## 📋 Using the System

### Complete a New Assessment
1. Click **"Start New Task"** button
2. Complete the drawing tasks
3. Click **"Submit"** when done
4. See the 🎉 **Congratulations popup**
5. Auto-redirect back to landing page

### View Your Saved Sessions
1. Click **"View Reports"** button
2. Browse all completed sessions
3. Click **"View"** to see detailed report
4. Click **"Download"** to get JSON file

## 🗂️ Where Are Files Saved?

All files go to the **Records** folder:
```
Records/
├── session-TIMESTAMP/
│   ├── JSON/
│   │   └── session.json      (Raw data)
│   ├── PNG/
│   │   └── task-*.png        (Canvas screenshots)
│   └── _report.json          (Analysis)
```

## ✅ System Features

- ✅ Landing page with two main actions
- ✅ Complete task drawing interface
- ✅ Submit button with congratulations popup
- ✅ Reports page to view all sessions
- ✅ Automatic analysis on submission
- ✅ Organized file storage
- ✅ Search functionality on reports
- ✅ Download session reports as JSON
- ✅ Responsive mobile design

---

**Ready to start?** → Open http://localhost:8000
