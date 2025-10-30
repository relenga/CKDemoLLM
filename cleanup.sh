#!/bin/bash
# Cleanup script for CK LangGraph project

echo "🧹 Starting project cleanup..."

# Backend cleanup
echo "Cleaning backend files..."
cd backend

# Remove temporary/debug files
rm -f debug_app.py simple_test.py test_post.py run_test.bat 2>/dev/null || true

# Remove Python cache
rm -rf __pycache__ app/__pycache__ 2>/dev/null || true

# Remove old main.py (keeping as backup)
if [ -f "main.py" ] && [ -f "main_clean.py" ]; then
    mv main.py main_backup.py
    mv main_clean.py main.py
    echo "✅ Replaced main.py with cleaned version"
fi

echo "✅ Backend cleanup complete"

# Frontend cleanup
echo "Cleaning frontend files..."
cd ../frontend

# Remove any temp files
rm -f *.tmp *.log 2>/dev/null || true

echo "✅ Frontend cleanup complete"

echo "🎉 Project cleanup finished!"
echo ""
echo "📁 Project structure is now clean and organized"
echo "🚀 You can run the servers with:"
echo "   Backend: cd backend && python main.py"
echo "   Frontend: cd frontend && npm start"