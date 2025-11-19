# Desktop App - Port Cleanup and Restart Script
# This script kills processes using ports 5173-5180 and restarts the desktop app

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Desktop App - Port Cleanup & Restart" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Kill processes on ports 5173-5180
Write-Host "Step 1: Cleaning up ports 5173-5180..." -ForegroundColor Yellow

$portsToClean = 5173..5180

foreach ($port in $portsToClean) {
    try {
        $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($connection) {
            $processId = $connection.OwningProcess
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue

            if ($process) {
                Write-Host "  Killing process $($process.ProcessName) (PID: $processId) on port $port" -ForegroundColor Red
                Stop-Process -Id $processId -Force
            }
        }
    } catch {
        # Port not in use, continue
    }
}

Write-Host "  Ports cleaned" -ForegroundColor Green
Write-Host ""

# Step 2: Kill any remaining Node/Electron processes
Write-Host "Step 2: Cleaning up Node/Electron processes..." -ForegroundColor Yellow

$processNames = @("node", "electron", "vite")
foreach ($name in $processNames) {
    $processes = Get-Process -Name $name -ErrorAction SilentlyContinue
    if ($processes) {
        foreach ($proc in $processes) {
            Write-Host "  Killing $name process (PID: $($proc.Id))" -ForegroundColor Red
            Stop-Process -Id $proc.Id -Force
        }
    }
}

Write-Host "  Processes cleaned" -ForegroundColor Green
Write-Host ""

# Step 3: Wait a moment for ports to be released
Write-Host "Step 3: Waiting for ports to be released..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Write-Host "  Ready" -ForegroundColor Green
Write-Host ""

# Step 4: Verify ports are available
Write-Host "Step 4: Verifying ports are available..." -ForegroundColor Yellow
$allClear = $true

foreach ($port in $portsToClean) {
    try {
        $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($connection) {
            Write-Host "  Port $port still occupied!" -ForegroundColor Red
            $allClear = $false
        }
    } catch {
        # Port is free, good
    }
}

if ($allClear) {
    Write-Host "  All ports available" -ForegroundColor Green
} else {
    Write-Host "  Warning: Some ports still occupied" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Restart desktop app
Write-Host "Step 5: Starting desktop app..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================="-ForegroundColor Cyan
Write-Host "Running: npm run dev:electron" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Run npm command
npm run dev:electron
