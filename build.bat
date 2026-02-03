@echo off
echo GitHub Streak Tracker - Windows Build
echo.

echo Installing dependencies...
pip install pyinstaller requests plyer

echo.
echo Building executable...
pyinstaller --onefile --windowed --name "GitHubStreakTracker" streak_gui.py

echo.
echo Build complete!
echo Executable: .\dist\GitHubStreakTracker.exe
echo.
pause
