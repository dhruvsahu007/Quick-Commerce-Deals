@echo off
echo Quick Commerce Deals - Setup and Run
echo =====================================

echo.
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Initializing database with sample data...
python database/init_db.py

echo.
echo Starting FastAPI backend server...
start "API Server" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo Waiting for API server to start...
timeout /t 5

echo.
echo Starting data simulation...
start "Data Simulation" cmd /k "python data/simulate_data.py"

echo.
echo Starting Streamlit web interface...
start "Web Interface" cmd /k "streamlit run web/app.py --server.port 8501"

echo.
echo =====================================
echo All services started successfully!
echo.
echo Access points:
echo - Web Interface: http://localhost:8501
echo - API Documentation: http://localhost:8000/docs
echo - API Health: http://localhost:8000/health
echo.
echo Press any key to exit...
pause
