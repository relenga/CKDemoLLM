Copilot start and stop guide:
# Backend
Start-Process -FilePath "cmd" -ArgumentList "/k", "cd /d C:\Users\AiDev\Documents\CKCode\2025-10-29 CKLangGraph\backend && .\venv\Scripts\python.exe main.py"

# Frontend  
Start-Process -FilePath "cmd" -ArgumentList "/k", "cd /d C:\Users\AiDev\Documents\CKCode\2025-10-29 CKLangGraph\frontend && npm start"






Backend startup
    cd backend
    python -m venv venv
    venv\Scripts\activate  # Windows
    pip install -r requirements.txt
    python main.py

Backened start if venv is running.
    cd backend
    venv\Scripts\activate
    python main.py

fontend startup:
    cd frontend
    npm install
    npm start

Always check netstat -an | findstr :8002 before starting, or use taskkill more aggressively to ensure clean starts!

Or use Docker:
docker-compose up --build



POST http://localhost:8002/api/buylist/upload
Not POST http://localhost:8002/api/health