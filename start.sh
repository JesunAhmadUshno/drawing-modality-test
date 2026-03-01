#!/bin/bash
# Quick start script for Codespaces

echo "🚀 Starting Drawing Modality Analysis Environment..."
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt -q

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting Flask backend on port 5000..."
echo "   Access the app when the port forwards automatically"
echo ""

python backend_api.py
