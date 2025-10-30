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

Or use Docker:
docker-compose up --build



POST http://localhost:8002/api/buylist/upload
Not POST http://localhost:8002/api/health