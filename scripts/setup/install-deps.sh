#!/bin/bash

# ATLAS Dependencies Installation Script

set -e

echo "🚀 Installing ATLAS dependencies..."

# Check if we're in the correct directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this script from the ATLAS root directory"
    exit 1
fi

# Install root dependencies
echo "📦 Installing root dependencies..."
npm install

# Install frontend dependencies
echo "🎨 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Install backend dependencies
echo "🔧 Installing backend dependencies..."
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Install MLflow dependencies
echo "📊 Installing MLflow dependencies..."
cd mlflow
pip install -r requirements.txt
cd ..

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual API keys"
fi

echo "✅ All dependencies installed successfully!"
echo ""
echo "Next steps:"
echo "1. Update .env with your API keys"
echo "2. Run 'npm run docker:up' to start services"
echo "3. Run 'npm run dev' to start development servers"