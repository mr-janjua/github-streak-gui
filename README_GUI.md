# GitHub Streak Tracker - GUI Edition 🔥

Beautiful cross-platform desktop app that helps you maintain your GitHub contribution streak with Duolingo-style motivation.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)

## Features

### 📊 Visual Dashboard
- Real-time streak counter with beautiful UI
- Track current streak, longest streak, and total active days
- Activity log showing all checks and events
- Clean, modern interface

### 🔔 Smart Notifications
- Desktop notifications at 9 AM, 2 PM, and 8 PM
- Only reminds you if you haven't committed yet
- Two reminder modes:
  - **Normal**: Friendly, encouraging messages
  - **Strict**: Aggressive Duolingo-owl style threats

### 🎯 Automatic Monitoring
- Background monitoring throughout the day
- Auto-start option (monitors when you open the app)
- Manual check button anytime
- Detects: pushes, PRs, issues, commits, comments

### 💾 Persistent Data
- All streak data saved locally
- Survives app restarts
- Privacy-focused (data never leaves your machine)

## Screenshots

```
┌─────────────────────────────────────────────┐
│  🔥 GitHub Streak Tracker      ⚙️ Settings  │
├─────────────────────────────────────────────┤
│                                             │
│  Current Streak    Longest Streak  Total   │
│       47              52            183     │
│     days 🔥        days 🏆       days 💎   │
│                                             │
│  Last Commit: 2026-02-01                   │
│  Mode: STRICT                               │
│                                             │
│  ✓ Streak safe for today!                  │
│                                             │
│  Activity Log                               │
│  ┌───────────────────────────────────────┐ │
│  │ [09:23] Running manual check...       │ │
│  │ [09:23] ✓ Activity detected!          │ │
│  │ [09:23] Streak: 47 days               │ │
│  └───────────────────────────────────────┘ │
│                                             │
│    ▶ Start Monitoring    ⏸ Stop           │
└─────────────────────────────────────────────┘
```

## Installation

### Option 1: Download Pre-Built Executable (Recommended)

**Windows:**
1. Download `GitHubStreakTracker.exe`
2. Double-click to run
3. No installation needed!

**macOS:**
1. Download `GitHubStreakTracker.app`
2. Move to Applications folder
3. First run: Right-click → Open (to bypass security)

**Linux:**
1. Download `GitHubStreakTracker`
2. Make executable: `chmod +x GitHubStreakTracker`
3. Run: `./GitHubStreakTracker`

### Option 2: Run from Source

```bash
# Install dependencies
pip install requests plyer

# Run the GUI
python3 streak_gui.py
```

### Option 3: Build Your Own Executable

```bash
# Linux/macOS
./build.sh

# Windows
build.bat
```

Executable will be in `dist/` folder.

## Setup

### First Time Setup

1. **Get GitHub Personal Access Token**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Name: "Streak Tracker"
   - Select scopes: `repo` and `user`
   - Click "Generate token"
   - Copy the token (you won't see it again!)

2. **Launch the App**
   - Enter your GitHub username
   - Paste your token
   - Choose reminder mode:
     - **Normal**: "💚 Keep your 5 day streak alive!"
     - **Strict**: "🦉 Your streak is DEAD. Get coding NOW!"
   - Click "Save & Continue"

3. **Start Monitoring**
   - Click "▶ Start Monitoring"
   - App will check at 9 AM, 2 PM, and 8 PM daily
   - Desktop notifications will appear

## Usage

### Main Dashboard
- **Current Streak**: Your ongoing streak (resets if you miss a day)
- **Longest Streak**: Your personal best
- **Total Days**: All days you've contributed
- **Status**: Shows if you've committed today

### Buttons
- **📊 Check Now**: Manually check GitHub activity
- **⚙️ Settings**: Update username, token, or mode
- **▶ Start Monitoring**: Begin automatic checks
- **⏸ Stop Monitoring**: Pause automatic checks

### Reminder Examples

**Normal Mode:**
- "💚 Start your GitHub streak today!"
- "🔥 5 day streak! You're building momentum!"
- "⏰ Evening reminder: Keep your 15 day streak alive!"

**Strict Mode:**
- "🦉 Your streak is DEAD. Get coding NOW or lose everything!"
- "🔴 FINAL WARNING! Your 47 day streak dies at midnight!"
- "💀 LAST CHANCE! Commit NOW or lose 47 days!"

## Building Executables

### Requirements
- Python 3.7+
- PyInstaller
- Dependencies: requests, plyer

### Build Commands

**All Platforms:**
```bash
pyinstaller --onefile --windowed --name "GitHubStreakTracker" streak_gui.py
```

**Custom Icon (Optional):**
```bash
# Add --icon=icon.ico flag
pyinstaller --onefile --windowed --icon=streak_icon.ico --name "GitHubStreakTracker" streak_gui.py
```

**Smaller File Size:**
```bash
# Use UPX compression
pyinstaller --onefile --windowed --upx-dir=/path/to/upx --name "GitHubStreakTracker" streak_gui.py
```

### Distribution

After building, distribute the file from `dist/`:
- **Windows**: `GitHubStreakTracker.exe` (~15-20 MB)
- **macOS**: `GitHubStreakTracker.app` (~20-25 MB)
- **Linux**: `GitHubStreakTracker` (~18-22 MB)

## Auto-Start on Boot

### Windows
1. Press `Win + R`
2. Type `shell:startup`
3. Copy `GitHubStreakTracker.exe` shortcut here

### macOS
1. System Preferences → Users & Groups
2. Login Items
3. Click `+` and add the app

### Linux
1. Create `~/.config/autostart/github-streak.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=GitHub Streak Tracker
Exec=/path/to/GitHubStreakTracker
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

## Privacy & Security

- **Token Storage**: Stored locally in `~/.github_streak/config.json`
- **Network**: Only connects to GitHub API
- **Data**: Never sent to any server except GitHub
- **Permissions**: Token needs `repo` and `user` scopes only

### Token Security
- Stored in plain text locally (only you can read it)
- Never share your token
- Revoke old tokens at https://github.com/settings/tokens
- Generate new token if compromised

## Troubleshooting

### "Could not check GitHub"
- Check internet connection
- Verify token is valid at https://github.com/settings/tokens
- Token needs `repo` and `user` scopes

### Notifications Not Working
- **Windows**: Check notification settings
- **macOS**: System Preferences → Notifications
- **Linux**: Install `notify-send` or `libnotify`

### App Won't Start
- Check Python version: `python3 --version` (need 3.7+)
- Reinstall dependencies: `pip install requests plyer`
- Run from terminal to see errors

### Streak Not Updating
- Click "📊 Check Now" to force update
- Verify you committed to GitHub today
- Check activity log for errors

## Development

### Project Structure
```
github-streak-tracker/
├── streak_gui.py          # Main GUI application
├── streak.py              # CLI version (legacy)
├── build.sh               # Linux/macOS build script
├── build.bat              # Windows build script
├── streak_gui.spec        # PyInstaller spec file
└── requirements_gui.txt   # Dependencies
```

### Dependencies
- `tkinter` - GUI (included with Python)
- `requests` - GitHub API calls
- `plyer` - Cross-platform notifications

### Contributing
Pull requests welcome! Please:
1. Test on your platform
2. Follow existing code style
3. Update README if adding features

## FAQ

**Q: Will this work with private repos?**
A: Yes, if your token has `repo` scope.

**Q: Does it count PR reviews or comments?**
A: Yes! It counts pushes, PRs, issues, commits, and comments.

**Q: Can I run it on multiple computers?**
A: Yes, but each tracks independently. Streaks won't sync.

**Q: What happens if I miss a day?**
A: Current streak resets to 0. Longest streak is preserved.

**Q: Can I change the check times?**
A: Currently fixed at 9 AM, 2 PM, 8 PM. Fork the code to customize!

## License

MIT License - Free to use, modify, and distribute.

## Credits

Inspired by Duolingo's persistent reminder system (minus the threatening owl... mostly).

Built with ❤️ for developers who want consistent GitHub contributions.

---

**Remember**: Quality > Quantity. This app encourages consistency, but meaningful contributions matter more than green squares! 💚
