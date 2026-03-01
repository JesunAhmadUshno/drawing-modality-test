# Drawing Modality Complete Test Environment Launcher
# =======================================================
# This script starts both the backend API and frontend servers
# for a complete isolated testing environment.

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Drawing Modality Test Environment Launcher               ║" -ForegroundColor Cyan
Write-Host "║  Sprint 3 - Complete Integration Test                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
$expectedPath = "Drawing_Modality_Test_1"
if (-not (Get-Location).Path.Contains($expectedPath)) {
    Write-Host "⚠️  Warning: Not in Drawing_Modality_Test_1 directory" -ForegroundColor Yellow
    Write-Host "   Current: $(Get-Location)" -ForegroundColor Yellow
    Write-Host ""
    $confirm = Read-Host "Continue anyway? (y/n)"
    if ($confirm -ne 'y') {
        Write-Host "❌ Cancelled" -ForegroundColor Red
        exit
    }
}

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "   Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Check if Flask is installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow
$flaskInstalled = python -c "import flask; print('ok')" 2>$null
if ($flaskInstalled -ne 'ok') {
    Write-Host "⚠️  Flask not installed. Installing dependencies..." -ForegroundColor Yellow
    pip install flask flask-cors numpy pandas opencv-python opencv-contrib-python scikit-image
}

Write-Host ""
Write-Host "✅ Environment ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Starting servers..." -ForegroundColor Cyan
Write-Host ""

# Start backend API in background
Write-Host "🚀 Starting Backend API (port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python backend_api.py" -WindowStyle Normal

Start-Sleep -Seconds 3

# Start frontend server in background  
Write-Host "🌐 Starting Frontend Server (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; python -m http.server 8000" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  🎉 Test Environment Running!                              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access Points:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:8000" -ForegroundColor White
Write-Host "   Backend API: http://localhost:5000" -ForegroundColor White
Write-Host "   API Health: http://localhost:5000/api/health" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Usage:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:8000 in your browser" -ForegroundColor White
Write-Host "   2. Complete drawing tasks" -ForegroundColor White
Write-Host "   3. Click 'Complete Assessment' or 'Export Session Data'" -ForegroundColor White
Write-Host "   4. Backend will automatically analyze and return results" -ForegroundColor White
Write-Host ""
Write-Host "📊 Features:" -ForegroundColor Cyan
Write-Host "   ✅ Dynamic Features (20+ temporal metrics)" -ForegroundColor Green
Write-Host "   ✅ Static Features (12+ geometric metrics)" -ForegroundColor Green
Write-Host "   ✅ Combined Scoring & Grading" -ForegroundColor Green
Write-Host "   ✅ Real-time Analysis" -ForegroundColor Green
Write-Host ""
Write-Host "🛑 To Stop:" -ForegroundColor Yellow
Write-Host "   Close the two PowerShell windows that opened" -ForegroundColor White
Write-Host "   Or press Ctrl+C in each window" -ForegroundColor White
Write-Host ""
Write-Host "📂 Working Directory: $PWD" -ForegroundColor Gray
Write-Host ""

# Wait for user to press Enter
Write-Host "Press Enter to open frontend in browser..." -ForegroundColor Cyan
Read-Host

# Open frontend in default browser
Start-Process "http://localhost:8000"

Write-Host ""
Write-Host "✅ Frontend opened in browser!" -ForegroundColor Green
Write-Host "   You can now start testing the drawing modality." -ForegroundColor White
Write-Host ""
