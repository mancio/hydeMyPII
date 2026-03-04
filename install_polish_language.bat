@echo off
REM This script installs Polish language support for Tesseract OCR
REM Right-click this file and select "Run as administrator"

setlocal enabledelayedexpansion

echo.
echo Installing Polish language for Tesseract OCR...
echo.

set TEMPFILE="%TEMP%\pol.traineddata"
set DESTFILE="C:\Program Files\Tesseract-OCR\tessdata\pol.traineddata"

if not exist %TEMPFILE% (
    echo Error: Polish language file not found at %TEMPFILE%
    echo Please run the Python script first to download the file.
    pause
    exit /b 1
)

echo Copying Polish language file...
copy %TEMPFILE% %DESTFILE%

if exist %DESTFILE% (
    echo.
    echo SUCCESS! Polish language installed at:
    echo %DESTFILE%
    echo.
    echo You can now use Polish language support in hydeMyPII:
    echo - CLI: hydemypii document.pdf --ocr --ocr-lang pol
    echo - GUI: Select 'pol' from the OCR language dropdown
    echo.
) else (
    echo Error: File copy failed. Please check administrator privileges.
    echo.
)

pause
