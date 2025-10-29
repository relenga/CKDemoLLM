# Backend - Python + FastAPI + LangGraph

This is the backend API server built with FastAPI and LangGraph for AI-powered workflows.

## Features

- 🚀 FastAPI with automatic API documentation
- 🤖 LangGraph integration for AI workflows  
- 🔒 CORS configuration for frontend integration
- 📝 Pydantic models for data validation
- 🐍 Python 3.9+ with type hints
- 🧪 Testing with pytest
- 📊 Structured logging

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### Configuration

Edit the `.env` file with your settings:

```env
HOST=localhost
PORT=8000
DEBUG=true
OPENAI_API_KEY=your_openai_api_key_here
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Running the Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host localhost --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000).

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/api/openapi.json](http://localhost:8000/api/openapi.json)

## Project Structure

```
app/
├── api/                    # API endpoints
│   ├── endpoints.py       # Route handlers
│   └── routes.py          # Router configuration
├── core/                  # Core configuration
│   └── config.py         # Settings and configuration
├── models/                # Data models
│   └── schemas.py        # Pydantic models
├── services/              # Business logic
│   └── graph_service.py  # Graph processing service
└── graph/                 # LangGraph workflows
    └── processor.py      # Graph workflow definition
tests/                     # Test files
main.py                   # Application entry point
requirements.txt          # Python dependencies
```

## API Endpoints

### Health and Status
```
GET  /                    # Root endpoint
GET  /health             # Health check
GET  /api/status         # API status and version info
```

### Graph Processing
```
POST /api/graph/process  # Process input through LangGraph
GET  /api/graph/info     # Get graph structure information
```

## LangGraph Integration

The application uses LangGraph for AI workflow orchestration:

### Graph Structure
1. **Input Processing**: Validates and prepares input
2. **AI Processing**: Processes through language model (if configured)
3. **Output Formatting**: Formats and structures the response

### Workflow Features
- State management between nodes
- Error handling and recovery
- Metadata tracking
- Processing time measurement

## Configuration Options

### LangGraph Settings
```python
LANGGRAPH_CONFIG = {
    "max_iterations": 10,
    "temperature": 0.7,
    "max_tokens": 1000
}
```

### CORS Configuration
```python
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_graph.py
```

### Code Quality
```bash
# Format code with black
black app/

# Sort imports
isort app/

# Type checking with mypy
mypy app/
```

### Adding New Endpoints

1. Define Pydantic models in `app/models/schemas.py`
2. Add business logic to appropriate service in `app/services/`
3. Create endpoint handlers in `app/api/endpoints.py`
4. Register routes in `app/api/routes.py`

### Extending LangGraph Workflows

1. Modify `app/graph/processor.py`
2. Add new nodes and edges as needed
3. Update the graph service to handle new functionality
4. Add corresponding API endpoints

## Deployment

### Docker
```bash
# Build image
docker build -t ck-langgraph-backend .

# Run container
docker run -p 8000:8000 ck-langgraph-backend
```

### Production Settings
```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
BACKEND_CORS_ORIGINS=["https://your-frontend-domain.com"]
```

## Monitoring and Logging

The application includes structured logging:
- Request/response logging
- Error tracking
- Performance monitoring
- Graph execution tracing

## Security Considerations

- Environment-based configuration
- CORS origin validation
- Input validation with Pydantic
- Security headers middleware ready

## Troubleshooting

### Common Issues

1. **Module Import Errors**: Ensure virtual environment is activated
2. **Port Already in Use**: Change PORT in .env or kill existing process
3. **OpenAI API Errors**: Verify OPENAI_API_KEY is set correctly
4. **CORS Issues**: Check BACKEND_CORS_ORIGINS includes frontend URL