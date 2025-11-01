# CK LangGraph Development Server Management

This folder contains utility scripts to manage the development servers reliably.

## Quick Start Scripts

### Starting Servers
- **Backend**: Double-click `backend/start-backend.bat`
  - Starts FastAPI server on http://localhost:8002
  - Includes Part Matching Engine endpoints
  - Automatically checks for required files and virtual environment

- **Frontend**: Double-click `frontend/start-frontend.bat` 
  - Starts React development server on http://localhost:3001
  - Automatically runs `npm install` if needed
  - Proxies API calls to backend

### Stopping Servers
- **All Servers**: Right-click `shutdown-all.ps1` → "Run with PowerShell"
  - Safely stops all Python and Node.js processes
  - Checks port availability
  - Shows cleanup status

## Troubleshooting

### If Servers Won't Start
1. Run `shutdown-all.ps1` first to clean up any stuck processes
2. If that doesn't work, restart your computer (known Windows port binding issue)
3. Then use the start scripts

### Port Issues
- Backend uses port 8002
- Frontend uses port 3001  
- The shutdown script will show which ports are still in use

### Directory Issues
- The scripts automatically navigate to their correct directories
- No need to manually `cd` to backend or frontend folders

## Manual Commands (if needed)

### Backend (from project root):
```bash
cd backend
./venv/Scripts/python.exe main.py
```

### Frontend (from project root):
```bash
cd frontend
npm start
```

## New Part Matching Engine Endpoints

After restart, the backend will include these new endpoints:
- `POST /api/matcher/find_matches` - Run part matching between SellList and BuyList
- `GET /api/matcher/status` - Check if data is loaded and ready for matching  
- `POST /api/matcher/preview` - Preview composite matching fields

Test at: http://localhost:8002/docs (FastAPI interactive docs)