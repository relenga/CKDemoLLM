@echo off
cd /d "C:\Users\AiDev\Documents\CKCode\2025-10-29 CKLangGraph\backend"
echo Starting server...
start /b .\venv\Scripts\python.exe working_main.py
timeout /t 5
echo Testing POST endpoint...
.\venv\Scripts\python.exe test_post.py
pause