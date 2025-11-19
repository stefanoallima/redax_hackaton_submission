; Custom NSIS installer script for Python dependencies
; This runs during installation to set up Python environment

; Install Python (bundled or system)
Section "Python Setup"
  ; Check if Python is installed
  nsExec::ExecToLog 'python --version'
  Pop $0
  
  ${If} $0 != 0
    ; Python not found, install bundled version
    DetailPrint "Installing Python..."
    File /r "python-installer.exe"
    ExecWait '"$INSTDIR\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1'
    Delete "$INSTDIR\python-installer.exe"
  ${EndIf}
SectionEnd

; Install Python dependencies
Section "Install Dependencies"
  DetailPrint "Installing Python dependencies..."
  
  ; Install pip packages
  nsExec::ExecToLog 'python -m pip install --upgrade pip'
  nsExec::ExecToLog 'python -m pip install -r "$INSTDIR\resources\python\requirements.txt"'
  
  ; Download spaCy Italian model
  DetailPrint "Downloading Italian language model..."
  nsExec::ExecToLog 'python -m spacy download it_core_news_lg'
  
  ; Download Tesseract Italian data (if not bundled)
  ; DetailPrint "Installing Tesseract language data..."
  ; File /r "tessdata\ita.traineddata"
SectionEnd

; Verify installation
Section "Verify Installation"
  DetailPrint "Verifying installation..."
  
  ; Test imports
  nsExec::ExecToLog 'python -c "import presidio_analyzer; import pytesseract; import spacy; print(\"OK\")"'
  Pop $0
  
  ${If} $0 != 0
    MessageBox MB_OK "Warning: Some dependencies may not be properly installed. The app may not function correctly."
  ${EndIf}
SectionEnd
