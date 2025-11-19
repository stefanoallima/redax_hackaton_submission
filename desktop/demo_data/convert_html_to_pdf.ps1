# Convert HTML lease agreements to PDF using Chrome headless
# PowerShell script

Write-Host "`nConverting HTML Lease Agreements to PDF..." -ForegroundColor Green
Write-Host "=" * 60

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$htmlFiles = Get-ChildItem -Path $scriptPath -Filter "lease_*_UNREDACTED.html" | Sort-Object Name

if ($htmlFiles.Count -eq 0) {
    Write-Host "No HTML files found!" -ForegroundColor Red
    exit 1
}

Write-Host "Found $($htmlFiles.Count) HTML files`n"

# Find Chrome
$chromePaths = @(
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe"
)

$chrome = $null
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        $chrome = $path
        break
    }
}

if (-not $chrome) {
    Write-Host "Chrome not found. Please install Google Chrome or convert manually." -ForegroundColor Red
    Write-Host "`nManual conversion:"
    Write-Host "1. Open each HTML file in your browser"
    Write-Host "2. Press Ctrl+P (Print)"
    Write-Host "3. Select 'Save as PDF'"
    Write-Host "4. Save in the same folder"
    exit 1
}

Write-Host "Using Chrome: $chrome`n"

$success = 0
$failed = 0

foreach ($htmlFile in $htmlFiles) {
    $htmlPath = $htmlFile.FullName
    $pdfPath = $htmlPath -replace '\.html$', '.pdf'
    $pdfFile = [System.IO.Path]::GetFileName($pdfPath)

    Write-Host "Converting: $($htmlFile.Name)" -NoNewline

    try {
        # Use Chrome headless to convert HTML to PDF
        $args = @(
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--print-to-pdf-no-header",
            "--print-to-pdf=`"$pdfPath`"",
            "file:///$($htmlPath -replace '\\', '/')"
        )

        $process = Start-Process -FilePath $chrome -ArgumentList $args -Wait -PassThru -WindowStyle Hidden

        if (Test-Path $pdfPath) {
            $fileSize = (Get-Item $pdfPath).Length / 1KB
            Write-Host " -> OK ($([math]::Round($fileSize, 1)) KB)" -ForegroundColor Green
            $success++
        } else {
            Write-Host " -> FAILED" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host " -> ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n" + ("=" * 60)
Write-Host "Conversion Complete!" -ForegroundColor Green
Write-Host "Success: $success | Failed: $failed"
Write-Host "`nPDF files created in: $scriptPath"

if ($success -gt 0) {
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "1. Open RedaxAI desktop app"
    Write-Host "2. Upload lease_01_UNREDACTED.pdf"
    Write-Host "3. Run standard detection and redact"
    Write-Host "4. Export as lease_01_REDACTED.pdf"
    Write-Host "5. Use redacted version to teach the system"
}
