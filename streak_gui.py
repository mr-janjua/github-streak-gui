#!/usr/bin/env python3

import dearpygui.dearpygui as dpg
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

class GitHubStreakGUI:
    def __init__(self):
        self.config_dir = Path.home() / ".github_streak"
        self.config_file = self.config_dir / "config.json"
        self.streak_file = self.config_dir / "streak.json"
        self.config_dir.mkdir(exist_ok=True)
        
        self.username = ""
        self.token = ""
        self.reminder_mode = "normal"
        self.auto_start = True
        
        self.streak_data = self.load_streak_data()
        self.is_running = False
        self.check_thread = None
        
        self.load_config()
        
        # Animation values
        self.current_streak_animated = 0
        self.longest_streak_animated = 0
        self.total_days_animated = 0
        
        self.setup_dpg()
    
    def setup_dpg(self):
        dpg.create_context()
        
        # Load default font with larger size for stats
        with dpg.font_registry():
            self.default_font = dpg.add_font("fonts/Roboto-Black.ttf", 13, default_font=True)
            self.large_font = dpg.add_font("fonts/Roboto-Bold.ttf", 120,)
            self.title_font = dpg.add_font("fonts/Roboto-Black.ttf", 32)
            self.stat_font = dpg.add_font("fonts/Roboto-Black.ttf", 38)
            self.github_font = dpg.add_font("fonts/Roboto-Black.ttf", 38)
            self.medium_font = dpg.add_font("fonts/Roboto-Black.ttf", 20)
            self.button_font = dpg.add_font("fonts/Roboto-Black.ttf", 14)
            # Font used for status messages (success/warning). Adjust size here.
            self.status_font = dpg.add_font("fonts/Roboto-Black.ttf", 16)
        
        # Color palette - Darker shades
        self.bg_color = (21, 2, 29, 1)
        self.fg_color = (219, 219, 219, 255)
        self.accent_color = (200, 60, 60, 255)  # Darker red
        self.secondary_color = (50, 155, 148, 255)  # Darker teal
        self.success_color = (46, 204, 113, 255)
        self.warning_color = (231, 76, 60, 255)
        self.card_bg = (22, 11, 32, 255)

        self.headLine = (255, 255, 255, 255)
        self.buttonAccent = (180, 60, 60, 255)
        self.buttonAccentSecondary = (100, 100, 100, 255)
        self.buttonAccentHover = (220, 70, 70, 255)
        self.buttonAccentSecondaryHover = (130, 130, 130, 255)

        # Setup themes
        self.create_themes()
        
        # Create main window
        with dpg.window(tag="main_window", label="GitHub Streak Tracker", 
                       width=900, height=620, no_close=True):
            
            if self.username and self.token:
                self.show_main_view()
            else:
                self.show_setup_view()
        
        # Setup viewport
        dpg.create_viewport(title="GitHub Streak Tracker. A project by github/mr-janjua", width=920, height=720)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        # Apply global theme
        dpg.bind_theme(self.global_theme)
        
        # Auto-start if configured
        if self.auto_start and self.username and self.token:
            dpg.set_frame_callback(5, self.start_monitoring)
    
    def create_themes(self):
        # Global theme
        with dpg.theme() as self.global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, self.bg_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, self.card_bg, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, self.fg_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, self.card_bg, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 0, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 8, category=dpg.mvThemeCat_Core)
        
        # Button theme (accent color) - Darker
        with dpg.theme() as self.button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.buttonAccent, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, self.buttonAccentHover, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, self.buttonAccentHover, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 12, category=dpg.mvThemeCat_Core)
        
        # Secondary button theme - Darker
        with dpg.theme() as self.secondary_button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.buttonAccentSecondary, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, self.buttonAccentSecondaryHover, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, self.buttonAccentSecondaryHover, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 12, category=dpg.mvThemeCat_Core)
        
        # Success theme
        with dpg.theme() as self.success_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, self.success_color, category=dpg.mvThemeCat_Core)
                
        
        # Warning theme
        with dpg.theme() as self.warning_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, self.warning_color, category=dpg.mvThemeCat_Core)
        
        # Input theme
        with dpg.theme() as self.input_theme:
            with dpg.theme_component(dpg.mvInputText):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (42, 42, 62, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (52, 52, 72, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8, category=dpg.mvThemeCat_Core)
        
        # Card theme
        with dpg.theme() as self.card_theme:
            with dpg.theme_component(dpg.mvChildWindow):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, self.card_bg, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, self.secondary_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 2, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)
                # Aggressively reduce vertical spacing inside cards (shrink "line-height")
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 0, 0, category=dpg.mvThemeCat_Core)
    
    def clear_window(self):
        dpg.delete_item("main_window", children_only=True)
    
    def show_setup_view(self):
        self.clear_window()
        
        with dpg.group(parent="main_window"):
            dpg.add_spacer(height=30)
            
            # Title
            title_text = dpg.add_text("GitHub Streak Tracker. A project by github/mr-janjua", 
                        color=self.headLine)
            dpg.bind_item_font(title_text, self.large_font)
            
            dpg.add_spacer(height=20)
            setup_text = dpg.add_text("Setup", color=self.fg_color)
            dpg.bind_item_font(setup_text, self.medium_font)
            
            dpg.add_spacer(height=30)
            
            # Setup form
            with dpg.group(horizontal=True):
                dpg.add_text("GitHub Username:", color=self.fg_color)
                dpg.add_spacer(width=20)
                dpg.add_input_text(tag="username_input", default_value=self.username, 
                                 width=400, hint="your-github-username")
                dpg.bind_item_theme(dpg.last_item(), self.input_theme)
            
            dpg.add_spacer(height=15)
            
            with dpg.group(horizontal=True):
                dpg.add_text("Access Token:     ", color=self.fg_color)
                dpg.add_spacer(width=20)
                dpg.add_input_text(tag="token_input", default_value=self.token, 
                                 width=400, password=True, hint="ghp_...")
                dpg.bind_item_theme(dpg.last_item(), self.input_theme)
            
            dpg.add_spacer(height=10)
            dpg.add_text("Get token from: https://github.com/settings/tokens", 
                        color=self.secondary_color)
            
            dpg.add_spacer(height=25)
            
            with dpg.group(horizontal=True):
                dpg.add_text("Reminder Mode:", color=self.fg_color)
                dpg.add_spacer(width=20)
                dpg.add_radio_button(items=["Normal (Friendly)", "Strict (Duolingo Mode)"], 
                                   tag="reminder_mode_radio",
                                   default_value="Normal (Friendly)" if self.reminder_mode == "normal" else "Strict (Duolingo Mode)",
                                   horizontal=True)
            
            dpg.add_spacer(height=40)
            
            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=250)
                btn = dpg.add_button(label="Save & Continue", width=200, height=45,
                                   callback=self.save_and_continue)
                dpg.bind_item_theme(btn, self.button_theme)
                
                if self.config_file.exists():
                    dpg.add_spacer(width=20)
                    btn2 = dpg.add_button(label="Back to Dashboard", width=200, height=45,
                                        callback=self.show_main_view)
                    dpg.bind_item_theme(btn2, self.secondary_button_theme)
    
    def show_main_view(self):
        self.clear_window()
        
        # Save current monitoring state before rebuilding UI
        was_running = self.is_running
        
        with dpg.group(parent="main_window"):
            dpg.add_spacer(height=10)
            
            # Header
            with dpg.group(horizontal=True):
                header_text = dpg.add_text("GitHub Streak Tracker", color=self.headLine)
                dpg.bind_item_font(header_text, self.stat_font)
                
                dpg.add_spacer(width=250)
                
                btn = dpg.add_button(label="Check Now", width=140, height=40,
                                   callback=lambda: threading.Thread(target=self.manual_check, daemon=True).start())
                dpg.bind_item_theme(btn, self.secondary_button_theme)
                dpg.bind_item_font(btn, self.button_font)
                
                dpg.add_spacer(width=10)
                
                btn2 = dpg.add_button(label="Settings", width=140, height=40,
                                    callback=self.show_setup_view)
                dpg.bind_item_theme(btn2, self.button_theme)
                dpg.bind_item_font(btn2, self.button_font)
            
            dpg.add_spacer(height=15)
            
            # Stats cards
            with dpg.child_window(height=200, border=True, tag="stats_container"):
                dpg.bind_item_theme("stats_container", self.card_theme)
                
                dpg.add_spacer(height=10)
                
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=50)
                    
                    # Current Streak
                    with dpg.group():
                        label1 = dpg.add_text("Current Streak", color=self.fg_color)
                        dpg.bind_item_font(label1, self.stat_font)
                        dpg.add_spacer(height=0)
                        streak_text = dpg.add_text(str(self.streak_data['current_streak']), tag="current_streak_display", color=(231, 76, 60, 255))
                        dpg.bind_item_font(streak_text, self.large_font)
                        # days_label = dpg.add_text("days 🔥", color=self.fg_color)
                        # dpg.bind_item_font(days_label, self.medium_font)
                    
                    dpg.add_spacer(width=80)
                    
                    # Longest Streak
                    with dpg.group():
                        label2 = dpg.add_text("Longest Streak", color=self.fg_color)
                        dpg.bind_item_font(label2, self.stat_font)
                        dpg.add_spacer(height=0)
                        longest_text = dpg.add_text(str(self.streak_data['longest_streak']), tag="longest_streak_display", color=(243, 156, 18, 255))
                        dpg.bind_item_font(longest_text, self.large_font)
                        # days_label = dpg.add_text("days 🏆", color=self.fg_color)
                        # dpg.bind_item_font(days_label, self.medium_font)
                    
                    dpg.add_spacer(width=80)
                    
                    # Total Days
                    with dpg.group():
                        label3 = dpg.add_text("Total Days", color=self.fg_color)
                        dpg.bind_item_font(label3, self.stat_font)
                        dpg.add_spacer(height=0)
                        total_text = dpg.add_text(str(self.streak_data['total_days']), tag="total_days_display", color=(52, 152, 219, 255))
                        dpg.bind_item_font(total_text, self.large_font)
                        # days_label = dpg.add_text("days 💎", color=self.fg_color)
                        # dpg.bind_item_font(days_label, self.medium_font)
                
                dpg.add_spacer(height=10)
                
                # Info
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=30)
                    with dpg.group():
                        last_commit = self.streak_data.get('last_commit_date', 'Never')
                        dpg.add_text(f"Last Commit: {last_commit}", tag="last_commit_text", color=self.fg_color)
                        dpg.bind_item_font("last_commit_text", self.medium_font)
                        dpg.add_text(f"Mode: {self.reminder_mode.upper()}", tag="mode_text", color=self.fg_color)
                        dpg.bind_item_font("mode_text", self.medium_font)
                        dpg.add_text(f"Username: {self.username}", tag="username_text", color=self.fg_color)
                        dpg.bind_item_font("username_text", self.medium_font)
            
            dpg.add_spacer(height=10)
            
            # Status message
            dpg.add_text("", tag="status_message")
            
            dpg.add_spacer(height=10)
            
            # Activity log
            with dpg.child_window(height=200, border=True):
                log_title = dpg.add_text("Activity Log", color=self.secondary_color)
                dpg.bind_item_font(log_title, self.title_font)
                dpg.add_separator()
                dpg.add_spacer(height=3)
                
                with dpg.child_window(tag="log_container", border=False, height=130):
                    pass
            
            dpg.add_spacer(height=15)
            
            # Control buttons - Set initial state based on monitoring status
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=250)
                
                btn = dpg.add_button(label="Start Monitoring", tag="start_button",
                                   width=180, height=45, callback=self.start_monitoring,
                                   enabled=not was_running)
                dpg.bind_item_theme(btn, self.button_theme)
                dpg.bind_item_font(btn, self.button_font)
                
                dpg.add_spacer(width=20)
                
                btn2 = dpg.add_button(label="Stop Monitoring", tag="stop_button",
                                    width=180, height=45, callback=self.stop_monitoring,
                                    enabled=was_running)
                dpg.bind_item_theme(btn2, self.secondary_button_theme)
                dpg.bind_item_font(btn2, self.button_font)
        
        # Animate stats on load
        self.animate_stats()
        
        # Only auto-start on first load, not when returning from settings
        if self.auto_start and not was_running and self.username and self.token:
            dpg.set_frame_callback(10, self.start_monitoring)
    
    def animate_stats(self):
        """Animate stat numbers from current to target values"""
        # Set animation starting point to current values
        self.current_streak_animated = self.streak_data['current_streak']
        self.longest_streak_animated = self.streak_data['longest_streak']
        self.total_days_animated = self.streak_data['total_days']
        
        target_current = self.streak_data['current_streak']
        target_longest = self.streak_data['longest_streak']
        target_total = self.streak_data['total_days']
        
        def animate_step():
            speed = 0.15
            
            # Animate current streak
            if self.current_streak_animated < target_current:
                self.current_streak_animated += max(1, int((target_current - self.current_streak_animated) * speed))
                if self.current_streak_animated > target_current:
                    self.current_streak_animated = target_current
            
            # Animate longest streak
            if self.longest_streak_animated < target_longest:
                self.longest_streak_animated += max(1, int((target_longest - self.longest_streak_animated) * speed))
                if self.longest_streak_animated > target_longest:
                    self.longest_streak_animated = target_longest
            
            # Animate total days
            if self.total_days_animated < target_total:
                self.total_days_animated += max(1, int((target_total - self.total_days_animated) * speed))
                if self.total_days_animated > target_total:
                    self.total_days_animated = target_total
            
            # Update display
            if dpg.does_item_exist("current_streak_display"):
                dpg.set_value("current_streak_display", str(self.current_streak_animated))
            if dpg.does_item_exist("longest_streak_display"):
                dpg.set_value("longest_streak_display", str(self.longest_streak_animated))
            if dpg.does_item_exist("total_days_display"):
                dpg.set_value("total_days_display", str(self.total_days_animated))
            
            # Continue animation if not done
            if (self.current_streak_animated < target_current or 
                self.longest_streak_animated < target_longest or 
                self.total_days_animated < target_total):
                dpg.set_frame_callback(1, animate_step)
        
        animate_step()
    
    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        if dpg.does_item_exist("log_container"):
            dpg.add_text(log_message, parent="log_container", color=self.fg_color)
            
            # Auto-scroll to bottom
            children = dpg.get_item_children("log_container", 1)
            if children and len(children) > 10:
                dpg.delete_item(children[0])
    
    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.username = config.get('username', '')
                self.token = config.get('token', '')
                self.reminder_mode = config.get('reminder_mode', 'normal')
                self.auto_start = config.get('auto_start', True)
    
    def save_config(self):
        config = {
            'username': self.username,
            'token': self.token,
            'reminder_mode': self.reminder_mode,
            'auto_start': self.auto_start
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_streak_data(self):
        if self.streak_file.exists():
            with open(self.streak_file, 'r') as f:
                return json.load(f)
        return {
            'current_streak': 0,
            'longest_streak': 0,
            'last_commit_date': None,
            'total_days': 0,
            'commit_history': {}
        }
    
    def save_streak_data(self):
        with open(self.streak_file, 'w') as f:
            json.dump(self.streak_data, f, indent=2)
    
    def save_and_continue(self):
        username = dpg.get_value("username_input")
        token = dpg.get_value("token_input")
        
        if not username or not token:
            self.show_error_popup("Please fill in all fields!")
            return
        
        self.username = username
        self.token = token
        
        mode_value = dpg.get_value("reminder_mode_radio")
        self.reminder_mode = "normal" if "Normal" in mode_value else "strict"
        
        self.save_config()
        self.show_success_popup("Configuration saved!")
        dpg.set_frame_callback(30, self.show_main_view)
    
    def show_error_popup(self, message):
        with dpg.window(label="Error", modal=True, show=True, tag="error_popup", 
                       width=300, height=120, pos=[310, 300]):
            dpg.add_text(message, color=self.warning_color)
            dpg.add_spacer(height=20)
            btn = dpg.add_button(label="OK", width=260, 
                               callback=lambda: dpg.delete_item("error_popup"))
            dpg.bind_item_theme(btn, self.button_theme)
    
    def show_success_popup(self, message):
        with dpg.window(label="Success", modal=True, show=True, tag="success_popup", 
                       width=300, height=120, pos=[310, 300]):
            dpg.add_text(message, color=self.success_color)
            dpg.add_spacer(height=20)
            btn = dpg.add_button(label="OK", width=260, 
                               callback=lambda: dpg.delete_item("success_popup"))
            dpg.bind_item_theme(btn, self.secondary_button_theme)
    
    def check_github_activity(self):
        today = datetime.now().date().isoformat()
        
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f'https://api.github.com/users/{self.username}/events'
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            events = response.json()
            
            for event in events:
                event_date = event['created_at'][:10]
                if event_date == today:
                    if event['type'] in ['PushEvent', 'PullRequestEvent', 'IssuesEvent', 
                                        'CreateEvent', 'CommitCommentEvent']:
                        return True
            return False
            
        except requests.exceptions.RequestException as e:
            self.log(f"Error checking GitHub: {e}")
            return None
    
    def update_streak(self, has_activity):
        today = datetime.now().date().isoformat()
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        last_date = self.streak_data['last_commit_date']
        
        if has_activity:
            self.streak_data['commit_history'][today] = True
            
            if last_date == yesterday or last_date == today:
                if last_date != today:
                    self.streak_data['current_streak'] += 1
            elif last_date is None:
                self.streak_data['current_streak'] = 1
            else:
                self.streak_data['current_streak'] = 1
            
            self.streak_data['last_commit_date'] = today
            
            if self.streak_data['current_streak'] > self.streak_data['longest_streak']:
                self.streak_data['longest_streak'] = self.streak_data['current_streak']
            
            self.streak_data['total_days'] = len(self.streak_data['commit_history'])
            self.save_streak_data()
            return True
        else:
            if last_date == yesterday:
                return False
            elif last_date != today:
                self.streak_data['current_streak'] = 0
                self.save_streak_data()
            return False
    
    def send_notification(self, title, message):
        if NOTIFICATIONS_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name='GitHub Streak',
                    timeout=10
                )
            except:
                pass
    
    def get_reminder_message(self):
        streak = self.streak_data['current_streak']
        
        if self.reminder_mode == "strict":
            messages = {
                0: "🦉 Your streak is DEAD. Get coding NOW!",
                1: "🔥 1 day? Pathetic. Don't break it.",
                2: "💀 2 days? You're on thin ice.",
                3: "☠️ 3 days! One miss = STREAK OVER.",
                4: "💣 4 days! Don't you DARE miss today.",
                5: "⚡ 5 days! One lazy day = GONE.",
                6: "⏳ 6 days! Time is ticking...",
                7: "🛑 7 days! Stop procrastinating!",
                8: "🔥 8 days! Keep the fire alive!",
                9: "🚨 9 days! Last chance to commit!",
                10: "💪 10 days! But I'm watching...",
                11: "👀 11 days! Eyes on the keyboard.",
                12: "🦴 12 days! No bone idle days.",
                13: "🎱 13 days! Pocket this commit.",
                14: "🎯 14 days! Bullseye. Hit it again.",
                15: "🧨 15 days! Don't be a dud.",
                16: "⚖️ 16 days! Balance: one commit.",
                17: "🗝️ 17 days! Key to success: code.",
                18: "☔ 18 days! Commit or get rained on.",
                19: "🌱 19 days! Plant that commit.",
                20: "📌 20 days! Pin yourself to the desk.",
                21: "🧭 21 days! Don't lose direction.",
                22: "🪓 22 days! Chop that todo list.",
                23: "🌪️ 23 days! Whirlwind of code.",
                24: "🔐 24 days! Lock in the habit.",
                25: "🏹 25 days! Target: commit. Fire.",
                26: "🛡️ 26 days! Shield your streak.",
                27: "🎪 27 days! Center ring: your keyboard.",
                28: "🛠️ 28 days! Build the habit daily.",
                29: "⛓️ 29 days! Chain another link.",
                30: "🕳️ 30 days! Don't fall in the gap.",
                31: "🌋 31 days! Molten-hot streak.",
                32: "🚂 32 days! Full steam ahead.",
                33: "🎲 33 days! No gambles, just commits.",
                34: "🧱 34 days! Brick by brick.",
                35: "🚧 35 days! Road work ahead: code.",
                36: "🐜 36 days! Work ethic of an ant.",
                37: "🔮 37 days! Future you is grateful.",
                38: "🪜 38 days! Climbing the ladder.",
                39: "🧯 39 days! Put out procrastination.",
                40: "⏰ 40 days! Alarm! Time to code.",
                41: "🎨 41 days! Masterpiece in progress.",
                42: "🛋️ 42 days! Get off the couch.",
                43: "🕸️ 43 days! Untangle with code.",
                44: "🍳 44 days! Don't let it fry.",
                45: "🪤 45 days! Avoid the trap of 'later'.",
                46: "🎣 46 days! Hook another commit.",
                47: "🚀 47 days! Ignition sequence on.",
                48: "🧿 48 days! Evil eye on laziness.",
                49: "🪨 49 days! Solid as a rock.",
                50: "🥊 50 days! Punch through blockers.",
                51: "🦾 51 days! You are augmented.",
                52: "🖇️ 52 days! Clip tasks together.",
                53: "🎼 53 days! Compose your commits.",
                54: "🩹 54 days! Heal broken habits.",
                55: "🪖 55 days! Helmets on, code.",
                56: "💎 56 days! Hard, precious streak.",
                57: "🕶️ 57 days! Cool shades, cooler code.",
                58: "🏮 58 days! Light the path.",
                59: "🪕 59 days! Strum that keyboard.",
                60: "🗿 60 days! Monumental streak.",
                61: "🧬 61 days! It's in your DNA now.",
                62: "🪶 62 days! Light, consistent touch.",
                63: "🦠 63 days! Infectiously productive.",
                64: "🔋 64 days! Fully charged.",
                65: "🧨 65 days! Another spark needed.",
                66: "🎚️ 66 days! Set the dial to commit.",
                67: "🦺 67 days! Safety first: commit.",
                68: "🏍️ 68 days! Ride the streak.",
                69: "🛢️ 69 days! Fuel up with code.",
                70: "🧿 70 days! Nazar on distractions.",
                71: "🎪 71 days! Still in the ring.",
                72: "🕰️ 72 days! Ticking masterpiece.",
                73: "🎡 73 days! Commit wheel spinning.",
                74: "📡 74 days! Signal: code received.",
                75: "🏋️ 75 days! Heavy lifting daily.",
                76: "🦴 76 days! No skeleton days.",
                77: "🎳 77 days! Strike! Every day.",
                78: "🪑 78 days! Stay in the chair.",
                79: "🍯 79 days! Sweet, sticky habit.",
                80: "🧭 80 days! Still navigating.",
                81: "🪓 81 days! Chop more tasks.",
                82: "🪢 82 days! Knot another day.",
                83: "🔭 83 days! Focus on the goal.",
                84: "🪟 84 days! Clear view to success.",
                85: "🪜 85 days! Higher and higher.",
                86: "🧱 86 days! Wall of discipline.",
                87: "🪕 87 days! Keep the rhythm.",
                88: "🛒 88 days! Add commit to cart.",
                89: "🪨 89 days! Unbreakable now.",
                90: "🥇 90 days! Gold medal habit.",
                91: "🧿 91 days! Warding off slumps.",
                92: "🛞 92 days! Wheels turning daily.",
                93: "🪜 93 days! To the top.",
                94: "🩻 94 days! X-ray shows commitment.",
                95: "🪡 95 days! Stitch it together.",
                96: "🧷 96 days! Fasten your focus.",
                97: "🪚 97 days! Saw through problems.",
                98: "🪣 98 days! Bucket of commits.",
                99: "🪤 99 days! Tread carefully.",
                100: "💯 100 days! LEGEND status.",
                101: "🚨 101 days! Don't crash now.",
                102: "🦅 102 days! Eagle-eyed focus.",
                103: "🎯 103 days! Still hitting marks.",
                104: "🛸 104 days! Out of this world.",
                105: "🥷 105 days! Stealthy consistency.",
                106: "🎹 106 days! Keyed in.",
                107: "🧩 107 days! Pieces fitting.",
                108: "🛡️ 108 days! Still shielding.",
                109: "🌲 109 days! Deep roots now.",
                110: "🦉 110 days! Wise commitment.",
                111: "⚔️ 111 days! Battle distraction.",
                112: "🧪 112 days! Experiment daily.",
                113: "🪄 113 days! Magic of habit.",
                114: "🎪 114 days! Three-ring circus of code.",
                115: "🏺 115 days! Ancient artifact streak.",
                116: "🦴 116 days! Backbone of steel.",
                117: "🛷 117 days! Sledding downhill.",
                118: "🪗 118 days! Accordion of accomplishments.",
                119: "🧲 119 days! Pulled to keyboard.",
                120: "🧿 120 days! Eye on the prize.",
                121: "🧵 121 days! Thread of discipline.",
                122: "🪕 122 days! Bluegrass coder.",
                123: "🛎️ 123 days! Bell rings: code.",
                124: "🪆 124 days! Nested successes.",
                125: "🧨 125 days! Still explosive.",
                126: "🪑 126 days! Chair is home.",
                127: "🪜 127 days! Ladder to the stars.",
                128: "🛡️ 128 days! Impenetrable focus.",
                129: "🎖️ 129 days! General of GitHub.",
                130: "🧿 130 days! Unblinking focus.",
                131: "🪨 131 days! Bedrock habits.",
                132: "🧱 132 days! Fortress of commits.",
                133: "🪓 133 days! Still chopping.",
                134: "🎪 134 days! Main attraction: you.",
                135: "🦾 135 days! Machine-like.",
                136: "🕰️ 136 days! Grandfather clock of code.",
                137: "🎣 137 days! Still fishing for wins.",
                138: "🛋️ 138 days! Sofa? What sofa?",
                139: "🧯 139 days! Fire extinguisher for excuses.",
                140: "🎨 140 days! Canvas of commits.",
                141: "🪤 141 days! Trap set for failure.",
                142: "🛢️ 142 days! Oil of productivity.",
                143: "🧬 143 days! Genetically coded to commit.",
                144: "🪟 144 days! Window to your soul: green squares.",
                145: "🪜 145 days! Sky's the limit.",
                146: "🎚️ 146 days! Levels maxed.",
                147: "🦺 147 days! High-visibility success.",
                148: "🎪 148 days! Greatest show on earth.",
                149: "🛞 149 days! All-terrain coder.",
                150: "🏆 150 days! Trophy unlocked.",
                151: "🧿 151 days! The eye sees all.",
                152: "🪕 152 days! Jam session daily.",
                153: "🛡️ 153 days! Still defending.",
                154: "🧱 154 days! Another brick.",
                155: "🪨 155 days! Diamond hands of code.",
                156: "🪓 156 days! Lumberjack of logic.",
                157: "🎪 157 days! Center stage.",
                158: "🦾 158 days! Upgraded human.",
                159: "🕰️ 159 days! Timeless effort.",
                160: "🎣 160 days! Big catch.",
                161: "🛋️ 161 days! Discipline is comfy.",
                162: "🧯 162 days! No fires, just code.",
                163: "🎨 163 days! Artisan.",
                164: "🪤 164 days! Failure avoided.",
                165: "🛢️ 165 days! Well-oiled machine.",
                166: "🧬 166 days! Prime specimen.",
                167: "🪟 167 days! Clear future.",
                168: "🪜 168 days! Step up.",
                169: "🎚️ 169 days! Perfect settings.",
                170: "🦺 170 days! Safe from regret.",
                171: "🎪 171 days! Star performer.",
                172: "🛞 172 days! Rolling smooth.",
                173: "🏆 173 days! Champion's composure.",
                174: "🧿 174 days! Focus amulet.",
                175: "🪕 175 days! Symphony of commits.",
                176: "🛡️ 176 days! Shield wall holds.",
                177: "🧱 177 days! Pyramid of progress.",
                178: "🪨 178 days! Gibraltar of grit.",
                179: "🪓 179 days! Forest cleared.",
                180: "🥑 180 days! Perfectly ripe streak.",
                181: "🧿 181 days! Warding off decay.",
                182: "🪕 182 days! Folklore of focus.",
                183: "🛡️ 183 days! Knighted by commits.",
                184: "🧱 184 days! Citadel of code.",
                185: "🪨 185 days! Sedimentary willpower.",
                186: "🪓 186 days! Honed edge.",
                187: "🎪 187 days! Headliner.",
                188: "🦾 188 days! Bionic dedication.",
                189: "🕰️ 189 days! Antique discipline.",
                190: "🎣 190 days! Deep sea diver.",
                191: "🛋️ 191 days! Throne of commits.",
                192: "🧯 192 days! Prevention expert.",
                193: "🎨 193 days! Renaissance coder.",
                194: "🪤 194 days! Mouse trap mind.",
                195: "🛢️ 195 days! Refined habits.",
                196: "🧬 196 days! Evolved.",
                197: "🪟 197 days! Panoramic view.",
                198: "🪜 198 days! Almost there.",
                199: "🎚️ 199 days! Master levels.",
                200: "🚀 200 days! Interstellar streak.",
                201: "🧿 201 days! All-seeing eye.",
                202: "🪕 202 days! Heartstring habit.",
                203: "🛡️ 203 days! Legendary defense.",
                204: "🧱 204 days! Great wall.",
                205: "🪨 205 days! Obsidian focus.",
                206: "🪓 206 days! Lumberjack legend.",
                207: "🎪 207 days! Ringmaster.",
                208: "🦾 208 days! Cybernetic will.",
                209: "🕰️ 209 days! Heirloom habit.",
                210: "🎣 210 days! Legendary angler.",
                211: "🛋️ 211 days! Pillar of comfort.",
                212: "🧯 212 days! Fireproof streak.",
                213: "🎨 213 days! Old master.",
                214: "🪤 214 days! Perfected trap.",
                215: "🛢️ 215 days! Crude commitment.",
                216: "🧬 216 days! Perfect clone.",
                217: "🪟 217 days! Bay window view.",
                218: "🪜 218 days! Ladder to heaven.",
                219: "🎚️ 219 days! Mix master.",
                220: "🦺 220 days! Hazard suit on.",
                221: "🎪 221 days! Eternal show.",
                222: "🛞 222 days! Off-road coder.",
                223: "🏆 223 days! Trophy case full.",
                224: "🧿 224 days! Ancient talisman.",
                225: "🪕 225 days! Platinum record.",
                226: "🛡️ 226 days! Hero's shield.",
                227: "🧱 227 days! Marble monument.",
                228: "🪨 228 days! Meteorite will.",
                229: "🪓 229 days! Paul Bunyan status.",
                230: "🎩 230 days! Hat trick daily.",
                231: "🧿 231 days! Third eye open.",
                232: "🪕 232 days! Bluegrass virtuoso.",
                233: "🛡️ 233 days! Fort Knox focus.",
                234: "🧱 234 days! Empire State.",
                235: "🪨 235 days! Foundation stone.",
                236: "🪓 236 days! Clear-cutting goals.",
                237: "🎪 237 days! Greatest of all time.",
                238: "🦾 238 days! Titanium tendons.",
                239: "🕰️ 239 days! Sundial of success.",
                240: "🎣 240 days! Whale of a streak.",
                241: "🛋️ 241 days! Couch potato? Never.",
                242: "🧯 242 days! Extinguished doubts.",
                243: "🎨 243 days! Gallery worthy.",
                244: "🪤 244 days! Chess master move.",
                245: "🛢️ 245 days! Pipeline of progress.",
                246: "🧬 246 days! Double helix habit.",
                247: "🪟 247 days! Stained glass discipline.",
                248: "🪜 248 days! Reaching zenith.",
                249: "🎚️ 249 days! Soundboard of success.",
                250: "🥊 250 days! Undisputed champ.",
                251: "🧿 251 days! Mystical focus.",
                252: "🪕 252 days! Concert hall ready.",
                253: "🛡️ 253 days! Spartan shield.",
                254: "🧱 254 days! Colosseum of commits.",
                255: "🪨 255 days! Mountain range.",
                256: "🪓 256 days! 2^8 days of power.",
                257: "🎪 257 days! P.T. Barnum of code.",
                258: "🦾 258 days! Full exoskeleton.",
                259: "🕰️ 259 days! Clockmaker's pride.",
                260: "🎣 260 days! Kraken caught.",
                261: "🛋️ 261 days! La-Z-Boy? More like Go-Boy.",
                262: "🧯 262 days! Cold fire of focus.",
                263: "🎨 263 days! Sistine Chapel ceiling.",
                264: "🪤 264 days! Rube Goldberg of wins.",
                265: "🛢️ 265 days! Strategic reserve.",
                266: "🧬 266 days! Genome sequenced.",
                267: "🪟 267 days! Observatory view.",
                268: "🪜 268 days! To the moon.",
                269: "🎚️ 269 days! Producer level.",
                270: "🥑 270 days! Avocado toast of success.",
                271: "🧿 271 days! Eye of Providence.",
                272: "🪕 272 days! Grammy incoming.",
                273: "🛡️ 273 days! Aegis of Athena.",
                274: "🧱 274 days! Great Pyramid.",
                275: "🪨 275 days! Stonehenge of streaks.",
                276: "🪓 276 days! Valhalla's lumberjack.",
                277: "🎪 277 days! Sold out shows.",
                278: "🦾 278 days! Deus Ex machina.",
                279: "🕰️ 279 days! Time lord status.",
                280: "🎣 280 days! Poseidon's trident.",
                281: "🛋️ 281 days! Throne of Games.",
                282: "🧯 282 days! Dragon's breath focus.",
                283: "🎨 283 days! Van Gogh's ear for code.",
                284: "🪤 284 days! Inception-level trap.",
                285: "🛢️ 285 days! Texas tea of tenacity.",
                286: "🧬 286 days! Jurassic Park amber.",
                287: "🪟 287 days! Portal to greatness.",
                288: "🪜 288 days! Stairway to heaven.",
                289: "🎚️ 289 days! 17² days of glory.",
                290: "🦺 290 days! Hazmat suit of habit.",
                291: "🎪 291 days! Big top legacy.",
                292: "🛞 292 days! Around the world.",
                293: "🏆 293 days! Hall of fame.",
                294: "🧿 294 days! Eye of Sauron.",
                295: "🪕 295 days! Stradivarius of streaks.",
                296: "🛡️ 296 days! Captain America's shield.",
                297: "🧱 297 days! Hadrian's Wall.",
                298: "🪨 298 days! Everest base camp.",
                299: "🪓 299 days! Mjolnir's swing.",
                300: "👑 300 days! Crown of Commitment.",
                301: "🧿 301 days! Palantír vision.",
                302: "🪕 302 days! Woodstock revival.",
                303: "🛡️ 303 days! Trojan defense.",
                304: "🧱 304 days! Machu Picchu.",
                305: "🪨 305 days! Grand Canyon deep.",
                306: "🪓 306 days! Babe the Blue Ox.",
                307: "🎪 307 days! Cirque du Soleil.",
                308: "🦾 308 days! Iron Man suit.",
                309: "🕰️ 309 days! Doomsday Clock (green).",
                310: "🎣 310 days! Ahab's white whale.",
                311: "🛋️ 311 days! Freud's couch of coding.",
                312: "🧯 312 days! Phoenix ashes.",
                313: "🎨 313 days! Bob Ross' happy trees.",
                314: "🪤 314 days! π-th perfection.",
                315: "🛢️ 315 days! 21² - 6² days of fuel.",
                316: "🧬 316 days! CRISPR-precise.",
                317: "🪟 317 days! Rose window focus.",
                318: "🪜 318 days! Tower of Babel.",
                319: "🎚️ 319 days! Studio master.",
                320: "🥊 320 days! Creed-level grit.",
                321: "🧿 321 days! Horus' right eye.",
                322: "🪕 322 days! Skynet's lullaby.",
                323: "🛡️ 323 days! Spartan-II program.",
                324: "🧱 324 days! 18² days of bricks.",
                325: "🪨 325 days! Petra carved.",
                326: "🪓 326 days! Gimli's axe.",
                327: "🎪 327 days! Barnum & Bailey.",
                328: "🦾 328 days! Major Motoko Kusanagi.",
                329: "🕰️ 329 days! Interstellar's clock.",
                330: "🎣 330 days! Old Man and the Sea.",
                331: "🛋️ 331 days! Sheldon's spot.",
                332: "🧯 332 days! Great Chicago Fireproof.",
                333: "🎨 333 days! Demonic perfection.",
                334: "🪤 334 days! Jigsaw's game.",
                335: "🛢️ 335 days! OPEC's envy.",
                336: "🧬 336 days! Darwin's finch.",
                337: "🪟 337 days! Overlook Hotel window.",
                338: "🪜 338 days! Jacob's ladder.",
                339: "🎚️ 339 days! Abbey Road mixing.",
                340: "🥑 340 days! Guacamole of greatness.",
                341: "🧿 341 days! Argus Panoptes.",
                342: "🪕 342 days! Deliverance duel.",
                343: "🛡️ 343 days! 7³ days defended.",
                344: "🧱 344 days! Great Wall extended.",
                345: "🪨 345 days! Uluru solid.",
                346: "🪓 346 days! Paulownia cutter.",
                347: "🎪 347 days! Ringling Bros.",
                348: "🦾 348 days! Ghost in the Shell.",
                349: "🕰️ 349 days! Ticking to triumph.",
                350: "🏔️ 350 days! Summit in sight.",
                351: "🧿 351 days! Lidless eye.",
                352: "🪕 352 days! Battle of the bands.",
                353: "🛡️ 353 days! Knights of the Round Table.",
                354: "🧱 354 days! Lunar base walls.",
                355: "🪨 355 days! K2 conquered.",
                356: "🪓 356 days! Year of the axe.",
                357: "🎪 357 days! Final bow approaching.",
                358: "🦾 358 days! Full conversion cyborg.",
                359: "🕰️ 359 days! One tick left.",
                360: "⛰️ 360 days! Everest peak.",
                361: "🧿 361 days! 19² days of sight.",
                362: "🪕 362 days! Encore! Encore!",
                363: "🛡️ 363 days! Citadel's last stand.",
                364: "🧱 364 days! One brick remains.",
                365: "🚨🏆🌌 365 days! ABSOLUTE VICTORY. YOU ARE A GITHUB DEITY. THE STREAK IS ETERNAL."
            }
        else:
            messages = {
                7: "🌟 **Week 1 Complete!** Your streak has a heartbeat! Keep it pumping!",
                14: "📚 **Week 2!** The habit is forming. You're building a solid foundation!",
                21: "⚡ **Week 3!** Three weeks strong! Consistency is becoming your superpower.",
                28: "🏆 **Month 1!** A FULL MONTH of commits! You're officially a streak runner!",
                35: "🚀 **Week 5!** Blasting past the one-month mark! Momentum is real!",
                42: "🛠️ **Week 6!** You're not just committing code, you're building discipline.",
                49: "🔥 **Week 7!** Almost to the big 50! Your graph is looking beautiful!",
                56: "💪 **8 Weeks!** Two months of dedication. Think how far you've come!",
                63: "🎯 **Week 9!** Precision focus! You're hitting targets week after week.",
                70: "🌈 **Week 10!** Double digits! Your streak is a rainbow of productivity.",
                77: "🧠 **Week 11!** This isn't just habit anymore—it's part of your identity.",
                84: "⚓ **Week 12!** Anchored in excellence. Three months of solid work!",
                91: "🚂 **Week 13!** Full steam ahead! Nothing can stop this train now.",
                98: "🎪 **Week 14!** The show must go on—and you're the star performer!",
                105: "🏔️ **Week 15!** You've climbed so high. The view is amazing, isn't it?",
                112: "🔐 **Week 16!** You've unlocked a new level of professional consistency.",
                119: "🛡️ **Week 17!** Protected against procrastination. Your will is strong!",
                126: "🎨 **Week 18!** Your contribution graph is a masterpiece in the making.",
                133: "🌌 **Week 19!** You're not just coding; you're creating constellations of commits.",
                140: "⚖️ **Week 20!** Perfect balance of discipline and creativity.",
                147: "🏰 **Week 21!** You've built a fortress of focus. Impenetrable!",
                154: "🌀 **Week 22!** You're in the flow state vortex now.",
                161: "🎭 **Week 23!** The discipline is so ingrained, it feels effortless.",
                168: "⏳ **Week 24!** Six months! Half a year of unstoppable progress!",
                175: "🌋 **Week 25!** Molten hot productivity erupting daily!",
                182: "🧭 **Week 26!** Your internal compass always points to 'commit'.",
                189: "🎲 **Week 27!** You've beaten the odds of distraction.",
                196: "🪐 **Week 28!** Your streak is on another planetary level!",
                203: "⚙️ **Week 29!** Well-oiled machine. Perfectly tuned.",
                210: "🏹 **Week 30!** Bullseye after bullseye. Unmatched accuracy.",
                217: "🪶 **Week 31!** Light as a feather, strong as steel.",
                224: "🔮 **Week 32!** Future you is so grateful for this.",
                231: "🧿 **Week 33!** The evil eye on all distractions.",
                238: "🎻 **Week 34!** Playing the symphony of consistency perfectly.",
                245: "🏹 **Week 35!** Every arrow hits its mark.",
                252: "🌲 **Week 36!** Deep roots now. Unshakeable.",
                259: "🦅 **Week 37!** Eagle-eyed focus from on high.",
                266: "⚔️ **Week 38!** Battle-tested and victorious.",
                273: "🕰️ **Week 39!** Timeless discipline.",
                280: "🧩 **Week 40!** Every piece fitting perfectly.",
                287: "🏺 **Week 41!** Ancient artifact-level commitment.",
                294: "🎪 **Week 42!** Center ring, spotlight on you.",
                301: "🛸 **Week 43!** Out of this world consistency.",
                308: "🪨 **Week 44!** Solid as bedrock.",
                315: "🌀 **Week 45!** In the productivity tornado.",
                322: "🎭 **Week 46!** The show never stops.",
                329: "🌅 **Week 47!** Every sunrise brings another commit.",
                336: "🏆 **Week 48!** Championship season, every week.",
                343: "🎰 **Week 49!** The house always wins—and you're the house.",
                350: "🛡️ **Week 50!** Fifty weeks! What an incredible journey!",
                357: "👑 **Week 51!** Royal levels of discipline.",
                364: "🎊 **Week 52!** ONE. FULL. YEAR. Absolute legend!",
            }
        
        for threshold in sorted(messages.keys(), reverse=True):
            if streak >= threshold:
                return messages[threshold]
        return messages[0]
    
    def manual_check(self):
        self.log("Running manual check...")
        
        today = datetime.now().date().isoformat()
        
        if self.streak_data['commit_history'].get(today):
            self.log("✓ Already committed today!")
            if dpg.does_item_exist("status_message"):
                dpg.set_value("status_message", "Streak safe for today!")
                dpg.bind_item_theme("status_message", self.success_theme)
                dpg.bind_item_font("status_message", self.title_font)
            return
        
        has_activity = self.check_github_activity()
        
        if has_activity is None:
            self.log("⚠️ Could not check GitHub")
            if dpg.does_item_exist("status_message"):
                dpg.set_value("status_message", "⚠️ Connection error")
                dpg.bind_item_theme("status_message", self.warning_theme)
            return
        
        if has_activity:
            self.update_streak(True)
            self.log(f"✓ Activity detected! Streak: {self.streak_data['current_streak']} days")
            if dpg.does_item_exist("status_message"):
                dpg.set_value("status_message", f"✓ Streak: {self.streak_data['current_streak']} days 🔥")
                dpg.bind_item_theme("status_message", self.success_theme)
            self.send_notification("GitHub Streak", 
                                  f"Activity detected! {self.streak_data['current_streak']} days 🔥")
        else:
            reminder = self.get_reminder_message()
            self.log(f"⚠️ NO ACTIVITY TODAY - {reminder}")
            if dpg.does_item_exist("status_message"):
                dpg.set_value("status_message", "⚠️ No activity today!")
                dpg.bind_item_font("status_message", self.title_font)
                dpg.bind_item_theme("status_message", self.warning_theme)
            self.send_notification("GitHub Streak Reminder", reminder)
        
        self.update_stats_display()
    
    def update_stats_display(self):
        """Update stats with animation"""
        self.animate_stats()
        
        if dpg.does_item_exist("last_commit_text"):
            last_commit = self.streak_data.get('last_commit_date', 'Never')
            dpg.set_value("last_commit_text", f"Last Commit: {last_commit}")
            
    
    def monitoring_loop(self):
        check_times = ["09:00", "14:00", "20:00"]
        last_check_date = None
        
        while self.is_running:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.date().isoformat()
            
            if current_date != last_check_date:
                last_check_date = current_date
                
                if current_time in check_times:
                    self.manual_check()
                    time.sleep(65)
            
            time.sleep(30)
    
    def start_monitoring(self):
        if self.is_running:
            return
        
        self.is_running = True
        
        if dpg.does_item_exist("start_button"):
            dpg.configure_item("start_button", enabled=False)
        if dpg.does_item_exist("stop_button"):
            dpg.configure_item("stop_button", enabled=True)
        
        self.log("Monitoring started")
        self.log("Checks at: 9:00 AM, 2:00 PM, 8:00 PM")
        
        self.check_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.check_thread.start()
        
        threading.Thread(target=self.manual_check, daemon=True).start()
    
    def stop_monitoring(self):
        self.is_running = False
        
        if dpg.does_item_exist("start_button"):
            dpg.configure_item("start_button", enabled=True)
        if dpg.does_item_exist("stop_button"):
            dpg.configure_item("stop_button", enabled=False)
        
        self.log("⏸ Monitoring stopped")
    
    def run(self):
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        
        self.is_running = False
        dpg.destroy_context()

def main():
    app = GitHubStreakGUI()
    app.run()

if __name__ == "__main__":
    main()