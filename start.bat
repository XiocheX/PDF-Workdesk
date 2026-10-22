@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 goto nopy
if not exist .venv\Scripts\activate.bat python -m venv .venv
call .venv\Scripts\activate.bat
python -c "import flask, pymupdf" >nul 2>nul
if errorlevel 1 pip install -r requirements.txt
if not exist tessdata\eng.traineddata call :getocr
echo Starting PDF Workbench. Close this window to stop it.
python app.py %*
pause
goto :eof

:getocr
echo Downloading English OCR data, one time only...
mkdir tessdata 2>nul
powershell -NoProfile -Command "try{Invoke-WebRequest -UseBasicParsing https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata -OutFile tessdata\eng.traineddata}catch{}"
goto :eof

:nopy
echo Python is not installed. Install it from python.org and tick "Add Python to PATH", then run this again.
pause
