import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import threading
import time
import json
from datetime import datetime
from index import StealthTrafficGenerator
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class EnhancedTrafficGeneratorGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("GhostTraffic made with love by @mrr_blaq_dev")
        self.master.geometry("1200x800")
        self.master.resizable(True, True)
        
        # Apply modern styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.colors = {
            'primary': '#2196F3',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'background': '#f5f5f5',
            'surface': '#ffffff'
        }
        
        # Initialize variables
        self.traffic_generator = None
        self.traffic_thread = None
        self.is_running = False
        self.live_stats = {
            'successful': 0,
            'failed': 0,
            'completed': 0,
            'total': 0,
            'avg_duration': 0,
            'start_time': None
        }
        self.session_history = []
        self.chart_data = {'times': [], 'success_rates': [], 'speeds': []}
        
        self.setup_ui()
        self.start_live_updates()
    
    def setup_ui(self):
        """Setup the enhanced user interface"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Setup tabs
        self.setup_main_tab()
        self.setup_advanced_tab()
        self.setup_monitoring_tab()
        self.setup_reports_tab()
        self.setup_logs_tab()
    
    def setup_main_tab(self):
        """Setup main control tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main Control")
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=10)
        config_frame.pack(fill='x', padx=10, pady=5)
        
        # URL input
        ttk.Label(config_frame, text="Target URL:").grid(row=0, column=0, sticky='w', pady=2)
        self.url_entry = ttk.Entry(config_frame, width=50)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky='ew', padx=(10, 0), pady=2)
        self.url_entry.insert(0, "https://example.com")
        
        # Sessions input
        ttk.Label(config_frame, text="Number of Sessions:").grid(row=1, column=0, sticky='w', pady=2)
        self.sessions_entry = ttk.Entry(config_frame, width=15)
        self.sessions_entry.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        self.sessions_entry.insert(0, "50")
        
        # Concurrent sessions
        ttk.Label(config_frame, text="Concurrent Sessions:").grid(row=2, column=0, sticky='w', pady=2)
        self.concurrent_entry = ttk.Entry(config_frame, width=15)
        self.concurrent_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=2)
        self.concurrent_entry.insert(0, "3")
        
        # Stealth level
        ttk.Label(config_frame, text="Stealth Level:").grid(row=3, column=0, sticky='w', pady=2)
        self.stealth_var = tk.StringVar(value="High")
        stealth_combo = ttk.Combobox(config_frame, textvariable=self.stealth_var, 
                                   values=["Low", "Medium", "High", "Maximum"])
        stealth_combo.grid(row=3, column=1, sticky='w', padx=(10, 0), pady=2)
        stealth_combo.state(['readonly'])
        
        config_frame.columnconfigure(1, weight=1)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="🚀 Start Traffic Generation", 
                                     command=self.start_traffic, style='Accent.TButton')
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stop", 
                                    command=self.stop_traffic, state='disabled')
        self.stop_button.pack(side='left', padx=(0, 10))
        
        self.pause_button = ttk.Button(control_frame, text="⏸️ Pause", 
                                     command=self.pause_traffic, state='disabled')
        self.pause_button.pack(side='left')
        
        # Progress and status frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress & Status", padding=10)
        progress_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, style='TProgressbar')
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # Status labels
        status_grid = ttk.Frame(progress_frame)
        status_grid.pack(fill='x')
        
        # Create status labels in a grid
        self.status_labels = {}
        labels = [
            ('Status:', 'Idle', 'status'),
            ('Progress:', '0/0', 'progress'),
            ('Success Rate:', '0%', 'success_rate'),
            ('Avg Duration:', '0.0s', 'avg_duration'),
            ('Sessions/Min:', '0', 'speed'),
            ('ETA:', 'N/A', 'eta')
        ]
        
        for i, (label, default, key) in enumerate(labels):
            row, col = i // 2, (i % 2) * 3
            ttk.Label(status_grid, text=label, font=('Arial', 9, 'bold')).grid(
                row=row, column=col, sticky='w', padx=(0, 5), pady=2)
            self.status_labels[key] = ttk.Label(status_grid, text=default, font=('Arial', 9))
            self.status_labels[key].grid(row=row, column=col+1, sticky='w', padx=(0, 20), pady=2)
        
        # Live chart frame
        chart_frame = ttk.LabelFrame(main_frame, text="Live Performance", padding=5)
        chart_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 3))
        self.fig.patch.set_facecolor('#f0f0f0')
        
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self.update_charts()
    
    def setup_advanced_tab(self):
        """Setup advanced configuration tab"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced Settings")
        
        # Browser settings
        browser_frame = ttk.LabelFrame(advanced_frame, text="Browser Configuration", padding=10)
        browser_frame.pack(fill='x', padx=10, pady=5)
        
        # User agent rotation
        self.rotate_ua_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(browser_frame, text="Rotate User Agents", 
                       variable=self.rotate_ua_var).pack(anchor='w')
        
        # Randomize viewport
        self.random_viewport_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(browser_frame, text="Randomize Viewport Sizes", 
                       variable=self.random_viewport_var).pack(anchor='w')
        
        # Simulate referrers
        self.simulate_referrers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(browser_frame, text="Simulate Referrer Traffic", 
                       variable=self.simulate_referrers_var).pack(anchor='w')
        
        # Behavior settings
        behavior_frame = ttk.LabelFrame(advanced_frame, text="Behavior Simulation", padding=10)
        behavior_frame.pack(fill='x', padx=10, pady=5)
        
        # Session duration
        ttk.Label(behavior_frame, text="Session Duration (seconds):").grid(row=0, column=0, sticky='w')
        self.min_duration = ttk.Entry(behavior_frame, width=10)
        self.min_duration.grid(row=0, column=1, padx=5)
        self.min_duration.insert(0, "5")
        ttk.Label(behavior_frame, text="to").grid(row=0, column=2, padx=5)
        self.max_duration = ttk.Entry(behavior_frame, width=10)
        self.max_duration.grid(row=0, column=3, padx=5)
        self.max_duration.insert(0, "30")
        
        # Page depth
        ttk.Label(behavior_frame, text="Max Pages per Session:").grid(row=1, column=0, sticky='w', pady=5)
        self.page_depth = ttk.Entry(behavior_frame, width=10)
        self.page_depth.grid(row=1, column=1, padx=5, pady=5)
        self.page_depth.insert(0, "3")
        
        # Delay settings
        delay_frame = ttk.LabelFrame(advanced_frame, text="Timing Configuration", padding=10)
        delay_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(delay_frame, text="Delay between sessions (seconds):").grid(row=0, column=0, sticky='w')
        self.session_delay = ttk.Entry(delay_frame, width=10)
        self.session_delay.grid(row=0, column=1, padx=5)
        self.session_delay.insert(0, "1")
        
        # Proxy settings
        proxy_frame = ttk.LabelFrame(advanced_frame, text="Proxy Configuration", padding=10)
        proxy_frame.pack(fill='x', padx=10, pady=5)
        
        self.use_proxy_var = tk.BooleanVar()
        ttk.Checkbutton(proxy_frame, text="Use Proxy Rotation", 
                       variable=self.use_proxy_var).pack(anchor='w')
        
        ttk.Label(proxy_frame, text="Proxy List (one per line):").pack(anchor='w', pady=(10, 0))
        self.proxy_text = scrolledtext.ScrolledText(proxy_frame, height=4, width=60)
        self.proxy_text.pack(fill='x', pady=5)
        self.proxy_text.insert('1.0', "# Enter proxies in format: ip:port:username:password\n# Example: 192.168.1.1:8080:user:pass")
    
    def setup_monitoring_tab(self):
        """Setup real-time monitoring tab"""
        monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_frame, text="Live Monitoring")
        
        # System metrics frame
        system_frame = ttk.LabelFrame(monitoring_frame, text="System Performance", padding=10)
        system_frame.pack(fill='x', padx=10, pady=5)
        
        # System metrics
        metrics_grid = ttk.Frame(system_frame)
        metrics_grid.pack(fill='x')
        
        self.system_labels = {}
        system_metrics = [
            ('CPU Usage:', '0%', 'cpu'),
            ('Memory Usage:', '0%', 'memory'),
            ('Active Threads:', '0', 'threads'),
            ('Network Status:', 'Idle', 'network')
        ]
        
        for i, (label, default, key) in enumerate(system_metrics):
            col = i * 2
            ttk.Label(metrics_grid, text=label, font=('Arial', 9, 'bold')).grid(
                row=0, column=col, sticky='w', padx=(0, 5))
            self.system_labels[key] = ttk.Label(metrics_grid, text=default, font=('Arial', 9))
            self.system_labels[key].grid(row=0, column=col+1, sticky='w', padx=(0, 20))
        
        # Session activity frame
        activity_frame = ttk.LabelFrame(monitoring_frame, text="Session Activity", padding=10)
        activity_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create treeview for session tracking
        columns = ('Session', 'Status', 'Duration', 'Pages', 'User Agent', 'Timestamp')
        self.session_tree = ttk.Treeview(activity_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.session_tree.heading(col, text=col)
            self.session_tree.column(col, width=120)
        
        # Scrollbars for treeview
        v_scrollbar = ttk.Scrollbar(activity_frame, orient='vertical', command=self.session_tree.yview)
        h_scrollbar = ttk.Scrollbar(activity_frame, orient='horizontal', command=self.session_tree.xview)
        self.session_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.session_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        activity_frame.grid_rowconfigure(0, weight=1)
        activity_frame.grid_columnconfigure(0, weight=1)
        
        # Real-time stats
        stats_frame = ttk.Frame(monitoring_frame)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.realtime_stats = ttk.Label(stats_frame, text="Waiting for traffic generation to start...", 
                                      font=('Arial', 10), foreground='blue')
        self.realtime_stats.pack()
    
    def setup_reports_tab(self):
        """Setup reports and analytics tab"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="Reports & Analytics")
        
        # Report controls
        control_frame = ttk.Frame(reports_frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="📊 Generate Report", 
                  command=self.generate_report).pack(side='left', padx=(0, 10))
        ttk.Button(control_frame, text="💾 Export CSV", 
                  command=self.export_csv).pack(side='left', padx=(0, 10))
        ttk.Button(control_frame, text="📋 Copy Summary", 
                  command=self.copy_summary).pack(side='left')
        
        # Report display
        report_frame = ttk.LabelFrame(reports_frame, text="Traffic Report", padding=10)
        report_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.report_text = scrolledtext.ScrolledText(report_frame, height=25, wrap=tk.WORD)
        self.report_text.pack(fill='both', expand=True)
        
        # Insert placeholder report
        self.report_text.insert('1.0', self.get_placeholder_report())
    
    def setup_logs_tab(self):
        """Setup logs and debugging tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs & Debug")
        
        # Log controls
        log_control_frame = ttk.Frame(logs_frame)
        log_control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(log_control_frame, text="🗑️ Clear Logs", 
                  command=self.clear_logs).pack(side='left', padx=(0, 10))
        ttk.Button(log_control_frame, text="💾 Save Logs", 
                  command=self.save_logs).pack(side='left', padx=(0, 10))
        
        # Log level selection
        ttk.Label(log_control_frame, text="Log Level:").pack(side='left', padx=(20, 5))
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_control_frame, textvariable=self.log_level_var,
                                     values=["DEBUG", "INFO", "WARNING", "ERROR"], width=10)
        log_level_combo.pack(side='left')
        log_level_combo.state(['readonly'])
        
        # Log display
        log_frame = ttk.LabelFrame(logs_frame, text="Application Logs", padding=5)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, background='black', 
                                                foreground='green', font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # Add initial log entry
        self.add_log_entry("INFO", "Traffic Generator GUI initialized")
    
    def start_traffic(self):
        """Start traffic generation with enhanced features"""
        target_url = self.url_entry.get().strip()
        
        if not target_url:
            messagebox.showwarning("Input Error", "Please enter a valid URL.")
            return
        
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, target_url)
        
        try:
            num_sessions = int(self.sessions_entry.get())
            max_concurrent = int(self.concurrent_entry.get())
            
            if num_sessions <= 0 or max_concurrent <= 0:
                raise ValueError("Sessions must be positive integers.")
                
        except ValueError:
            messagebox.showwarning("Input Error", "Invalid input. Enter positive integers for sessions.")
            return
        
        # Update UI state
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.pause_button.config(state='normal')
        self.is_running = True
        
        # Reset stats
        self.live_stats = {
            'successful': 0,
            'failed': 0,
            'completed': 0,
            'total': num_sessions,
            'avg_duration': 0,
            'start_time': datetime.now()
        }
        self.session_history.clear()
        self.chart_data = {'times': [], 'success_rates': [], 'speeds': []}
        
        # Clear session tree
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)
        
        # Update status
        self.status_labels['status'].config(text="Generating Traffic...", foreground='blue')
        self.add_log_entry("INFO", f"Starting traffic generation: {num_sessions} sessions to {target_url}")
        
        # Create traffic generator with callback
        self.traffic_generator = StealthTrafficGenerator(target_url, callback=self.traffic_callback)
        
        # Start traffic generation in thread
        self.traffic_thread = threading.Thread(target=self.run_traffic, 
                                             args=(num_sessions, max_concurrent))
        self.traffic_thread.daemon = True
        self.traffic_thread.start()
    
    def stop_traffic(self):
        """Stop traffic generation"""
        if self.traffic_generator:
            self.traffic_generator.stop()
            self.add_log_entry("WARNING", "Stop signal sent to traffic generator")
            
        self.is_running = False
        self.update_ui_state('stopped')
    
    def pause_traffic(self):
        """Pause/resume traffic generation"""
        # This is a placeholder - actual pause functionality would need to be implemented in the generator
        if self.pause_button['text'] == '⏸️ Pause':
            self.pause_button.config(text='▶️ Resume')
            self.add_log_entry("INFO", "Traffic generation paused")
        else:
            self.pause_button.config(text='⏸️ Pause')
            self.add_log_entry("INFO", "Traffic generation resumed")
    
    def run_traffic(self, num_sessions, max_concurrent):
        """Run traffic generation in separate thread"""
        try:
            successful, failed = self.traffic_generator.generate_traffic(
                num_sessions=num_sessions,
                max_concurrent=max_concurrent
            )
            
            if self.is_running:  # Only update if not stopped
                self.master.after(0, self.traffic_complete, successful, failed)
                
        except Exception as e:
            self.master.after(0, self.traffic_error, str(e))
    
    def traffic_callback(self, event_type, data):
        """Callback for traffic generator events"""
        self.master.after(0, self.handle_traffic_event, event_type, data)
    
    def handle_traffic_event(self, event_type, data):
        """Handle traffic generator events on main thread"""
        if event_type == 'generation_start':
            self.add_log_entry("INFO", f"Traffic generation started with {data['total_sessions']} sessions")
            
        elif event_type == 'session_start':
            self.add_log_entry("DEBUG", f"Session {data['session_num']} started")
            
        elif event_type == 'session_complete':
            self.handle_session_complete(data)
            
        elif event_type == 'stats_update':
            self.update_live_stats(data)
            
        elif event_type == 'generation_complete':
            self.handle_generation_complete(data)
    
    def handle_session_complete(self, data):
        """Handle individual session completion"""
        session_num = data['session_num']
        success = data['success']
        duration = data.get('duration', 0)
        pages = data.get('pages_visited', 0)
        
        # Add to session tree
        status = "✅ Success" if success else "❌ Failed"
        status_color = 'green' if success else 'red'
        
        item = self.session_tree.insert('', 'end', values=(
            f"#{session_num}",
            status,
            f"{duration:.1f}s",
            pages,
            "Chrome (randomized)",
            datetime.now().strftime("%H:%M:%S")
        ))
        
        # Color code the row
        if success:
            self.session_tree.set(item, 'Status', '✅ Success')
        else:
            self.session_tree.set(item, 'Status', '❌ Failed')
        
        # Auto-scroll to bottom
        self.session_tree.see(item)
        
        # Store session data
        self.session_history.append({
            'session_num': session_num,
            'success': success,
            'duration': duration,
            'pages': pages,
            'timestamp': datetime.now()
        })
        
        # Log the session
        log_level = "INFO" if success else "WARNING"
        self.add_log_entry(log_level, f"Session {session_num}: {'Success' if success else 'Failed'} - {duration:.1f}s, {pages} pages")
    
    def update_live_stats(self, data):
        """Update live statistics display"""
        self.live_stats.update(data)
        
        # Update progress bar
        progress = (data['completed'] / data['total']) * 100 if data['total'] > 0 else 0
        self.progress_var.set(progress)
        
        # Update status labels
        self.status_labels['progress'].config(text=f"{data['completed']}/{data['total']}")
        
        success_rate = (data['successful'] / data['completed']) * 100 if data['completed'] > 0 else 0
        self.status_labels['success_rate'].config(text=f"{success_rate:.1f}%")
        
        self.status_labels['avg_duration'].config(text=f"{data['avg_duration']:.1f}s")
        
        # Calculate sessions per minute
        if self.live_stats['start_time']:
            elapsed = (datetime.now() - self.live_stats['start_time']).total_seconds()
            sessions_per_min = (data['completed'] / elapsed) * 60 if elapsed > 0 else 0
            self.status_labels['speed'].config(text=f"{sessions_per_min:.1f}")
            
            # Calculate ETA
            if sessions_per_min > 0:
                remaining = data['total'] - data['completed']
                eta_minutes = remaining / sessions_per_min
                eta_text = f"{eta_minutes:.1f}m" if eta_minutes > 1 else f"{eta_minutes*60:.0f}s"
                self.status_labels['eta'].config(text=eta_text)
        
        # Update real-time stats
        stats_text = (f"🚀 Active: {data['completed']}/{data['total']} | "
                     f"✅ Success: {data['successful']} | "
                     f"❌ Failed: {data['failed']} | "
                     f"📊 Rate: {success_rate:.1f}%")
        self.realtime_stats.config(text=stats_text)
        
        # Update charts
        self.update_chart_data(success_rate, sessions_per_min)
        self.update_charts()
    
    def update_chart_data(self, success_rate, speed):
        """Update chart data for live visualization"""
        current_time = datetime.now()
        
        self.chart_data['times'].append(current_time)
        self.chart_data['success_rates'].append(success_rate)
        self.chart_data['speeds'].append(speed)
        
        # Keep only last 50 data points
        if len(self.chart_data['times']) > 50:
            for key in self.chart_data:
                self.chart_data[key] = self.chart_data[key][-50:]
    
    def update_charts(self):
        """Update live performance charts"""
        self.ax1.clear()
        self.ax2.clear()
        
        if self.chart_data['times']:
            # Success rate chart
            self.ax1.plot(self.chart_data['times'], self.chart_data['success_rates'], 
                         'g-', linewidth=2, label='Success Rate %')
            self.ax1.set_title('Success Rate Over Time', fontsize=10)
            self.ax1.set_ylabel('Success Rate (%)')
            self.ax1.grid(True, alpha=0.3)
            self.ax1.set_ylim(0, 100)
            
            # Speed chart
            self.ax2.plot(self.chart_data['times'], self.chart_data['speeds'], 
                         'b-', linewidth=2, label='Sessions/Min')
            self.ax2.set_title('Generation Speed', fontsize=10)
            self.ax2.set_ylabel('Sessions/Min')
            self.ax2.grid(True, alpha=0.3)
            
            # Format x-axis
            for ax in [self.ax1, self.ax2]:
                ax.tick_params(axis='x', rotation=45, labelsize=8)
                ax.tick_params(axis='y', labelsize=8)
        
        else:
            # Show placeholder when no data
            for ax, title in zip([self.ax1, self.ax2], ['Success Rate', 'Generation Speed']):
                ax.text(0.5, 0.5, f'Waiting for {title} data...', 
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=10, alpha=0.6)
                ax.set_title(title, fontsize=10)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def traffic_complete(self, successful, failed):
        """Handle traffic generation completion"""
        self.is_running = False
        self.update_ui_state('completed')
        
        # Update final status
        total = successful + failed
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        self.status_labels['status'].config(text="Completed", foreground='green')
        
        completion_msg = (f"Traffic generation completed!\n"
                         f"✅ Successful: {successful}\n"
                         f"❌ Failed: {failed}\n"
                         f"📊 Success Rate: {success_rate:.1f}%")
        
        messagebox.showinfo("Generation Complete", completion_msg)
        self.add_log_entry("INFO", f"Traffic generation completed: {successful} successful, {failed} failed")
        
        # Generate final report
        if self.traffic_generator:
            report = self.traffic_generator.get_report()
            self.display_report(report)
    
    def traffic_error(self, error_msg):
        """Handle traffic generation error"""
        self.is_running = False
        self.update_ui_state('error')
        
        self.status_labels['status'].config(text="Error", foreground='red')
        messagebox.showerror("Error", f"Traffic generation failed: {error_msg}")
        self.add_log_entry("ERROR", f"Traffic generation failed: {error_msg}")
    
    def update_ui_state(self, state):
        """Update UI button states"""
        if state == 'stopped':
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.pause_button.config(state='disabled')
            self.status_labels['status'].config(text="Stopped", foreground='orange')
        elif state == 'completed':
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.pause_button.config(state='disabled')
        elif state == 'error':
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.pause_button.config(state='disabled')
    
    def start_live_updates(self):
        """Start live system monitoring updates"""
        self.update_system_metrics()
        self.master.after(2000, self.start_live_updates)  # Update every 2 seconds
    
    def update_system_metrics(self):
        """Update system performance metrics"""
        if self.traffic_generator:
            try:
                system_info = self.traffic_generator.get_system_info()
                self.system_labels['cpu'].config(text=f"{system_info['cpu_percent']:.1f}%")
                self.system_labels['memory'].config(text=f"{system_info['memory_percent']:.1f}%")
                self.system_labels['threads'].config(text=str(system_info['active_threads']))
                self.system_labels['network'].config(text="Active" if self.is_running else "Idle")
            except:
                pass
    
    def generate_report(self):
        """Generate and display comprehensive report"""
        if self.traffic_generator:
            report = self.traffic_generator.get_report()
            self.display_report(report)
        else:
            messagebox.showinfo("No Data", "No traffic generation data available for report.")
    
    def display_report(self, report):
        """Display formatted report"""
        self.report_text.delete('1.0', tk.END)
        
        report_content = f"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                              TRAFFIC GENERATION REPORT                               ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

📊 EXECUTIVE SUMMARY
════════════════════════════════════════════════════════════════════════════════════════
Session ID: {report['session_id']}
Target URL: {report['target_url']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 KEY METRICS
════════════════════════════════════════════════════════════════════════════════════════
✅ Success Rate: {report['summary']['success_rate']}
⏱️  Total Runtime: {report['summary']['total_runtime']}
📄 Avg Pages/Session: {report['summary']['avg_pages_per_session']}
🏆 Performance Score: {report['summary']['performance_score']}/100

📈 DETAILED STATISTICS
════════════════════════════════════════════════════════════════════════════════════════
Total Sessions: {report['stats']['total_sessions']}
Successful Sessions: {report['stats']['successful_sessions']}
Failed Sessions: {report['stats']['failed_sessions']}
Total Page Views: {report['stats']['total_page_views']}
Average Session Duration: {report['stats']['avg_session_duration']:.2f} seconds
Sessions per Minute: {report['stats']['sessions_per_minute']:.2f}
Bounce Rate: {report['stats']['bounce_rate']:.1f}%

🌍 DIVERSITY METRICS
════════════════════════════════════════════════════════════════════════════════════════
Unique Browsers Used: {len(report['stats']['browsers_used'])}
Countries Simulated: {len(report['stats']['countries_simulated'])}
Unique Pages Visited: {len(report['stats']['unique_pages_visited'])}

🔧 TECHNICAL DETAILS
════════════════════════════════════════════════════════════════════════════════════════
Stealth Features: ✅ User Agent Rotation, ✅ Viewport Randomization, ✅ Referrer Simulation
Browser Profiles: {', '.join(list(report['stats']['browsers_used'])[:5])}
Simulated Countries: {', '.join(list(report['stats']['countries_simulated'])[:10])}

═══════════════════════════════════════════════════════════════════════════════════════
Report generated by GhostTraffic
For support and updates, visit: https://github.com/Dahnhiel/Website-Traffic-Driver
═══════════════════════════════════════════════════════════════════════════════════════
        """
        
        self.report_text.insert('1.0', report_content)
        
        # Switch to reports tab
        self.notebook.select(3)
    
    def get_placeholder_report(self):
        """Get placeholder report text"""
        return """
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                          TRAFFIC GENERATION REPORT                                   ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

📊 Waiting for traffic generation to complete...

This comprehensive report will include:
• Executive summary with key performance indicators
• Detailed session statistics and success metrics
• Browser diversity and geolocation simulation data
• Performance analysis and optimization recommendations
• Technical configuration details

Start a traffic generation session to see your detailed report here.

═══════════════════════════════════════════════════════════════════════════════════════
GhostTraffic - Ready for Action!
═══════════════════════════════════════════════════════════════════════════════════════
        """
    
    def export_csv(self):
        """Export session data to CSV"""
        if not self.session_history:
            messagebox.showinfo("No Data", "No session data available to export.")
            return
        
        try:
            from tkinter import filedialog
            import csv
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Session Data"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['session_num', 'success', 'duration', 'pages', 'timestamp']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for session in self.session_history:
                        writer.writerow({
                            'session_num': session['session_num'],
                            'success': session['success'],
                            'duration': session['duration'],
                            'pages': session['pages'],
                            'timestamp': session['timestamp'].isoformat()
                        })
                
                messagebox.showinfo("Export Complete", f"Session data exported to {filename}")
                self.add_log_entry("INFO", f"Session data exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
            self.add_log_entry("ERROR", f"Export failed: {str(e)}")
    
    def copy_summary(self):
        """Copy session summary to clipboard"""
        if not self.session_history:
            messagebox.showinfo("No Data", "No session data available to copy.")
            return
        
        try:
            successful = sum(1 for s in self.session_history if s['success'])
            failed = len(self.session_history) - successful
            avg_duration = sum(s['duration'] for s in self.session_history) / len(self.session_history)
            total_pages = sum(s['pages'] for s in self.session_history)
            
            summary = f"""Traffic Generation Summary:
• Total Sessions: {len(self.session_history)}
• Successful: {successful} ({successful/len(self.session_history)*100:.1f}%)
• Failed: {failed} ({failed/len(self.session_history)*100:.1f}%)
• Average Duration: {avg_duration:.2f} seconds
• Total Pages Visited: {total_pages}
• Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            self.master.clipboard_clear()
            self.master.clipboard_append(summary)
            messagebox.showinfo("Copied", "Summary copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy summary: {str(e)}")
    
    def add_log_entry(self, level, message):
        """Add a log entry to the log display"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_colors = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red'
        }
        
        color = log_colors.get(level, 'white')
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # Auto-scroll to bottom
        
        # Color the last line
        line_start = self.log_text.index("end-2l")
        line_end = self.log_text.index("end-1l")
        self.log_text.tag_add(level, line_start, line_end)
        self.log_text.tag_config(level, foreground=color)
        
        # Limit log size to prevent memory issues
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 1000:
            self.log_text.delete('1.0', '100.0')
    
    def clear_logs(self):
        """Clear all log entries"""
        self.log_text.delete('1.0', tk.END)
        self.add_log_entry("INFO", "Logs cleared")
    
    def save_logs(self):
        """Save logs to file"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Logs"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get('1.0', tk.END))
                
                messagebox.showinfo("Save Complete", f"Logs saved to {filename}")
                self.add_log_entry("INFO", f"Logs saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save logs: {str(e)}")
            self.add_log_entry("ERROR", f"Save logs failed: {str(e)}")

def main():
    """Main function to start the application"""
    root = tk.Tk()
    
    # Set application icon (if available)
    try:
        # You can add an icon file here if you have one
        # root.iconbitmap('icon.ico')
        pass
    except:
        pass
    
    # Apply modern theme
    try:
        root.tk.call('source', 'azure.tcl')
        root.tk.call('set_theme', 'light')
    except:
        pass  # Fallback to default theme if Azure theme not available
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Create and run application
    app = EnhancedTrafficGeneratorGUI(root)
    
    # Handle window close event
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("Quit", "Traffic generation is running. Do you want to stop it and quit?"):
                app.stop_traffic()
                root.after(1000, root.destroy)  # Give time for cleanup
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        if app.is_running:
            app.stop_traffic()
        root.destroy()

if __name__ == "__main__":
    main()