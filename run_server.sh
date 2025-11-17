# Load dotenv manually for the shell environment
export $(grep -v '^#' .env | xargs)

echo "Starting FastAPI server on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Wait a moment to let uvicorn boot
sleep 2

echo "Starting ngrok tunnel..."
ngrok config add-authtoken $NGRROK_API_KEY >/dev/null 2>&1
ngrok http 8000
