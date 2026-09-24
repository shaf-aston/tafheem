#!/bin/bash
# Tafheem: Cross-platform startup script (macOS/Linux)
# Run: bash "/c/Users/Shaf/Downloads/aRABIC GRAMMAR TOOL/arabic-grammar-tool/start.sh"
set -e

# Change to script directory so relative paths work
cd "$(dirname "$0")"

echo "🚀 Starting Tafheem..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create a .env file with your GROQ_API_KEY"
    echo ""
    echo "Quick setup:"
    echo "  1. Copy .env.example to .env"
    echo "  2. Get your free API key from https://console.groq.com/keys"
    echo "  3. Edit .env and paste your key"
    echo ""
    exit 1
fi
echo "✓ Configuration file found"
echo ""

# Set up Python virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Setting up Python environment..."
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv venv
    else
        python -m venv venv
    fi
fi

# Activate virtual environment (Git Bash on Windows uses Scripts/)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "❌ Could not find venv activation script"
    exit 1
fi

REQ_HASH=$(sha256sum requirements.txt 2>/dev/null || shasum -a 256 requirements.txt)
HASH_FILE="venv/.requirements.hash"
if [ ! -f "$HASH_FILE" ] || [ "$(cat "$HASH_FILE")" != "$REQ_HASH" ]; then
    echo "Installing/updating Python dependencies..."
    pip install -q -r requirements.txt
    echo "$REQ_HASH" > "$HASH_FILE"
else
    echo "✓ Python dependencies up to date (skipped install)"
fi
echo "✓ Python environment ready"
echo ""

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install --silent && cd ..
fi
echo "✓ Frontend dependencies ready"
echo ""

echo "Starting backend  → http://localhost:8000"
echo "Starting frontend → http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start backend in background (run from project root so backend.* imports resolve)
python -m uvicorn backend.main:app --reload --reload-dir backend --port 8000 &
BACKEND_PID=$!

# Ensure backend is killed on exit (Ctrl+C, error, or frontend exit)
trap "kill $BACKEND_PID 2>/dev/null" INT TERM EXIT

# Start frontend in foreground
cd frontend && npm run dev