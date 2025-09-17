#!/bin/bash
# Quick start script for Web Application Honeypot
# This script sets up and runs the honeypot with proper warnings

echo "=================================================================="
echo "🍯 WEB APPLICATION HONEYPOT - QUICK START"
echo "=================================================================="
echo ""
echo "⚠️  SECURITY WARNING:"
echo "   This honeypot is for LAB/EDUCATIONAL USE ONLY!"
echo "   Do not expose to public internet without proper isolation."
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.7+ and try again."
    exit 1
fi

# Check Python version
python_version=$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
required_version="3.7"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "❌ Python $required_version or higher required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create data directory if it doesn't exist
if [[ ! -d "honeypot/data" ]]; then
    echo "📁 Creating data directory..."
    mkdir -p honeypot/data
fi

echo ""
echo "🚀 Starting honeypot..."
echo "   - Access at: http://127.0.0.1:8080/login"
echo "   - Logs will be written to: honeypot/data/web_honeypot.jsonl"
echo "   - Press Ctrl+C to stop"
echo ""
echo "=================================================================="

# Start the honeypot
python -m honeypot.webapp