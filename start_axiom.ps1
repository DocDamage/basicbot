Write-Host "Starting Axiom Math Chatbot System..." -ForegroundColor Cyan

# 1. Start Backend
Write-Host "Initializing Neural Backend (FastAPI)..." -ForegroundColor Green
Start-Process -FilePath "uvicorn" -ArgumentList "main:app --reload --port 8001" -WorkingDirectory "backend" -WindowStyle Minimized

# 2. Start Frontend
Write-Host "Launching Interface (Vite)..." -ForegroundColor Green
Set-Location frontend
npm run dev

# Note: The user can access it at localhost:5173
