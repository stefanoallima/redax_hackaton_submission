@echo off
REM Test File Generator for Error Handling Tests
REM Creates various invalid/edge-case files for testing

echo ========================================
echo Creating Test Files for Error Testing
echo ========================================
echo.

set TEST_DIR=test_documents\error_tests
if not exist "%TEST_DIR%" mkdir "%TEST_DIR%"

echo [1/7] Creating empty PDF (0 bytes)...
type nul > "%TEST_DIR%\empty_file.pdf"
echo    ✓ Created: %TEST_DIR%\empty_file.pdf

echo.
echo [2/7] Creating corrupted PDF (text file with .pdf extension)...
echo This is not a real PDF file. Just plain text. > "%TEST_DIR%\corrupted.pdf"
echo    ✓ Created: %TEST_DIR%\corrupted.pdf

echo.
echo [3/7] Creating invalid file types...
echo Test content > "%TEST_DIR%\test_image.jpg"
echo Test content > "%TEST_DIR%\test_document.txt"
echo Test content > "%TEST_DIR%\test_archive.zip"
echo    ✓ Created: %TEST_DIR%\test_image.jpg
echo    ✓ Created: %TEST_DIR%\test_document.txt
echo    ✓ Created: %TEST_DIR%\test_archive.zip

echo.
echo [4/7] Creating large dummy file (110MB)...
echo    (This may take a minute...)
fsutil file createnew "%TEST_DIR%\large_file.pdf" 115343360 >nul 2>&1
if %errorlevel% equ 0 (
    echo    ✓ Created: %TEST_DIR%\large_file.pdf ^(110MB^)
) else (
    echo    ⚠ Failed to create large file ^(requires admin rights^)
    echo    ⚠ Run this script as Administrator to create large test file
)

echo.
echo [5/7] Creating PDF with special characters in filename...
echo Test > "%TEST_DIR%\file with spaces & special-chars!.pdf"
echo    ✓ Created: %TEST_DIR%\file with spaces ^& special-chars!.pdf

echo.
echo [6/7] Creating minimal valid PDF (for baseline test)...
REM This creates the smallest valid PDF structure
(
echo %%PDF-1.4
echo 1 0 obj ^<^< /Type /Catalog /Pages 2 0 R ^>^> endobj
echo 2 0 obj ^<^< /Type /Pages /Kids [3 0 R] /Count 1 ^>^> endobj
echo 3 0 obj ^<^< /Type /Page /Parent 2 0 R /Resources ^<^< ^>^> /MediaBox [0 0 612 792] ^>^> endobj
echo xref
echo 0 4
echo 0000000000 65535 f
echo 0000000009 00000 n
echo 0000000058 00000 n
echo 0000000115 00000 n
echo trailer ^<^< /Size 4 /Root 1 0 R ^>^>
echo startxref
echo 218
echo %%%%EOF
) > "%TEST_DIR%\minimal_valid.pdf"
echo    ✓ Created: %TEST_DIR%\minimal_valid.pdf

echo.
echo [7/7] Creating test summary file...
(
echo Test Files Created: %date% %time%
echo ==========================================
echo.
echo Directory: %TEST_DIR%
echo.
echo Files Created:
echo   1. empty_file.pdf         - 0 bytes, should fail
echo   2. corrupted.pdf          - Text file renamed, should fail
echo   3. test_image.jpg         - Invalid type, should be rejected
echo   4. test_document.txt      - Invalid type, should be rejected
echo   5. test_archive.zip       - Invalid type, should be rejected
echo   6. large_file.pdf         - 110MB, should be rejected (^>100MB limit^)
echo   7. file with spaces...    - Test special characters handling
echo   8. minimal_valid.pdf      - Smallest valid PDF, should work
echo.
echo Usage:
echo   1. Try uploading each file to the app
echo   2. Verify error messages are user-friendly
echo   3. Check that invalid files are rejected gracefully
echo   4. Ensure app doesn't crash on any file
echo   5. Verify valid PDF (minimal_valid.pdf^) processes successfully
echo.
echo Reference: ERROR_HANDLING_TEST_PLAN.md
) > "%TEST_DIR%\README.txt"
echo    ✓ Created: %TEST_DIR%\README.txt

echo.
echo ========================================
echo ✓ All test files created successfully!
echo ========================================
echo.
echo Location: %CD%\%TEST_DIR%
echo.
echo Next Steps:
echo   1. Open the app (npm run dev or npm run build)
echo   2. Follow ERROR_HANDLING_TEST_PLAN.md
echo   3. Test each file and document results
echo   4. Update logs\ERROR_DEBUG_LOG.md with findings
echo.
pause
