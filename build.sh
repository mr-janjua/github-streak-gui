#!/bin/bash

echo "🔥 GitHub Streak Tracker - Build Script 🔥"
echo ""

echo "Installing build dependencies..."
pip install --break-system-packages pyinstaller requests plyer

echo ""
echo "Building executable..."

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Building for Linux..."
    pyinstaller --onefile --windowed --name "GitHubStreakTracker" streak_gui.py
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Building for macOS..."
    pyinstaller --onefile --windowed --name "GitHubStreakTracker" streak_gui.py
    
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Building for Windows..."
    pyinstaller --onefile --windowed --name "GitHubStreakTracker" streak_gui.py
fi

echo ""
echo "✓ Build complete!"
echo ""
echo "Executable location:"
echo "  - Linux/macOS: ./dist/GitHubStreakTracker"
echo "  - Windows: ./dist/GitHubStreakTracker.exe"
echo ""
echo "You can distribute the file in the 'dist' folder!"
