# Quick Commerce Deals - Setup and Run
Write-Host "Quick Commerce Deals - Setup and Run" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "`nInitializing database with sample data..." -ForegroundColor Yellow
python database/init_db.py

Write-Host "`nStarting FastAPI backend server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "`nWaiting for API server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`nStarting data simulation..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python data/simulate_data.py"

Write-Host "`nStarting Streamlit web interface..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "streamlit run web/app.py --server.port 8501"

Write-Host "`n=====================================" -ForegroundColor Green
Write-Host "All services started successfully!" -ForegroundColor Green
Write-Host "`nAccess points:" -ForegroundColor White
Write-Host "- Web Interface: http://localhost:8501" -ForegroundColor Cyan
Write-Host "- API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "- API Health: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
