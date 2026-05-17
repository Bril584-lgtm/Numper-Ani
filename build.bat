@echo off
echo ========================================
echo  Numper Ani - Build EXE
echo ========================================

echo Installing / upgrading dependencies...
pip install -r requirements.txt pyinstaller --quiet

echo Building executable...
pyinstaller numper.spec --clean --noconfirm

echo.
if exist "dist\NumperAni.exe" (
    echo  Build successful: dist\NumperAni.exe
    echo.
    echo  NOTE: First run will auto-install Playwright Chromium browser.
    echo  This is a one-time 150MB download.
) else (
    echo  Build FAILED. Check output above.
)
pause
