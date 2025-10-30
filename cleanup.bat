@echo off
REM Cleanup script for CK LangGraph project (Windows)

echo 🧹 Starting project cleanup...

REM Backend cleanup
echo Cleaning backend files...
cd backend

REM Remove temporary/debug files
if exist debug_app.py del debug_app.py
if exist simple_test.py del simple_test.py
if exist test_post.py del test_post.py
if exist run_test.bat del run_test.bat

REM Remove Python cache
if exist __pycache__ rmdir /s /q __pycache__
if exist app\__pycache__ rmdir /s /q app\__pycache__

REM Replace main.py with cleaned version
if exist main.py if exist main_clean.py (
    move main.py main_backup.py
    move main_clean.py main.py
    echo ✅ Replaced main.py with cleaned version
)

echo ✅ Backend cleanup complete

REM Frontend cleanup
echo Cleaning frontend files...
cd ..\frontend

REM Remove any temp files
if exist *.tmp del *.tmp
if exist *.log del *.log

echo ✅ Frontend cleanup complete

cd ..
echo 🎉 Project cleanup finished!
echo.
echo 📁 Project structure is now clean and organized
echo 🚀 You can run the servers with:
echo    Backend: cd backend ^&^& python main.py
echo    Frontend: cd frontend ^&^& npm start

pause