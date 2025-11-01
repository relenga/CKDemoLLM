# CK LangGraph Server Management Script
# PowerShell script to stop all servers and clean up processes

Write-Host "=====================================" -ForegroundColor Yellow
Write-Host "   CK LangGraph Server Shutdown" -ForegroundColor Yellow  
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Gray
Write-Host ""

# Function to safely stop processes
function Stop-ProcessesByName {
    param([string]$ProcessName)
    
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "Stopping $($processes.Count) $ProcessName process(es)..." -ForegroundColor Cyan
        $processes | ForEach-Object {
            Write-Host "  - Stopping PID $($_.Id)" -ForegroundColor Gray
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
        
        # Check if any are still running
        $remaining = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
        if ($remaining) {
            Write-Host "  WARNING: $($remaining.Count) $ProcessName process(es) still running" -ForegroundColor Yellow
        } else {
            Write-Host "  SUCCESS: All $ProcessName processes stopped" -ForegroundColor Green
        }
    } else {
        Write-Host "No $ProcessName processes found" -ForegroundColor Gray
    }
}

# Stop Python processes (backend)
Stop-ProcessesByName "python"
Stop-ProcessesByName "python3.11"

# Stop Node.js processes (frontend)
Stop-ProcessesByName "node"

# Check port usage
Write-Host ""
Write-Host "Checking port usage..." -ForegroundColor Cyan

$port8002 = netstat -ano | Select-String ":8002.*LISTENING"
$port3001 = netstat -ano | Select-String ":3001.*LISTENING"

if ($port8002) {
    Write-Host "  WARNING: Port 8002 still in use:" -ForegroundColor Yellow
    Write-Host "    $port8002" -ForegroundColor Gray
} else {
    Write-Host "  Port 8002: FREE" -ForegroundColor Green
}

if ($port3001) {
    Write-Host "  WARNING: Port 3001 still in use:" -ForegroundColor Yellow
    Write-Host "    $port3001" -ForegroundColor Gray
} else {
    Write-Host "  Port 3001: FREE" -ForegroundColor Green
}

Write-Host ""
Write-Host "Shutdown complete!" -ForegroundColor Green
Write-Host "You can now safely restart the servers using:" -ForegroundColor White
Write-Host "  - backend\start-backend.bat" -ForegroundColor Cyan
Write-Host "  - frontend\start-frontend.bat" -ForegroundColor Cyan