# CK LangGraph Application

A full-stack application combining a React + Material-UI frontend with a Python + LangGraph backend for AI-powered graph processing workflows.

## Project Structure

```
├── frontend/                 # React + TypeScript + Material-UI
│   ├── public/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   ├── hooks/           # Custom React hooks
│   │   ├── types/           # TypeScript type definitions
│   │   └── utils/           # Utility functions
│   ├── package.json
│   └── tsconfig.json
├── backend/                  # Python + FastAPI + LangGraph
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Core configuration
│   │   ├── models/          # Pydantic models
│   │   ├── services/        # Business logic
│   │   └── graph/           # LangGraph workflows
│   ├── tests/               # Test files
│   ├── requirements.txt
│   └── main.py
├── shared/                   # Shared configurations
└── docker-compose.yml        # Docker orchestration
```

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Material-UI (MUI)** for components and theming
- **React Router** for navigation
- **Axios** for API communication
- **Vite** for fast development builds

### Backend
- **FastAPI** for REST API
- **LangGraph** for AI workflow orchestration
- **LangChain** for AI integrations
- **Pydantic** for data validation
- **Uvicorn** as ASGI server

## Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.9+
- Git

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd 2025-10-29\ CKLangGraph

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables in .env
# Add your OpenAI API key if using AI features
OPENAI_API_KEY=your_openai_api_key_here

# Run the backend
python main.py
```

The backend will be available at: http://localhost:8000

### 3. Frontend Setup

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will be available at: http://localhost:3000

## Development

### Backend Development

```bash
# Run with auto-reload
uvicorn main:app --reload --host localhost --port 8000

# Run tests
pytest

# Check API documentation
# Visit http://localhost:8000/docs for Swagger UI
# Visit http://localhost:8000/redoc for ReDoc
```

### Frontend Development

```bash
# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Type checking
npx tsc --noEmit
```

### Using Docker

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop services
docker-compose down
```

## API Endpoints

### Core Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/status` - API status and version

### Graph Processing
- `POST /api/graph/process` - Process input through LangGraph
- `GET /api/graph/info` - Get graph structure information

## Configuration

### Backend Environment Variables
```env
HOST=localhost
PORT=8000
DEBUG=true
OPENAI_API_KEY=your_key_here
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend Environment Variables
```env
REACT_APP_API_URL=http://localhost:8000
```

## Features

### Current Features
- ✅ React + Material-UI responsive frontend
- ✅ FastAPI backend with automatic API documentation
- ✅ LangGraph integration for AI workflows
- ✅ CORS configuration for local development
- ✅ TypeScript support throughout
- ✅ Docker containerization ready
- ✅ Environment-based configuration

### Planned Features
- 🔄 User authentication and authorization
- 🔄 Real-time graph processing updates
- 🔄 Graph visualization components
- 🔄 File upload and processing
- 🔄 Multiple AI model support
- 🔄 Workflow templates and presets

## Architecture

The application follows a clean architecture pattern:

1. **Frontend**: React SPA that communicates with the backend via REST API
2. **Backend**: FastAPI server that orchestrates LangGraph workflows
3. **Graph Processing**: LangGraph handles complex AI workflows and state management
4. **API Layer**: RESTful endpoints with automatic documentation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team.