# 🚀 Setup & Installation Guide

Complete guide for setting up the PulseKey Drawing Modality Analysis System across different environments.

---

## 📋 Table of Contents

1. [Quick Start (Recommended)](#-quick-start-recommended)
2. [GitHub Codespaces Setup](#-github-codespaces-setup-full-app)
3. [GitHub Pages Setup](#-github-pages-setup-frontend-only)
4. [Local Development Setup](#-local-development-setup)
5. [Troubleshooting](#-troubleshooting)
6. [Verification](#-verification)

---

## ⚡ Quick Start (Recommended)

### Option 1: GitHub Codespaces (Full Application)
**Best for:** Testing the complete system with all features

1. **Click this link:** [Launch Codespace](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=JesunAhmadUshno/drawing-modality-test)
2. **Wait** ~2-3 minutes for automatic setup
3. **Run:** `python backend_api.py`
4. **Access:** Click the forwarded port notification/URL
5. **Done!** Full app is running

### Option 2: GitHub Pages (Frontend Demo)
**Best for:** Quick demo of the UI (no analysis features)

**Live at:** https://jesunahmadushno.github.io/drawing-modality-test/

No setup needed - just visit the link!

---

## 💻 GitHub Codespaces Setup (Full App)

GitHub Codespaces provides a complete cloud development environment with everything pre-configured.

### Step 1: Create Codespace

**Method A - Direct Link:**
```
https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=JesunAhmadUshno/drawing-modality-test
```
Click "Create codespace"

**Method B - Via Repository:**
1. Go to https://github.com/JesunAhmadUshno/drawing-modality-test
2. Click green **"Code"** button
3. Select **"Codespaces"** tab
4. Click **"Create codespace on main"**

### Step 2: Wait for Setup

The `.devcontainer/devcontainer.json` configuration will automatically:
- ✅ Install Python 3.11
- ✅ Install Node.js 18
- ✅ Run `pip install -r requirements.txt`
- ✅ Configure VS Code extensions
- ✅ Set up port forwarding for port 5000

**Time:** ~2-3 minutes (first time), ~30 seconds (subsequent starts)

### Step 3: Start the Backend

Once the Codespace loads, in the terminal run:

```bash
python backend_api.py
```

Or use the quick start script:
```bash
chmod +x start.sh
./start.sh
```

### Step 4: Access the Application

1. A notification will appear: **"Your application is available on port 5000"**
2. Click **"Open in Browser"**
3. Or click the **Ports** tab → Right-click port 5000 → **"Open in Browser"**

### Step 5: Use the App

Navigate to:
- **Home:** `/` or `/frontend/index.html`
- **Drawing Task:** `/frontend/task.html`
- **Analytics:** `/frontend/analytics-dashboard.html`
- **Reports:** `/frontend/reports.html`
- **API Health:** `/api/health`

### Managing Codespaces

**View all Codespaces:**
https://github.com/codespaces

**Stop Codespace:**
- Click the Codespace name → "Stop codespace"
- Auto-stops after 30 minutes of inactivity

**Delete Codespace:**
- Click "..." menu → "Delete"

**Free Tier:**
- 120 core-hours/month for personal repos
- 15 GB storage

---

## 🌐 GitHub Pages Setup (Frontend Only)

GitHub Pages automatically deploys the frontend on every push.

### Step 1: Enable GitHub Pages

1. Go to repository **Settings** → **Pages**
2. Under **"Source"**, select: **GitHub Actions**
3. Click **"Save"**

### Step 2: Verify Deployment

1. Go to **Actions** tab: https://github.com/JesunAhmadUshno/drawing-modality-test/actions
2. Check workflow: **"Deploy Frontend to GitHub Pages"**
3. Wait for ✅ green checkmark (~2 minutes)

### Step 3: Access the Site

**URL:** https://jesunahmadushno.github.io/drawing-modality-test/

### Limitations

⚠️ **GitHub Pages runs ONLY frontend files:**
- ✅ UI and drawing interface work
- ❌ Analysis features don't work (Python backend not available)
- ❌ Session submission fails (no API)
- ❌ Data processing unavailable

**For full functionality**, use GitHub Codespaces or local development.

---

## 🏠 Local Development Setup

Run the complete system on your local machine.

### Prerequisites

- **Python:** 3.9 or higher (recommended: 3.11+)
- **Git:** Latest version
- **pip:** Python package manager
- **Browser:** Chrome 90+, Firefox 88+, or Safari 14+

### Step 1: Clone Repository

```bash
git clone https://github.com/JesunAhmadUshno/drawing-modality-test.git
cd drawing-modality-test
```

### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected packages:**
- Flask, Flask-CORS (web server)
- NumPy, Pandas, SciPy (numerical computing)
- OpenCV, scikit-image (computer vision)
- Matplotlib, Seaborn (visualization)
- pytest (testing)

**Time:** ~2-5 minutes depending on internet speed

### Step 4: Verify Installation

```bash
python -c "import cv2, numpy, pandas, flask; print('✅ All dependencies installed')"
```

### Step 5: Start Backend Server

```bash
python backend_api.py
```

**Expected output:**
```
✅ Drawing Modality Analysis System
📊 Version: 3.0
🌐 Server running on: http://localhost:5000
🔥 Press CTRL+C to quit
```

### Step 6: Access Frontend

Open your browser to:
- **Main Interface:** http://localhost:5000/frontend/index.html
- **Drawing Task:** http://localhost:5000/frontend/task.html
- **Analytics:** http://localhost:5000/frontend/analytics-dashboard.html
- **API Health Check:** http://localhost:5000/api/health

### Optional: Run Tests

```bash
# Integration tests
python tests/integration_tests.py

# Test submission
python test_submit.py

# Demo
python demo.py
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. **"Module not found" error**
```bash
# Ensure virtual environment is activated
# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. **"Port 5000 already in use"**
```bash
# Windows - Find and kill process
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9

# Or use different port in backend_api.py
```

#### 3. **OpenCV import fails**
```bash
# Uninstall and reinstall
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python opencv-contrib-python
```

#### 4. **CORS errors in browser**
- Check Flask-CORS is installed: `pip install flask-cors`
- Verify CORS is enabled in `backend_api.py`
- Clear browser cache and reload

#### 5. **GitHub Pages 404 error**
- Ensure GitHub Actions is selected as source (not branch)
- Check Actions tab for deployment status
- Wait 2-3 minutes after enabling Pages
- Verify workflow file: `.github/workflows/pages.yml`

#### 6. **Codespace won't create**
- Check GitHub Codespaces quota (Settings → Billing)
- Try creating from repository Code button
- Delete old Codespaces to free up resources
- Verify `.devcontainer/devcontainer.json` syntax

#### 7. **Analysis returns empty results**
- Check browser console for errors (F12)
- Verify backend is running (`/api/health`)
- Check Records/ folder permissions
- Review backend_api.py logs in terminal

---

## ✅ Verification

### Backend Health Check

**Terminal:**
```bash
curl http://localhost:5000/api/health
```

**Browser:**
```
http://localhost:5000/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "Drawing Modality Analysis - Isolated Test",
  "version": "3.0",
  "features": {
    "dynamic": "enabled",
    "static": "enabled",
    "combined_scoring": "enabled"
  }
}
```

### Frontend Verification

1. Open: http://localhost:5000/frontend/task.html
2. Click "Start Session"
3. Draw on canvas
4. Click "Submit Drawing"
5. Check for success message and results

### Full System Test

```bash
# Run complete integration test
python tests/integration_tests.py

# Expected: All tests pass with ✅
```

---

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 7+ / macOS 10.12+ / Ubuntu 18.04+ | Windows 10+ / macOS 12+ / Ubuntu 22.04+ |
| **Python** | 3.9 | 3.11+ |
| **RAM** | 2 GB | 4 GB+ |
| **Disk Space** | 500 MB | 2 GB |
| **Browser** | Chrome 80+ | Chrome 100+, Firefox 90+ |
| **Network** | 5 Mbps | 25 Mbps |

---

## 🎯 Environment Comparison

| Feature | Local | Codespaces | GitHub Pages |
|---------|-------|------------|--------------|
| **Full Backend** | ✅ | ✅ | ❌ |
| **Frontend** | ✅ | ✅ | ✅ |
| **Analysis** | ✅ | ✅ | ❌ |
| **Setup Time** | 10 min | 3 min | 0 min |
| **Cost** | Free | Free tier* | Free |
| **Persistence** | ✅ | Session-based | ✅ |
| **Collaboration** | ❌ | ✅ | ✅ |
| **Internet Required** | No** | Yes | Yes |

\* 120 core-hours/month  
\** After initial setup

---

## 🆘 Getting Help

1. **Check documentation:** [README.md](README.md), [COMPREHENSIVE_WORKLOG.md](COMPREHENSIVE_WORKLOG.md)
2. **Review logs:** Check terminal output for error messages
3. **Test setup:** Run `python tests/integration_tests.py`
4. **Verify dependencies:** `pip list | grep -E "(flask|numpy|opencv|pandas)"`
5. **Check API:** Visit http://localhost:5000/api/health

---

## 🔗 Quick Links

- **Repository:** https://github.com/JesunAhmadUshno/drawing-modality-test
- **Live Demo:** https://jesunahmadushno.github.io/drawing-modality-test/
- **Create Codespace:** [Launch here](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=JesunAhmadUshno/drawing-modality-test)
- **Issues:** https://github.com/JesunAhmadUshno/drawing-modality-test/issues
- **Deployments:** https://github.com/JesunAhmadUshno/drawing-modality-test/deployments

---

**Last Updated:** March 1, 2026  
**Version:** 3.0  
**Maintainer:** Jesun Ahmad Ushno
