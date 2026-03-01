# Deployment Guide

This project supports multiple deployment options for different use cases.

---

## 🌐 GitHub Pages (Frontend Only)

**Best for:** Public demos, portfolio showcases

### Setup:
1. Push code to GitHub
2. Go to **Settings → Pages**
3. Source: **GitHub Actions**
4. The workflow will auto-deploy on push

**URL:** `https://[username].github.io/[repo-name]/`

### Note:
- ⚠️ **Backend features won't work** on GitHub Pages (Python can't run)
- Frontend will load but analysis requires backend
- See "Client-Side JS Option" below for standalone version

---

## 💻 GitHub Codespaces (Full App)

**Best for:** Development, testing, team collaboration

### Setup:
1. Push code to GitHub
2. Click **Code → Codespaces → Create codespace**
3. Wait for container to build (auto-installs dependencies)
4. Run: `python backend_api.py` or `./start.sh`
5. Port 5000 auto-forwards → Click "Open in Browser"

**Features:**
- ✅ Full Python backend with all features
- ✅ Real-time analysis
- ✅ OpenCV, NumPy, all dependencies
- ✅ Development environment in browser
- ⏰ Auto-hibernates after 30 min idle

**Limits:**
- Free tier: 120 core-hours/month for personal repos
- Not for permanent hosting (development only)

---

## 🔧 Other Hosting Options

### Option 1: Split Deployment
- **Frontend:** GitHub Pages
- **Backend:** Railway, Render, Heroku, PythonAnywhere
- Update frontend API endpoint to backend URL

### Option 2: Full Stack Platforms
- **Vercel/Netlify:** (Frontend + serverless functions)
- **Railway/Render:** (Frontend + backend containers)
- **AWS/GCP/Azure:** (Full cloud deployment)

### Option 3: Client-Side Only (No Backend)
Convert Python analysis to JavaScript:
- Reimplement features using OpenCV.js + math.js
- Run 100% in browser
- Deploy to GitHub Pages as static site

---

## 📦 Quick Commands

### Local Development:
```bash
# Windows
.venv\Scripts\activate
python backend_api.py

# Mac/Linux
source .venv/bin/activate
python backend_api.py
```

### Codespaces:
```bash
./start.sh
# or
python backend_api.py
```

### GitHub Pages:
- Automatic via GitHub Actions on push

---

## 🎯 Recommended Setup

**For Development:**
→ Use **GitHub Codespaces**

**For Public Demo:**
→ Use **GitHub Pages** (frontend) + **Railway/Render** (backend)

**For Research/Testing:**
→ Use **Local** or **Codespaces**

---

## 📝 Additional Configuration

### Update API Endpoint (if using split deployment):

In `frontend/drawingCapture.js` and `frontend/taskManager.js`, find:
```javascript
const API_URL = 'http://localhost:5000';
```

Change to your backend URL:
```javascript
const API_URL = 'https://your-backend-url.railway.app';
```

---

## 🆘 Troubleshooting

**Codespaces won't start:**
- Delete and recreate codespace
- Check `.devcontainer/devcontainer.json` syntax

**GitHub Pages showing 404:**
- Ensure Actions are enabled
- Check Settings → Pages → Source = "GitHub Actions"
- Wait 2-3 minutes after push

**Backend not connecting:**
- Check port forwarding in Codespaces
- Verify CORS settings in `backend_api.py`
- Check firewall/network settings
