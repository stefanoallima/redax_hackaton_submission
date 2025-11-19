# Testing Instructions - Redaction Fix Verification

## Quick Start - Test the Fix Now

### Method 1: Run Full Desktop App (Recommended)

1. **Open a terminal in the `desktop` directory:**
   ```bash
   cd desktop
   ```

2. **Start the development server:**
   ```bash
   npm run electron:dev
   ```

3. **The app will open automatically**
   - You'll see the main window with file upload
   - The Python backend starts automatically in the background

4. **Test the redaction:**
   - Click "Select Document"
   - Choose: `test_documents/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf`
   - Click "Detect PII"
   - Wait for detection to complete (shows entities in table)
   - Select the entities you want to redact
   - Click "Export Redacted PDF"
   - Choose output location

5. **Verify the fix:**
   - Open the redacted PDF
   - **Page 1:** Check that "REPUBBLICA ITALIANA" is **VISIBLE** ✅
   - **Page 2:** Check that email is **REDACTED** ✅

---

### Method 2: Backend Only (For Quick CLI Testing)

If you just want to test the backend without the full UI:

1. **Navigate to Python directory:**
   ```bash
   cd desktop/src/python
   ```

2. **Activate virtual environment:**
   ```bash
   venv\Scripts\activate
   ```

3. **Run the backend:**
   ```bash
   python main.py
   ```

   You should see:
   ```
   {"status": "ready"}
   ```

4. **In another terminal, send a test command:**
   ```bash
   cd desktop
   python test_backend_command.py
   ```

   (I can create this test script if you want to test via CLI)

---

### Method 3: Run Automated Test

The comprehensive test we just ran:

```bash
cd desktop/src/python
venv\Scripts\python.exe ..\..\run_comprehensive_test.py
```

This will:
- ✅ Extract text from PDF
- ✅ Detect PII entities
- ✅ Map entity locations
- ✅ Export redacted PDF
- ✅ Verify REPUBBLICA ITALIANA is visible
- ✅ Generate report

---

## Expected Results After Fix

### ✅ Correct Behavior (After Fix)

**Page 1:**
```
REPUBBLICA ITALIANA
IN NOME DEL POPOLO ITALIANO
```
→ **VISIBLE** (not redacted, because it's not PII)

**Page 2:**
```
(avv.marcovannini@pec.com
```
→ **REDACTED to:** `[EML1------------------]`

**Mapping Table CSV:**
- Contains ~13-19 entities
- Each entity shows: Original Text → Placeholder → Type

---

### ❌ Old Behavior (Before Fix)

**Page 1:**
```
ANA
IN NOME DEL POPOLO ITALIANO
```
→ "REPUBBLICA ITALI" was incorrectly redacted, leaving only "ANA"

**Reason:** Email from page 2 was incorrectly applied to page 1 due to page numbering bug

---

## Troubleshooting

### Backend Not Starting

If you see "Python process not running":

1. Check Python is installed:
   ```bash
   desktop\src\python\venv\Scripts\python.exe --version
   ```

2. Check dependencies are installed:
   ```bash
   cd desktop/src/python
   venv\Scripts\pip.exe list
   ```

3. Check logs:
   ```bash
   type desktop\src\python\redact.log
   ```

### Desktop App Not Opening

1. **Check if Node modules are installed:**
   ```bash
   cd desktop
   npm install
   ```

2. **Check if Electron is available:**
   ```bash
   npm run electron:dev
   ```

3. **Check console output** for errors

### Redaction Not Working

1. **Check backend is running:**
   - Look for "Python backend started" in console
   - Check `desktop/src/python/redact.log`

2. **Check file format:**
   - Must be PDF, DOCX, or TXT
   - File size < 100MB

3. **Check entity detection:**
   - At least some entities should be detected
   - Check if entities have locations

---

## Test Files Available

Located in `desktop/test_documents/`:

1. **sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf**
   - Italian legal document
   - Contains PII: names, emails, addresses
   - **THIS IS THE FILE WITH THE REPUBBLICA BUG** ← Use this!

2. **italian_pii_comprehensive_test.txt**
   - Text file with various PII types
   - Good for testing detection accuracy

---

## Quick Verification Commands

### Check if fix is applied:
```bash
cd desktop/src/python
grep -n "page_num + 1" pii_detector.py
```

Should show:
```
498:    'page': page_num + 1,  # Store as 1-based page number
```

### Check backend status:
```bash
cd desktop/src/python
type redact.log | findstr /C:"Python backend started"
```

### Compare old vs new PDF:
```bash
cd desktop/test_documents

# Old PDF (before fix) - should show "ANA"
python -c "import fitz; doc=fitz.open('sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban_REDACTED.pdf'); print(doc[0].search_for('REPUBBLICA ITALIANA'))"

# New PDF (after fix) - should show full text
python -c "import fitz; doc=fitz.open('sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban_TEST_REDACTED.pdf'); print(doc[0].search_for('REPUBBLICA ITALIANA'))"
```

---

## Next Steps After Testing

1. ✅ Verify REPUBBLICA ITALIANA is visible in redacted PDF
2. ✅ Verify all PII entities are correctly redacted on their pages
3. ✅ Check mapping table CSV matches redactions
4. ⏭️ (Optional) Filter false positive detections (titles, legal terms)

---

## Need Help?

- Check `REDACTION_FIX_REPORT.md` for detailed technical analysis
- Check `redact.log` for backend execution logs
- Check browser console (F12) for frontend errors
- Check Electron console output for IPC errors
