#!/bin/bash
# FedEx DCA System - Quick Setup Script
# Run this to set up everything automatically

echo "=================================================="
echo "🚀 FedEx DCA System - Automated Setup"
echo "=================================================="
echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed!"
echo ""

# Step 2: Generate data
echo "📊 Step 2: Generating 1000 sample cases..."
python generate_data.py
echo "✅ Data generated!"
echo ""

# Step 3: Train models
echo "🧠 Step 3: Training ML models..."
python train_model.py
echo "✅ Models trained!"
echo ""

echo "=================================================="
echo "✨ Setup Complete!"
echo "=================================================="
echo ""
echo "🌐 To start the system:"
echo "   1. Run: python app.py"
echo "   2. Open browser: http://localhost:5000"
echo ""
echo "📚 For more info, see README.md"
echo "=================================================="
