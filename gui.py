"""
GUI DASHBOARD
-------------
Tkinter-based graphical user interface for viewing and managing USB logs.

ENHANCED FEATURES:
- File activity log display (second table)
- Analytics dashboard (sessions, file transfers, large transfers)
- Alert popups for large file transfers (>50MB)
- Refresh file logs button
- Color coding for risk levels
- Enhanced status information

Tkinter is used because:
- Built into Python (no extra installation)
- Cross-platform compatible
- Perfect for desktop applications
- Easy to learn and demonstrate
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import (fetch_all_logs, clear_all_logs, fetch_file_logs, clear_file_logs,
                      count_large_transfers, count_total_file_events, count_sessions_today,
                      count_unauthorized_events)
from config import get_app_config, save_app_config, WHITELIST_PATH
from export import export_to_csv
from utils import format_file_size, format_duration, get_timestamp
import threading


class USBLoggerGUI:
    """
    Main GUI class for Real Time USB Activity Logger.
    
    Features:
    - Real-time USB log display
    - File activity monitoring display
    - Analytics dashboard
    - Auto-refresh capability
    - CSV export
    - Clear logs function
    - Alert popups for large transfers
    - Professional styling
    """
    
    def __init__(self, root):
        """
        Initialize the GUI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Real Time USB Activity Logger")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        
        # Auto-refresh control
        self.auto_refresh = True
        self.refresh_interval = 3000  # milliseconds (3 seconds)
        
        # Setup GUI components
        self.setup_ui()
        
        # Populate admin input fields once on init (before auto-refresh starts)
        self.populate_admin_input_fields()
        
        # Start auto-refresh
        self.schedule_refresh()
    
    def setup_ui(self):
        """
        Create and arrange all GUI components.
        """
        # ===== TITLE SECTION =====
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🔌 Real Time USB Activity Logger",
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # ===== ANALYTICS DASHBOARD =====
        analytics_frame = tk.Frame(self.root, bg='#ecf0f1', height=80)
        analytics_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=5)
        analytics_frame.pack_propagate(False)
        
        # Analytics labels
        self.sessions_label = tk.Label(
            analytics_frame,
            text="Sessions Today: 0",
            font=('Arial', 11, 'bold'),
            bg='#3498db',
            fg='white',
            padx=15,
            pady=10,
            relief=tk.RAISED,
            bd=2
        )
        self.sessions_label.pack(side=tk.LEFT, padx=10, pady=15)
        
        self.file_events_label = tk.Label(
            analytics_frame,
            text="Total File Events: 0",
            font=('Arial', 11, 'bold'),
            bg='#2ecc71',
            fg='white',
            padx=15,
            pady=10,
            relief=tk.RAISED,
            bd=2
        )
        self.file_events_label.pack(side=tk.LEFT, padx=10, pady=15)
        
        self.large_transfers_label = tk.Label(
            analytics_frame,
            text="⚠️ Large Transfers: 0",
            font=('Arial', 11, 'bold'),
            bg='#e74c3c',
            fg='white',
            padx=15,
            pady=10,
            relief=tk.RAISED,
            bd=2
        )
        self.large_transfers_label.pack(side=tk.LEFT, padx=10, pady=15)
        
        # ===== ADMIN DASHBOARD PANEL =====
        self.admin_frame = tk.Frame(self.root, bg='#f8f9fa', height=110)
        self.admin_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=5)
        self.admin_frame.pack_propagate(False)

        admin_title = tk.Label(
            admin_frame,
            text="Admin Dashboard",
            font=('Arial', 12, 'bold'),
            bg='#f8f9fa',
            fg='#2c3e50'
        )
        admin_title.pack(anchor='w', padx=10, pady=(8, 4))

        self.email_alert_status_label = tk.Label(
            admin_frame,
            text="Email Alerts: Disabled",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        self.email_alert_status_label.pack(anchor='w', padx=20)

        self.email_sender_label = tk.Label(
            admin_frame,
            text="Sender: N/A",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        self.email_sender_label.pack(anchor='w', padx=20)

        self.email_recipients_label = tk.Label(
            admin_frame,
            text="Recipients: N/A",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        self.email_recipients_label.pack(anchor='w', padx=20)

        self.email_enabled_var = tk.BooleanVar(value=False)
        self.email_enabled_check = tk.Checkbutton(
            admin_frame,
            text="Enable email alerts",
            variable=self.email_enabled_var,
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e',
            activebackground='#f8f9fa',
            selectcolor='#f8f9fa'
        )
        self.email_enabled_check.pack(anchor='w', padx=20, pady=(4, 2))

        smtp_host_label = tk.Label(
            admin_frame,
            text="SMTP Host:",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        smtp_host_label.pack(anchor='w', padx=20, pady=(2, 0))
        self.smtp_host_entry = tk.Entry(admin_frame, width=40)
        self.smtp_host_entry.insert(0, '')
        self.smtp_host_entry.pack(anchor='w', padx=20, pady=(0, 2))

        smtp_port_label = tk.Label(
            admin_frame,
            text="SMTP Port:",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        smtp_port_label.pack(anchor='w', padx=20, pady=(2, 0))
        self.smtp_port_entry = tk.Entry(admin_frame, width=12)
        self.smtp_port_entry.insert(0, '587')
        self.smtp_port_entry.pack(anchor='w', padx=20, pady=(0, 8))

        smtp_username_label = tk.Label(
            admin_frame,
            text="SMTP Username:",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        smtp_username_label.pack(anchor='w', padx=20, pady=(2, 0))
        self.smtp_username_entry = tk.Entry(admin_frame, width=40)
        self.smtp_username_entry.insert(0, '')
        self.smtp_username_entry.pack(anchor='w', padx=20, pady=(0, 2))

        smtp_password_label = tk.Label(
            admin_frame,
            text="SMTP Password:",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        smtp_password_label.pack(anchor='w', padx=20, pady=(2, 0))
        self.smtp_password_entry = tk.Entry(admin_frame, width=40, show='*')
        self.smtp_password_entry.insert(0, '')
        self.smtp_password_entry.pack(anchor='w', padx=20, pady=(0, 8))

        self.admin_sender_entry = tk.Entry(admin_frame, width=50)
        self.admin_sender_entry.insert(0, '')
        self.admin_sender_entry.pack(anchor='w', padx=20, pady=(4, 2))

        self.admin_recipients_entry = tk.Entry(admin_frame, width=50)
        self.admin_recipients_entry.insert(0, '')
        self.admin_recipients_entry.pack(anchor='w', padx=20, pady=(2, 8))

        self.admin_total_usb_label = tk.Label(
            admin_frame,
            text="Total USB events: 0",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        self.admin_total_usb_label.pack(anchor='w', padx=20)

        self.admin_total_file_label = tk.Label(
            admin_frame,
            text="Total file events: 0",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        self.admin_total_file_label.pack(anchor='w', padx=20)

        self.admin_whitelist_label = tk.Label(
            admin_frame,
            text="Whitelist enforcement: Unknown",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        self.admin_whitelist_label.pack(anchor='w', padx=20)

        self.admin_unauthorized_label = tk.Label(
            admin_frame,
            text="Unauthorized events: 0",
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#34495e'
        )
        self.admin_unauthorized_label.pack(anchor='w', padx=20)

        self.admin_buttons_frame = tk.Frame(admin_frame, bg='#f8f9fa')
        self.admin_buttons_frame.pack(fill=tk.X, padx=10, pady=8)

        self.open_whitelist_admin_btn = tk.Button(
            self.admin_buttons_frame,
            text="Open Whitelist File",
            command=self.open_whitelist_file,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=18,
            relief=tk.RAISED,
            bd=2
        )
        self.open_whitelist_admin_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.refresh_admin_btn = tk.Button(
            self.admin_buttons_frame,
            text="Refresh Admin Panel",
            command=self.refresh_admin_dashboard,
            bg='#2ecc71',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=18,
            relief=tk.RAISED,
            bd=2
        )
        self.refresh_admin_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.save_admin_email_btn = tk.Button(
            self.admin_buttons_frame,
            text="Save Email Settings",
            command=self.save_admin_email_settings,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=18,
            relief=tk.RAISED,
            bd=2
        )
        self.save_admin_email_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # ===== BUTTON PANEL =====
        button_frame = tk.Frame(self.root, bg='#ecf0f1', height=60)
        button_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=5)
        button_frame.pack_propagate(False)
        
        # Button styling
        button_style = {
            'font': ('Arial', 9, 'bold'),
            'width': 14,
            'height': 2,
            'relief': tk.RAISED,
            'bd': 2
        }
        
        # Refresh USB logs button
        self.refresh_usb_btn = tk.Button(
            button_frame,
            text="🔄 Refresh USB",
            command=self.refresh_usb_logs,
            bg='#3498db',
            fg='white',
            **button_style
        )
        self.refresh_usb_btn.pack(side=tk.LEFT, padx=3)
        
        # Refresh file logs button
        self.refresh_file_btn = tk.Button(
            button_frame,
            text="📁 Refresh Files",
            command=self.refresh_file_logs,
            bg='#9b59b6',
            fg='white',
            **button_style
        )
        self.refresh_file_btn.pack(side=tk.LEFT, padx=3)
        
        # Export button
        self.export_btn = tk.Button(
            button_frame,
            text="📤 Export CSV",
            command=self.export_logs,
            bg='#2ecc71',
            fg='white',
            **button_style
        )
        self.export_btn.pack(side=tk.LEFT, padx=3)
        
        # Clear USB logs button
        self.clear_usb_btn = tk.Button(
            button_frame,
            text="🗑️ Clear USB",
            command=self.clear_usb_logs,
            bg='#e67e22',
            fg='white',
            **button_style
        )
        self.clear_usb_btn.pack(side=tk.LEFT, padx=3)
        
        # Clear file logs button
        self.clear_file_btn = tk.Button(
            button_frame,
            text="🗑️ Clear Files",
            command=self.clear_file_logs_action,
            bg='#e74c3c',
            fg='white',
            **button_style
        )
        self.clear_file_btn.pack(side=tk.LEFT, padx=3)
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.auto_refresh_check = tk.Checkbutton(
            button_frame,
            text="Auto-Refresh",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh,
            font=('Arial', 9),
            bg='#ecf0f1'
        )
        self.auto_refresh_check.pack(side=tk.LEFT, padx=15)

        self.admin_mode_var = tk.BooleanVar(value=True)
        self.admin_mode_check = tk.Checkbutton(
            button_frame,
            text="Admin Mode",
            variable=self.admin_mode_var,
            command=self.toggle_admin_mode,
            font=('Arial', 9),
            bg='#ecf0f1'
        )
        self.admin_mode_check.pack(side=tk.LEFT, padx=15)
        
        # Exit button
        self.exit_btn = tk.Button(
            button_frame,
            text="❌ Exit",
            command=self.exit_application,
            bg='#95a5a6',
            fg='white',
            **button_style
        )
        self.exit_btn.pack(side=tk.RIGHT, padx=3)
        
        # ===== USB LOGS TABLE SECTION =====
        usb_label_frame = tk.LabelFrame(
            self.root,
            text="USB Device Activity",
            font=('Arial', 11, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        usb_label_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        usb_table_frame = tk.Frame(usb_label_frame)
        usb_table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create USB Treeview
        usb_columns = ('ID', 'Event', 'Device', 'VID', 'PID', 'Serial', 'Username', 'Timestamp', 'Duration')
        
        self.usb_tree = ttk.Treeview(usb_table_frame, columns=usb_columns, show='headings', height=10)
        
        # Define column headings and widths
        usb_column_widths = {
            'ID': 40,
            'Event': 100,
            'Device': 200,
            'VID': 70,
            'PID': 70,
            'Serial': 150,
            'Username': 100,
            'Timestamp': 140,
            'Duration': 80
        }
        
        for col in usb_columns:
            self.usb_tree.heading(col, text=col, anchor=tk.W)
            self.usb_tree.column(col, width=usb_column_widths.get(col, 100), anchor=tk.W)
        
        # Add scrollbars
        usb_vsb = ttk.Scrollbar(usb_table_frame, orient="vertical", command=self.usb_tree.yview)
        usb_hsb = ttk.Scrollbar(usb_table_frame, orient="horizontal", command=self.usb_tree.xview)
        self.usb_tree.configure(yscrollcommand=usb_vsb.set, xscrollcommand=usb_hsb.set)
        
        # Grid layout
        self.usb_tree.grid(row=0, column=0, sticky='nsew')
        usb_vsb.grid(row=0, column=1, sticky='ns')
        usb_hsb.grid(row=1, column=0, sticky='ew')
        
        usb_table_frame.grid_rowconfigure(0, weight=1)
        usb_table_frame.grid_columnconfigure(0, weight=1)
        
        # Apply row coloring
        self.usb_tree.tag_configure('connected', background='#d5f4e6')
        self.usb_tree.tag_configure('disconnected', background='#fadbd8')
        
        # ===== FILE ACTIVITY TABLE SECTION =====
        file_label_frame = tk.LabelFrame(
            self.root,
            text="File Activity Log",
            font=('Arial', 11, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        file_label_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        file_table_frame = tk.Frame(file_label_frame)
        file_table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create File Treeview
        file_columns = ('ID', 'Device ID', 'File Path', 'Event', 'Size', 'Risk', 'Username', 'Timestamp')
        
        self.file_tree = ttk.Treeview(file_table_frame, columns=file_columns, show='headings', height=10)
        
        # Define column headings and widths
        file_column_widths = {
            'ID': 40,
            'Device ID': 100,
            'File Path': 350,
            'Event': 90,
            'Size': 100,
            'Risk': 120,
            'Username': 100,
            'Timestamp': 140
        }
        
        for col in file_columns:
            self.file_tree.heading(col, text=col, anchor=tk.W)
            self.file_tree.column(col, width=file_column_widths.get(col, 100), anchor=tk.W)
        
        # Add scrollbars
        file_vsb = ttk.Scrollbar(file_table_frame, orient="vertical", command=self.file_tree.yview)
        file_hsb = ttk.Scrollbar(file_table_frame, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=file_vsb.set, xscrollcommand=file_hsb.set)
        
        # Grid layout
        self.file_tree.grid(row=0, column=0, sticky='nsew')
        file_vsb.grid(row=0, column=1, sticky='ns')
        file_hsb.grid(row=1, column=0, sticky='ew')
        
        file_table_frame.grid_rowconfigure(0, weight=1)
        file_table_frame.grid_columnconfigure(0, weight=1)
        
        # Apply row coloring for risk levels
        self.file_tree.tag_configure('normal', background='#ffffff')
        self.file_tree.tag_configure('large_transfer', background='#ffcccc', foreground='#c0392b')
        self.file_tree.tag_configure('suspicious_file', background='#fadbd8', foreground='#e74c3c')
        
        # ===== STATUS BAR =====
        self.status_bar = tk.Label(
            self.root,
            text="Ready | USB Logs: 0 | File Events: 0",
            bg='#34495e',
            fg='white',
            font=('Arial', 9),
            anchor=tk.W,
            relief=tk.SUNKEN
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Initial load
        self.refresh_all()
    
    def refresh_usb_logs(self):
        """
        Refresh the USB log table with latest data from database.
        """
        # Clear existing items
        for item in self.usb_tree.get_children():
            self.usb_tree.delete(item)
        
        # Fetch logs from database
        logs = fetch_all_logs()
        
        # Insert logs into table
        for log in logs:
            # log format: (id, event_type, device_name, device_id, vendor_id, product_id, 
            #              serial_number, timestamp, connect_time, disconnect_time, usage_duration, username)
            
            # Format duration
            duration_str = ''
            if log[10]:  # usage_duration
                duration_str = format_duration(log[10])
            
            display_data = (
                log[0],  # ID
                log[1],  # Event Type
                log[2] or 'Unknown',  # Device Name
                log[4] or 'N/A',  # Vendor ID
                log[5] or 'N/A',  # Product ID
                log[6] or 'N/A',  # Serial Number
                log[11] or 'N/A',  # Username
                log[7],  # Timestamp
                duration_str  # Duration
            )
            
            # Color code based on event type
            tag = 'connected' if log[1] == 'CONNECTED' else 'disconnected'
            self.usb_tree.insert('', tk.END, values=display_data, tags=(tag,))
        
        return len(logs)
    
    def refresh_file_logs(self):
        """
        Refresh the file activity table with latest data from database.
        """
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Fetch file logs from database
        logs = fetch_file_logs(limit=500)  # Limit to last 500 events
        
        # Insert logs into table
        for log in logs:
            # log format: (id, device_id, file_path, event_type, file_size, username, timestamp, risk_flag)
            
            # Format file size
            size_str = format_file_size(log[4]) if log[4] else '0 B'
            
            # Shorten device ID for display
            device_id_short = log[1][:20] + '...' if len(log[1]) > 20 else log[1]
            
            display_data = (
                log[0],  # ID
                device_id_short,  # Device ID (shortened)
                log[2],  # File Path
                log[3],  # Event Type
                size_str,  # File Size (formatted)
                log[7] or 'NORMAL',  # Risk Flag
                log[5] or 'N/A',  # Username
                log[6]  # Timestamp
            )
            
            # Color code based on risk level
            tag = 'normal'
            if log[7] == 'LARGE_TRANSFER':
                tag = 'large_transfer'
            elif log[7] == 'SUSPICIOUS_FILE':
                tag = 'suspicious_file'
                
            self.file_tree.insert('', tk.END, values=display_data, tags=(tag,))
        
        return len(logs)
    
    def refresh_analytics(self):
        """
        Refresh the analytics dashboard.
        """
        sessions = count_sessions_today()
        file_events = count_total_file_events()
        large_transfers = count_large_transfers()
        
        self.sessions_label.config(text=f"Sessions Today: {sessions}")
        self.file_events_label.config(text=f"Total File Events: {file_events}")
        self.large_transfers_label.config(text=f"⚠️ Large Transfers: {large_transfers}")
        self.refresh_admin_dashboard()

    def refresh_admin_dashboard(self):
        """Refresh read-only display labels only (not input fields)."""
        config = get_app_config()
        email_config = config.get('email_alerts', {})
        enabled = email_config.get('enabled', False)
        sender = email_config.get('sender', 'N/A') or 'N/A'
        recipients = ', '.join(email_config.get('recipients', [])) or 'None'
        whitelist_enabled = config.get('whitelist_enabled', True)
        unauthorized_count = count_unauthorized_events()

        self.email_alert_status_label.config(text=f"Email Alerts: {'Enabled' if enabled else 'Disabled'}")
        self.email_sender_label.config(text=f"Sender: {sender}")
        self.email_recipients_label.config(text=f"Recipients: {recipients}")
        self.admin_whitelist_label.config(text=f"Whitelist enforcement: {'Enabled' if whitelist_enabled else 'Disabled'}")
        total_usb = len(fetch_all_logs())
        total_file = count_total_file_events()
        self.admin_total_usb_label.config(text=f"Total USB events: {total_usb}")
        self.admin_total_file_label.config(text=f"Total file events: {total_file}")
        self.admin_unauthorized_label.config(text=f"Unauthorized events: {unauthorized_count}")

    def populate_admin_input_fields(self):
        """Populate input fields from config (called on load and after save only)."""
        config = get_app_config()
        email_config = config.get('email_alerts', {})
        enabled = email_config.get('enabled', False)
        sender = email_config.get('sender', '') or ''
        recipients = ', '.join(email_config.get('recipients', []))
        
        self.email_enabled_var.set(enabled)
        self.smtp_host_entry.delete(0, tk.END)
        self.smtp_host_entry.insert(0, email_config.get('smtp_host', ''))
        self.smtp_port_entry.delete(0, tk.END)
        self.smtp_port_entry.insert(0, str(email_config.get('smtp_port', 587)))
        self.smtp_username_entry.delete(0, tk.END)
        self.smtp_username_entry.insert(0, email_config.get('username', ''))
        self.smtp_password_entry.delete(0, tk.END)
        self.smtp_password_entry.insert(0, email_config.get('password', ''))
        self.admin_sender_entry.delete(0, tk.END)
        self.admin_sender_entry.insert(0, sender)
        self.admin_recipients_entry.delete(0, tk.END)
        self.admin_recipients_entry.insert(0, recipients)

    def refresh_all(self):
        """
        Refresh all displays (USB logs, file logs, analytics).
        """
        usb_count = self.refresh_usb_logs()
        file_count = self.refresh_file_logs()
        self.refresh_analytics()
        self.refresh_admin_dashboard()
        
        # Update status bar
        self.status_bar.config(text=f"Ready | USB Logs: {usb_count} | File Events: {file_count}")
    
    def schedule_refresh(self):
        """
        Schedule automatic refresh of all logs.
        """
        if self.auto_refresh_var.get():
            self.refresh_all()
        
        # Schedule next refresh
        self.root.after(self.refresh_interval, self.schedule_refresh)
    
    def toggle_auto_refresh(self):
        """
        Toggle auto-refresh on/off.
        """
        if self.auto_refresh_var.get():
            self.status_bar.config(text="Auto-refresh enabled")
        else:
            self.status_bar.config(text="Auto-refresh disabled")

    def toggle_admin_mode(self):
        # Keep the admin panel always visible and just refresh its contents.
        self.admin_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=5)
        self.refresh_admin_dashboard()
    
    def save_admin_email_settings(self):
        config = get_app_config()
        email_config = config.get('email_alerts', {})
        email_config['enabled'] = self.email_enabled_var.get()
        email_config['smtp_host'] = self.smtp_host_entry.get().strip()
        try:
            email_config['smtp_port'] = int(self.smtp_port_entry.get().strip() or 587)
        except ValueError:
            email_config['smtp_port'] = 587
        email_config['username'] = self.smtp_username_entry.get().strip()
        email_config['password'] = self.smtp_password_entry.get()
        email_config['sender'] = self.admin_sender_entry.get().strip()
        recipients = [recipient.strip() for recipient in self.admin_recipients_entry.get().split(',') if recipient.strip()]
        email_config['recipients'] = recipients
        config['email_alerts'] = email_config

        if save_app_config(config):
            messagebox.showinfo('Saved', 'Email settings saved successfully.')
        else:
            messagebox.showerror('Save Failed', 'Unable to save email settings.')

        self.refresh_admin_dashboard()
        self.populate_admin_input_fields()
    
    def export_logs(self):
        """
        Export logs to CSV file.
        """
        success, message, filepath = export_to_csv()
        
        if success:
            messagebox.showinfo("Export Successful", f"{message}\n\nSaved to:\n{filepath}")
        else:
            messagebox.showerror("Export Failed", message)
    
    def clear_usb_logs(self):
        """
        Clear all USB logs from database after confirmation.
        """
        response = messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to delete ALL USB logs?\n\nThis action cannot be undone!"
        )
        
        if response:
            success = clear_all_logs()
            if success:
                self.refresh_all()
                messagebox.showinfo("Success", "All USB logs have been cleared.")
            else:
                messagebox.showerror("Error", "Failed to clear USB logs.")
    
    def clear_file_logs_action(self):
        """
        Clear all file logs from database after confirmation.
        """
        response = messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to delete ALL file logs?\n\nThis action cannot be undone!"
        )
        
        if response:
            success = clear_file_logs()
            if success:
                self.refresh_all()
                messagebox.showinfo("Success", "All file logs have been cleared.")
            else:
                messagebox.showerror("Error", "Failed to clear file logs.")

    def open_whitelist_file(self):
        """
        Open or create the whitelist file for editing.
        """
        try:
            if not os.path.exists(WHITELIST_PATH):
                with open(WHITELIST_PATH, 'w', encoding='utf-8') as f:
                    f.write('{"whitelist_enabled": true, "whitelisted_devices": []}')
            os.startfile(WHITELIST_PATH)
        except Exception as e:
            messagebox.showerror("Open Failed", f"Unable to open whitelist file:\n{e}")
    
    def show_large_transfer_alert(self, file_path, file_size_mb, username, event_type, risk_flag='LARGE_TRANSFER'):
        """
        Show alert popup for high risk file activity.
        
        Args:
            file_path (str): Path to the file
            file_size_mb (float): File size in MB
            username (str): User who performed the action
            event_type (str): Type of event (CREATED, MODIFIED, etc.)
            risk_flag (str): Type of risk ('LARGE_TRANSFER' or 'SUSPICIOUS_FILE')
        """
        import os
        filename = os.path.basename(file_path)
        
        title = "⚠️ SECURITY ALERT"
        header = "POTENTIAL DATA EXFILTRATION DETECTED"
        description = "This file exceeds the 50MB threshold."
        
        if risk_flag == 'SUSPICIOUS_FILE':
            title = "⛔ SUSPICIOUS FILE DETECTED"
            if event_type == 'FOUND_ON_SCAN':
                header = "EXISTING SUSPICIOUS FILE FOUND"
                description = "This file was already on the drive when connected."
            else:
                header = "EXECUTABLE/SCRIPT FILE DETECTED"
                description = "This file type (.exe/.bat/etc) is potentially dangerous."
        
        alert_message = f"""
{header}

File: {filename}
Full Path: {file_path}
Size: {file_size_mb:.2f} MB
Event: {event_type}
User: {username}
Time: {get_timestamp()}
Risk: {risk_flag}

{description}
The operation has been LOGGED.
        """
        
        # Show warning dialog
        messagebox.showwarning(
            title,
            alert_message.strip()
        )
    
    def exit_application(self):
        """
        Exit the application.
        """
        response = messagebox.askyesno("Exit", "Are you sure you want to exit?")
        if response:
            self.root.quit()


def launch_gui():
    """
    Launch the GUI application.
    """
    root = tk.Tk()
    app = USBLoggerGUI(root)
    
    # Set up file alert callback for monitor
    try:
        from monitor import set_file_alert_callback
        set_file_alert_callback(app.show_large_transfer_alert)
    except ImportError:
        pass
    
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
