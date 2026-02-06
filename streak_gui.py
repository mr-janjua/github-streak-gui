#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import sys
import os

try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

class GitHubStreakGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Streak Tracker")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.config_dir = Path.home() / ".github_streak"
        self.config_file = self.config_dir / "config.json"
        self.streak_file = self.config_dir / "streak.json"
        self.config_dir.mkdir(exist_ok=True)
        
        self.username = tk.StringVar()
        self.token = tk.StringVar()
        self.reminder_mode = tk.StringVar(value="normal")
        self.auto_start = tk.BooleanVar(value=True)
        
        self.streak_data = self.load_streak_data()
        self.is_running = False
        self.check_thread = None
        
        self.setup_ui()
        self.load_config()
        
        if self.username.get() and self.token.get():
            self.show_main_view()
        else:
            self.show_setup_view()
    
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Color palette
        bg_color = "#1e1e2e"      # Dark background
        fg_color = "#dbdbdb"      # Light foreground
        accent_color = "#ff6b6b"   # Red accent
        secondary_color = "#4ecdc4" # Teal accent
        
        # Configure root window
        self.root.configure(bg=bg_color)
        
        # Configure ttk styles
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background=accent_color, foreground=fg_color)
        style.configure('TLabelframe', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
        style.configure('TEntry', fieldbackground="#2a2a3e", foreground=fg_color)
        style.configure('TRadiobutton', background=bg_color, foreground=fg_color)
        
        # Custom label styles
        style.configure('Title.TLabel', font=('Segoe UI', 28, 'bold'), 
                       background=bg_color, foreground=accent_color)
        style.configure('Stat.TLabel', font=('Segoe UI', 40, 'bold'), 
                       background=bg_color, foreground=secondary_color)
        style.configure('StatLabel.TLabel', font=('Segoe UI', 13), 
                       background=bg_color, foreground=fg_color)
        style.configure('Success.TLabel', foreground='#2ecc71', font=('Segoe UI', 14, 'bold'),
                       background=bg_color)
        style.configure('Warning.TLabel', foreground='#e74c3c', font=('Segoe UI', 14, 'bold'),
                       background=bg_color)
        
        # Button styling
        style.map('TButton',
                 background=[('active', '#ff5252'), ('pressed', '#ff3333')],
                 foreground=[('active', '#ffffff')])
        
        # Stats frame styling with colored border
        style.configure('Stats.TLabelframe', background=bg_color, foreground=accent_color,
                       bordercolor=secondary_color, borderwidth=2, relief='solid')
        style.configure('Stats.TLabelframe.Label', background=bg_color, foreground=accent_color,
                       font=('Segoe UI', 12, 'bold'))
        
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
    
    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def show_setup_view(self):
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="🔥 GitHub Streak Tracker", 
                 style='Title.TLabel').grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Label(self.main_frame, text="Setup", 
                 font=('Arial', 16, 'bold')).grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Label(self.main_frame, text="GitHub Username:").grid(row=2, column=0, sticky=tk.W, pady=5)
        username_entry = ttk.Entry(self.main_frame, textvariable=self.username, width=40)
        username_entry.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(self.main_frame, text="Personal Access Token:").grid(row=3, column=0, sticky=tk.W, pady=5)
        token_entry = ttk.Entry(self.main_frame, textvariable=self.token, width=40, show="*")
        token_entry.grid(row=3, column=1, pady=5, padx=5)
        
        ttk.Label(self.main_frame, text="Get token from: https://github.com/settings/tokens",
                 foreground='blue', cursor='hand2').grid(row=4, column=0, columnspan=2, pady=5)
        
        ttk.Label(self.main_frame, text="Reminder Mode:").grid(row=5, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(self.main_frame)
        mode_frame.grid(row=5, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(mode_frame, text="Normal (Friendly)", variable=self.reminder_mode, 
                       value="normal").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Strict (Duolingo Mode)", variable=self.reminder_mode, 
                       value="strict").pack(side=tk.LEFT, padx=5)
        
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=30)
        
        ttk.Button(button_frame, text="Save & Continue", 
                  command=self.save_and_continue).pack(side=tk.LEFT, padx=5)
        
        if self.config_file.exists():
            ttk.Button(button_frame, text="Back to Dashboard", 
                      command=self.show_main_view).pack(side=tk.LEFT, padx=5)
    
    def show_main_view(self):
        self.clear_frame()
        
        header = ttk.Frame(self.main_frame)
        header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(header, text="🔥 GitHub Streak Tracker", 
                 style='Title.TLabel').pack(side=tk.LEFT)
        
        ttk.Button(header, text="⚙️ Settings", 
                  command=self.show_setup_view).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header, text="📊 Check Now", 
                  command=self.manual_check).pack(side=tk.RIGHT, padx=5)
        
        stats_frame = ttk.LabelFrame(self.main_frame, text="Your Stats", padding="20", style='Stats.TLabelframe')
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        
        current_frame = ttk.Frame(stats_frame)
        current_frame.grid(row=0, column=0, padx=20, pady=10)
        ttk.Label(current_frame, text="Current Streak", style='StatLabel.TLabel').pack()
        self.current_streak_label = ttk.Label(current_frame, 
                                             text=str(self.streak_data['current_streak']), 
                                             style='Stat.TLabel', foreground='#e74c3c')
        self.current_streak_label.pack()
        ttk.Label(current_frame, text="days 🔥", font=('Arial', 12)).pack()
        
        longest_frame = ttk.Frame(stats_frame)
        longest_frame.grid(row=0, column=1, padx=20, pady=10)
        ttk.Label(longest_frame, text="Longest Streak", style='StatLabel.TLabel').pack()
        ttk.Label(longest_frame, text=str(self.streak_data['longest_streak']), 
                 style='Stat.TLabel', foreground='#f39c12').pack()
        ttk.Label(longest_frame, text="days 🏆", font=('Arial', 12)).pack()
        
        total_frame = ttk.Frame(stats_frame)
        total_frame.grid(row=0, column=2, padx=20, pady=10)
        ttk.Label(total_frame, text="Total Days", style='StatLabel.TLabel').pack()
        ttk.Label(total_frame, text=str(self.streak_data['total_days']), 
                 style='Stat.TLabel', foreground='#3498db').pack()
        ttk.Label(total_frame, text="days 💎", font=('Arial', 12)).pack()
        
        info_frame = ttk.Frame(stats_frame)
        info_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        last_commit = self.streak_data.get('last_commit_date', 'Never')
        ttk.Label(info_frame, text=f"Last Commit: {last_commit}").pack()
        ttk.Label(info_frame, text=f"Mode: {self.reminder_mode.get().upper()}").pack()
        ttk.Label(info_frame, text=f"Username: {self.username.get()}").pack()
        
        self.status_label = ttk.Label(stats_frame, text="", font=('Arial', 14, 'bold'))
        self.status_label.grid(row=2, column=0, columnspan=3, pady=10)
        
        log_frame = ttk.LabelFrame(self.main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70, 
                                                  state='disabled', wrap=tk.WORD,
                                                  bg="#2a2a3e", fg="#e0e0e0",
                                                  font=('Courier', 10),
                                                  insertbackground="#e0e0e0")
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=3, column=0, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="▶ Start Monitoring", 
                                       command=self.start_monitoring, width=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="⏸ Stop Monitoring", 
                                      command=self.stop_monitoring, width=20, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.update_stats_display()
        
        if self.auto_start.get():
            self.root.after(1000, self.start_monitoring)
    
    def log(self, message):
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
    
    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.username.set(config.get('username', ''))
                self.token.set(config.get('token', ''))
                self.reminder_mode.set(config.get('reminder_mode', 'normal'))
                self.auto_start.set(config.get('auto_start', True))
    
    def save_config(self):
        config = {
            'username': self.username.get(),
            'token': self.token.get(),
            'reminder_mode': self.reminder_mode.get(),
            'auto_start': self.auto_start.get()
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
        if not self.username.get() or not self.token.get():
            messagebox.showerror("Error", "Please fill in all fields!")
            return
        
        self.save_config()
        messagebox.showinfo("Success", "Configuration saved!")
        self.show_main_view()
    
    def check_github_activity(self):
        today = datetime.now().date().isoformat()
        
        headers = {
            'Authorization': f'token {self.token.get()}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f'https://api.github.com/users/{self.username.get()}/events'
        
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
        
        if self.reminder_mode.get() == "strict":
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
            self.status_label.configure(text="✓ Streak safe for today!", 
                                       foreground='#2ecc71')
            return
        
        has_activity = self.check_github_activity()
        
        if has_activity is None:
            self.log("⚠️ Could not check GitHub")
            self.status_label.configure(text="⚠️ Connection error", 
                                       foreground='#e74c3c')
            return
        
        if has_activity:
            self.update_streak(True)
            self.log(f"✓ Activity detected! Streak: {self.streak_data['current_streak']} days")
            self.status_label.configure(text=f"✓ Streak: {self.streak_data['current_streak']} days 🔥", 
                                       foreground='#2ecc71')
            self.send_notification("GitHub Streak", 
                                  f"Activity detected! {self.streak_data['current_streak']} days 🔥")
        else:
            reminder = self.get_reminder_message()
            self.log(f"⚠️ NO ACTIVITY TODAY - {reminder}")
            self.status_label.configure(text="⚠️ No activity today!", 
                                       foreground='#e74c3c')
            self.send_notification("GitHub Streak Reminder", reminder)
        
        self.update_stats_display()
    
    def update_stats_display(self):
        if hasattr(self, 'current_streak_label'):
            self.current_streak_label.configure(text=str(self.streak_data['current_streak']))
    
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
                    self.root.after(0, self.manual_check)
                    time.sleep(65)
            
            time.sleep(30)
    
    def start_monitoring(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        
        self.log("🔥 Monitoring started")
        self.log("Checks at: 9:00 AM, 2:00 PM, 8:00 PM")
        
        self.check_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.check_thread.start()
        
        self.manual_check()
    
    def stop_monitoring(self):
        self.is_running = False
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.log("⏸ Monitoring stopped")
    
    def on_closing(self):
        self.is_running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = GitHubStreakGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
