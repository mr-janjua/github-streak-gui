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
        dpg.create_viewport(title="🔥 GitHub Streak Tracker", width=920, height=720)
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
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.accent_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (220, 70, 70, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (180, 50, 50, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 12, category=dpg.mvThemeCat_Core)
        
        # Secondary button theme - Darker
        with dpg.theme() as self.secondary_button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.secondary_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (65, 175, 168, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (40, 135, 128, 255), category=dpg.mvThemeCat_Core)
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
            title_text = dpg.add_text("🔥 GitHub Streak Tracker", 
                        color=self.accent_color)
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
                header_text = dpg.add_text("GitHub Streak Tracker", color=self.accent_color)
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
                5: "⚡ 5 days! One lazy day = GONE.",
                10: "💪 10 days! But I'm watching...",
                20: "🎯 20 DAYS! Miss = back to zero.",
                30: "👑 30 DAYS! Don't you DARE break this.",
                50: "🚀 50 DAYS! Keep going or regret FOREVER.",
                100: "🏆 100 DAYS! You're unstoppable!"
            }
        else:
            messages = {
                0: "💚 Start your GitHub streak today!",
                1: "🌱 Keep it going!",
                5: "🔥 5 days! Building momentum!",
                10: "⭐ 10 days! You're on fire!",
                20: "🎉 20 days! Great habit!",
                30: "💎 30 days! Legend status!",
                50: "🚀 50 DAYS! Incredible!",
                100: "👑 100 DAYS! Unstoppable!"
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