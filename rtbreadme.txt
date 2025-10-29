Backend startup

cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py

fontend startup:
cd frontend
npm install
npm start

Or use Docker:
docker-compose up --build