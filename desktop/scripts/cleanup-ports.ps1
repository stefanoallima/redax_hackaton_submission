# Cleanup script for stopping all development servers
# Kills processes on common development ports

Write-Host "Cleaning up development servers..." -ForegroundColor Yellow

# Ports used by the desktop app
$ports = @(5173, 5174, 5175, 5176, 5177, 5178, 5179)

foreach ($port in $ports) {
    Write-Host "Checking port $port..." -ForegroundColor Cyan

    # Find process using the port
    $connections = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"

    if ($connections) {
        foreach ($connection in $connections) {
            # Extract PID from netstat output (use processId instead of reserved $pid)
            $processId = ($connection -split '\s+')[-1]

            if ($processId -and $processId -match '^\d+$') {
                try {
                    $process = Get-Process -Id $processId -ErrorAction Stop
                    Write-Host "  Killing process $($process.Name) (PID: $processId) on port $port" -ForegroundColor Red
                    Stop-Process -Id $processId -Force
                    Start-Sleep -Milliseconds 500
                } catch {
                    Write-Host "  Process $processId already terminated" -ForegroundColor Gray
                }
            }
        }
    } else {
        Write-Host "  Port $port is free" -ForegroundColor Green
    }
}

# Also kill any processes specifically running electron or vite
# Use command line detection to avoid killing npm process chain
Write-Host "`nCleaning up electron and vite processes..." -ForegroundColor Yellow

try {
    $processesKilled = 0

    # Get all processes with their command lines using WMI
    $processes = Get-WmiObject Win32_Process -Filter "Name='electron.exe' OR Name='node.exe'" -ErrorAction SilentlyContinue

    foreach ($proc in $processes) {
        $commandLine = $proc.CommandLine

        # Only kill if command line contains electron or vite (not npm or other node processes)
        if ($commandLine -match "electron|vite" -and $commandLine -notmatch "npm|powershell|cleanup") {
            try {
                Write-Host "  Stopping $($proc.Name) (PID: $($proc.ProcessId))" -ForegroundColor Red
                Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
                $processesKilled++
            } catch {
                # Process may have already terminated, ignore
            }
        }
    }

    # Wait for processes to fully terminate
    if ($processesKilled -gt 0) {
        Start-Sleep -Milliseconds 1000
        Write-Host "  Stopped $processesKilled process(es)" -ForegroundColor Green
    } else {
        Write-Host "  No stale electron/vite processes found" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Error during process cleanup: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`nCleanup complete!" -ForegroundColor Green
Write-Host "You can now run: npm run electron:dev" -ForegroundColor Cyan

# Explicit success exit to ensure npm continues
exit 0
