"""
PyQt6-based GUI for Real Time USB Activity Logger

This provides a modern UI alternative to the existing Tkinter `gui.py`.
It exposes `launch_gui()` so `main.py` can call it interchangeably.

Features implemented (minimal, functional):
- Tabs: USB Activity, File Activity, Analytics
- Tables populated from `database` helper functions
- Refresh, Export, Clear actions
- Auto-refresh via QTimer
- Hook for `monitor.set_file_alert_callback`

Notes: This is intentionally compact to bootstrap the migration. Further
styling, charts, and searchable filters will be added in next steps.
"""
import json
import os

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTabWidget, QTreeWidget,
                             QTreeWidgetItem, QLabel, QCheckBox, QFileDialog, QMessageBox,
                             QLineEdit, QComboBox, QPlainTextEdit)
import sys
import threading
import datetime

try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget
    PYQTGRAPH_AVAILABLE = True
except Exception:
    PYQTGRAPH_AVAILABLE = False

from database import (fetch_all_logs, fetch_file_logs, clear_all_logs,
                      clear_file_logs, count_large_transfers, count_total_file_events,
                      count_sessions_today, count_unauthorized_events, fetch_unauthorized_logs)
from config import get_app_config, save_app_config, WHITELIST_PATH
from export import export_to_csv, export_to_json
from monitor import get_active_sessions
from utils import format_file_size, format_duration, get_timestamp, send_email_notification


class USBLoggerQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real Time USB Activity Logger")
        self.resize(1200, 800)
        self.THEME_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'theme_config.json')
        self.theme_presets = {
            'Light': {
                'primary': '#2c3e50', 'accent': '#3498db', 'success': '#2ecc71',
                'warn': '#e67e22', 'danger': '#e74c3c', 'bg': '#f5f7fa', 'card': '#ffffff',
                'input_bg': 'white', 'input_border': '#dfe6ee', 'header_bg': '#ecf0f3',
                'disabled_bg': '#e5e7eb', 'disabled_text': '#9ca3af'
            },
            'Dark': {
                'primary': '#ecf0f3', 'accent': '#5dade2', 'success': '#27ae60',
                'warn': '#d35400', 'danger': '#c0392b', 'bg': '#121212', 'card': '#1e1e1e',
                'input_bg': '#1e1e1e', 'input_border': '#2b2b2b', 'header_bg': '#1a1a1a',
                'disabled_bg': '#2d2d2d', 'disabled_text': '#555555'
            },
            'Ocean': {
                'primary': '#1b2838', 'accent': '#4f8fd8', 'success': '#2aa198',
                'warn': '#e68a00', 'danger': '#c0392b', 'bg': '#eaf3fb', 'card': '#ffffff',
                'input_bg': 'white', 'input_border': '#bfd7f5', 'header_bg': '#dcebf9',
                'disabled_bg': '#e5e7eb', 'disabled_text': '#9ca3af'
            },
            'Professional': {
                'primary': '#1f2937', 'accent': '#2563eb', 'success': '#16a34a',
                'warn': '#d97706', 'danger': '#b91c1c', 'bg': '#f3f4f6', 'card': '#ffffff',
                'input_bg': 'white', 'input_border': '#d1d5db', 'header_bg': '#e5e7eb',
                'disabled_bg': '#e5e7eb', 'disabled_text': '#9ca3af'
            }
        }
        self.current_theme = self.load_theme_setting()
        self.apply_theme(self.current_theme)

        self.auto_refresh = True
        self.refresh_interval_ms = 3000

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Collapsible container helper
        class CollapsibleBox(QtWidgets.QWidget):
            def __init__(self, title="", parent=None):
                super().__init__(parent)
                self.toggle_button = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
                self.toggle_button.setStyleSheet("QToolButton { border: none; font-weight: bold; }")
                self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
                self.toggle_button.clicked.connect(self.on_pressed)

                self.content_area = QtWidgets.QScrollArea(maximumHeight=0, minimumHeight=0)
                self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
                self.content_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

                lay = QtWidgets.QVBoxLayout(self)
                lay.setSpacing(4)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.addWidget(self.toggle_button)
                lay.addWidget(self.content_area)

                self.content_widget = QtWidgets.QWidget()
                self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
                self.content_layout.setContentsMargins(6, 6, 6, 6)
                self.content_area.setWidget(self.content_widget)
                self.content_area.setWidgetResizable(True)

            def on_pressed(self):
                checked = self.toggle_button.isChecked()
                self.toggle_button.setArrowType(QtCore.Qt.ArrowType.DownArrow if checked else QtCore.Qt.ArrowType.RightArrow)
                self.content_area.setMaximumHeight(16777215 if checked else 0)

            def addWidget(self, widget):
                self.content_layout.addWidget(widget)


        # Top controls
        controls = QHBoxLayout()
        self.refresh_usb_btn = QPushButton("Refresh USB")
        self.refresh_file_btn = QPushButton("Refresh Files")
        self.export_btn = QPushButton("Export")
        self.export_format_selector = QComboBox()
        self.export_format_selector.addItems(['CSV', 'JSON'])
        self.clear_usb_btn = QPushButton("Clear USB")
        self.clear_file_btn = QPushButton("Clear Files")
        self.auto_refresh_chk = QCheckBox("Auto-refresh")
        self.auto_refresh_chk.setChecked(True)
        self.dark_mode_chk = QCheckBox("Dark mode")
        self.admin_mode_chk = QCheckBox("Admin Mode")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(['Light', 'Dark', 'Ocean', 'Professional'])
        self.theme_selector.setCurrentText(self.current_theme)
        self.dark_mode_chk.setChecked(self.current_theme == 'Dark')

        controls.addWidget(self.refresh_usb_btn)
        controls.addWidget(self.refresh_file_btn)
        controls.addWidget(self.export_btn)
        controls.addWidget(self.export_format_selector)
        controls.addWidget(self.clear_usb_btn)
        controls.addWidget(self.clear_file_btn)
        controls.addStretch()
        controls.addWidget(self.theme_selector)
        controls.addWidget(self.auto_refresh_chk)
        controls.addWidget(self.dark_mode_chk)
        controls.addWidget(self.admin_mode_chk)

        main_layout.addLayout(controls)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # USB Activity tab
        self.usb_tab = QWidget()
        self.usb_layout = QVBoxLayout(self.usb_tab)
        # Collapsible details for USB
        self.usb_details_box = CollapsibleBox("USB Details")
        self.usb_details_label = QLabel("Rows: 0 | Last updated: -")
        self.usb_details_box.addWidget(self.usb_details_label)
        self.usb_layout.addWidget(self.usb_details_box)
        # USB search/filter bar
        usb_filter_layout = QHBoxLayout()
        self.usb_search_input = QLineEdit()
        self.usb_search_input.setPlaceholderText("Search USB logs (device, serial, username, event)")
        self.usb_event_filter = QComboBox()
        self.usb_event_filter.addItem("All")
        self.usb_user_filter = QComboBox()
        self.usb_user_filter.addItem("All")
        usb_filter_layout.addWidget(self.usb_search_input)
        usb_filter_layout.addWidget(self.usb_event_filter)
        usb_filter_layout.addWidget(self.usb_user_filter)
        self.usb_layout.addLayout(usb_filter_layout)

        self.usb_tree = QTreeWidget()
        self.usb_tree.setHeaderLabels(['ID', 'Event', 'Device', 'VID', 'PID', 'Serial', 'Username', 'Timestamp', 'Duration'])
        self.usb_layout.addWidget(self.usb_tree)
        self.tabs.addTab(self.usb_tab, "USB Activity")

        # File Activity tab
        self.file_tab = QWidget()
        self.file_layout = QVBoxLayout(self.file_tab)
        # Collapsible details for File activity
        self.file_details_box = CollapsibleBox("File Details")
        self.file_details_label = QLabel("Rows: 0 | Last updated: -")
        self.file_details_box.addWidget(self.file_details_label)
        self.file_layout.addWidget(self.file_details_box)
        # File search/filter bar
        file_filter_layout = QHBoxLayout()
        self.file_search_input = QLineEdit()
        self.file_search_input.setPlaceholderText("Search file logs (path, username, event)")
        self.file_event_filter = QComboBox()
        self.file_event_filter.addItem("All")
        self.file_risk_filter = QComboBox()
        self.file_risk_filter.addItem("All")
        self.file_user_filter = QComboBox()
        self.file_user_filter.addItem("All")
        file_filter_layout.addWidget(self.file_search_input)
        file_filter_layout.addWidget(self.file_event_filter)
        file_filter_layout.addWidget(self.file_risk_filter)
        file_filter_layout.addWidget(self.file_user_filter)
        self.file_layout.addLayout(file_filter_layout)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(['ID', 'Device ID', 'File Path', 'Event', 'Size', 'Risk', 'Username', 'Timestamp'])
        self.file_layout.addWidget(self.file_tree)
        self.tabs.addTab(self.file_tab, "File Activity")

        # Security tab
        self.security_tab = QWidget()
        self.security_layout = QVBoxLayout(self.security_tab)
        self.active_sessions_label = QLabel("Active Sessions: 0")
        self.unauthorized_summary_label = QLabel("Unauthorized Events: 0")
        self.security_layout.addWidget(self.active_sessions_label)
        self.security_layout.addWidget(self.unauthorized_summary_label)

        self.active_sessions_tree = QTreeWidget()
        self.active_sessions_tree.setHeaderLabels(['Device', 'Drive', 'User', 'Connected', 'Duration'])
        self.active_sessions_tree.setAlternatingRowColors(True)
        self.security_layout.addWidget(QLabel("Live USB Sessions"))
        self.security_layout.addWidget(self.active_sessions_tree)

        self.unauthorized_tree = QTreeWidget()
        self.unauthorized_tree.setHeaderLabels(['ID', 'Device', 'VID', 'PID', 'Serial', 'User', 'Timestamp'])
        self.unauthorized_tree.setAlternatingRowColors(True)
        self.security_layout.addWidget(QLabel("Recent Unauthorized USB Events"))
        self.security_layout.addWidget(self.unauthorized_tree)
        self.tabs.addTab(self.security_tab, "Security")

        # Admin Dashboard tab
        self.admin_tab = QWidget()
        self.admin_layout = QVBoxLayout(self.admin_tab)
        self.admin_title = QLabel("Admin Dashboard")
        self.admin_title.setObjectName('title')
        self.admin_layout.addWidget(self.admin_title)
        self.admin_overview_label = QLabel("Loading admin summary...")
        self.admin_overview_label.setWordWrap(True)
        self.admin_layout.addWidget(self.admin_overview_label)
        self.admin_total_usb_label = QLabel("")
        self.admin_total_usb_label.setWordWrap(True)
        self.admin_layout.addWidget(self.admin_total_usb_label)
        self.admin_total_file_label = QLabel("")
        self.admin_total_file_label.setWordWrap(True)
        self.admin_layout.addWidget(self.admin_total_file_label)
        self.admin_email_label = QLabel("")
        self.admin_email_label.setWordWrap(True)
        self.admin_layout.addWidget(self.admin_email_label)
        
        # SMTP Configuration fields for Admin Dashboard
        self.admin_layout.addWidget(QLabel("Enable email alerts"))
        self.admin_email_alerts_chk = QCheckBox("")
        self.admin_layout.addWidget(self.admin_email_alerts_chk)
        
        self.admin_layout.addWidget(QLabel("SMTP Host"))
        self.admin_smtp_host_input = QLineEdit()
        self.admin_smtp_host_input.setPlaceholderText("SMTP host")
        self.admin_layout.addWidget(self.admin_smtp_host_input)
        
        self.admin_layout.addWidget(QLabel("SMTP Port"))
        self.admin_smtp_port_input = QLineEdit()
        self.admin_smtp_port_input.setPlaceholderText("SMTP port")
        self.admin_layout.addWidget(self.admin_smtp_port_input)
        
        self.admin_layout.addWidget(QLabel("SMTP Username"))
        self.admin_smtp_username_input = QLineEdit()
        self.admin_smtp_username_input.setPlaceholderText("SMTP username")
        self.admin_layout.addWidget(self.admin_smtp_username_input)
        
        self.admin_layout.addWidget(QLabel("SMTP Password"))
        self.admin_smtp_password_input = QLineEdit()
        self.admin_smtp_password_input.setPlaceholderText("SMTP password")
        self.admin_smtp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_layout.addWidget(self.admin_smtp_password_input)
        
        self.admin_smtp_tls_chk = QCheckBox("Use TLS/STARTTLS")
        self.admin_layout.addWidget(self.admin_smtp_tls_chk)
        
        self.admin_layout.addWidget(QLabel("Sender Email"))
        self.admin_sender_input = QLineEdit()
        self.admin_sender_input.setPlaceholderText("Sender email address")
        self.admin_layout.addWidget(self.admin_sender_input)
        
        self.admin_layout.addWidget(QLabel("Recipients"))
        self.admin_recipients_input = QLineEdit()
        self.admin_recipients_input.setPlaceholderText("Recipient emails, comma-separated")
        self.admin_layout.addWidget(self.admin_recipients_input)
        self.admin_whitelist_label = QLabel("")
        self.admin_whitelist_label.setWordWrap(True)
        self.admin_layout.addWidget(self.admin_whitelist_label)
        self.admin_unauthorized_label = QLabel("")
        self.admin_unauthorized_label.setWordWrap(True)
        self.admin_layout.addWidget(self.admin_unauthorized_label)
        admin_button_layout = QHBoxLayout()
        self.open_whitelist_admin_btn = QPushButton("Open Whitelist File")
        self.refresh_admin_btn = QPushButton("Refresh Admin Panel")
        self.save_admin_email_btn = QPushButton("Save Email Settings")
        admin_button_layout.addWidget(self.open_whitelist_admin_btn)
        admin_button_layout.addWidget(self.refresh_admin_btn)
        admin_button_layout.addWidget(self.save_admin_email_btn)
        self.admin_layout.addLayout(admin_button_layout)
        self.admin_layout.addStretch()
        self.tabs.addTab(self.admin_tab, "Admin Dashboard")

        # Settings tab
        self.settings_tab = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_tab)

        self.whitelist_enabled_chk = QCheckBox("Enable whitelist enforcement")
        self.alert_on_unknown_chk = QCheckBox("Alert on unknown USB device")
        self.email_alerts_chk = QCheckBox("Enable email alerts")
        self.screenshot_capture_chk = QCheckBox("Capture screenshot on unauthorized insert")
        self.screenshot_dir_input = QLineEdit()
        self.screenshot_dir_input.setPlaceholderText("Screenshot save directory")
        self.smtp_host_input = QLineEdit()
        self.smtp_host_input.setPlaceholderText("SMTP host")
        self.smtp_port_input = QLineEdit()
        self.smtp_port_input.setPlaceholderText("SMTP port")
        self.smtp_username_input = QLineEdit()
        self.smtp_username_input.setPlaceholderText("SMTP username")
        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setPlaceholderText("SMTP password")
        self.smtp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.sender_input = QLineEdit()
        self.sender_input.setPlaceholderText("Sender email address")
        self.recipients_input = QLineEdit()
        self.recipients_input.setPlaceholderText("Recipient emails, comma-separated")
        self.smtp_tls_chk = QCheckBox("Use TLS/STARTTLS")
        self.test_email_btn = QPushButton("Send Test Email")
        self.open_whitelist_btn = QPushButton("Open whitelist file")
        self.save_settings_btn = QPushButton("Save Settings")

        self.settings_layout.addWidget(self.whitelist_enabled_chk)
        self.settings_layout.addWidget(self.alert_on_unknown_chk)
        self.settings_layout.addWidget(self.email_alerts_chk)
        self.settings_layout.addWidget(QLabel("SMTP Host"))
        self.settings_layout.addWidget(self.smtp_host_input)
        self.settings_layout.addWidget(QLabel("SMTP Port"))
        self.settings_layout.addWidget(self.smtp_port_input)
        self.settings_layout.addWidget(QLabel("SMTP Username"))
        self.settings_layout.addWidget(self.smtp_username_input)
        self.settings_layout.addWidget(QLabel("SMTP Password"))
        self.settings_layout.addWidget(self.smtp_password_input)
        self.settings_layout.addWidget(self.smtp_tls_chk)
        self.settings_layout.addWidget(QLabel("Sender Email"))
        self.settings_layout.addWidget(self.sender_input)
        self.settings_layout.addWidget(QLabel("Recipients"))
        self.settings_layout.addWidget(self.recipients_input)
        self.settings_layout.addWidget(self.test_email_btn)
        self.settings_layout.addWidget(self.screenshot_capture_chk)
        self.settings_layout.addWidget(QLabel("Screenshot directory"))
        self.settings_layout.addWidget(self.screenshot_dir_input)
        self.settings_layout.addWidget(self.open_whitelist_btn)
        self.settings_layout.addWidget(self.save_settings_btn)
        self.settings_layout.addStretch()
        self.tabs.addTab(self.settings_tab, "Settings")

        # Analytics tab
        self.analytics_tab = QWidget()
        self.analytics_layout = QVBoxLayout(self.analytics_tab)
        self.sessions_label = QLabel("Sessions Today: 0")
        self.file_events_label = QLabel("Total File Events: 0")
        self.large_transfers_label = QLabel("Large Transfers: 0")
        self.analytics_layout.addWidget(self.sessions_label)
        self.analytics_layout.addWidget(self.file_events_label)
        self.analytics_layout.addWidget(self.large_transfers_label)
        # Add plots if pyqtgraph is available
        if PYQTGRAPH_AVAILABLE:
            # Events over time (last 30 minutes)
            self.events_plot = PlotWidget(title="File Events Over Time (per minute)")
            self.events_plot.setBackground('w')
            self.events_plot.showGrid(x=True, y=True)
            self.analytics_layout.addWidget(self.events_plot)

            # Large transfers by user (bar chart)
            self.large_bar_plot = PlotWidget(title="Large Transfers by User")
            self.large_bar_plot.setBackground('w')
            self.analytics_layout.addWidget(self.large_bar_plot)
        else:
            note = QLabel("pyqtgraph not installed — install pyqtgraph for charts")
            self.analytics_layout.addWidget(note)

        self.analytics_layout.addStretch()
        self.tabs.addTab(self.analytics_tab, "Analytics")

        # Status bar
        self.status = self.statusBar()
        self.status.showMessage("Ready")

        # Connect signals
        self.refresh_usb_btn.clicked.connect(self.refresh_usb_logs)
        self.refresh_file_btn.clicked.connect(self.refresh_file_logs)
        self.export_btn.clicked.connect(self.export_logs)
        self.clear_usb_btn.clicked.connect(self.clear_usb_logs)
        self.clear_file_btn.clicked.connect(self.clear_file_logs)
        self.open_whitelist_btn.clicked.connect(self.open_whitelist_file)
        self.open_whitelist_admin_btn.clicked.connect(self.open_whitelist_file)
        self.refresh_admin_btn.clicked.connect(self.refresh_admin_dashboard)
        self.save_admin_email_btn.clicked.connect(self.save_admin_email_settings)
        self.save_settings_btn.clicked.connect(self.save_settings)
        self.test_email_btn.clicked.connect(self.send_test_email)
        self.email_alerts_chk.stateChanged.connect(self.toggle_email_controls)
        self.auto_refresh_chk.stateChanged.connect(self.toggle_auto_refresh)
        self.dark_mode_chk.stateChanged.connect(self.toggle_dark_mode)
        self.admin_mode_chk.stateChanged.connect(self.toggle_admin_mode)
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        # Search/filter signals
        try:
            self.usb_search_input.textChanged.connect(self.refresh_usb_logs)
            self.usb_event_filter.currentIndexChanged.connect(self.refresh_usb_logs)
            self.usb_user_filter.currentIndexChanged.connect(self.refresh_usb_logs)
            self.file_search_input.textChanged.connect(self.refresh_file_logs)
            self.file_event_filter.currentIndexChanged.connect(self.refresh_file_logs)
            self.file_risk_filter.currentIndexChanged.connect(self.refresh_file_logs)
            self.file_user_filter.currentIndexChanged.connect(self.refresh_file_logs)
        except Exception:
            pass

        # Timer for auto-refresh
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(self.refresh_interval_ms)

        # Visual polish: per-button colors and tree settings
        try:
            self.export_btn.setStyleSheet(f"background: {self.success}; color: white; border-radius:6px;")
            self.clear_usb_btn.setStyleSheet(f"background: {self.warn}; color: white; border-radius:6px;")
            self.clear_file_btn.setStyleSheet(f"background: {self.danger}; color: white; border-radius:6px;")
            self.refresh_usb_btn.setMinimumWidth(110)
            self.refresh_file_btn.setMinimumWidth(110)
            self.export_btn.setMinimumWidth(88)
            self.export_format_selector.setMinimumWidth(80)

            self.usb_tree.setAlternatingRowColors(True)
            self.file_tree.setAlternatingRowColors(True)
            self.usb_tree.setStyleSheet("QTreeWidget { font-size: 12px; }")
            self.file_tree.setStyleSheet("QTreeWidget { font-size: 12px; }")

            if PYQTGRAPH_AVAILABLE:
                # set polite background and axis colors for plots
                pg.setConfigOptions(background='w', foreground='#2c3e50')
        except Exception:
            pass

        # Initial load
        self.load_settings()
        self.populate_admin_input_fields()  # Populate admin input fields only on init
        self.refresh_all()

    def on_timer(self):
        if self.auto_refresh_chk.isChecked():
            self.refresh_all()
    def apply_theme(self, theme_name: str = 'Light'):
        """Apply a named theme using preset colors."""
        if theme_name not in self.theme_presets:
            theme_name = 'Light'
        theme = self.theme_presets[theme_name]
        self.current_theme = theme_name
        self.primary = theme['primary']
        self.accent = theme['accent']
        self.success = theme['success']
        self.warn = theme['warn']
        self.danger = theme['danger']
        self.bg = theme['bg']
        self.card = theme['card']
        input_bg = theme['input_bg']
        input_border = theme['input_border']
        header_bg = theme['header_bg']
        disabled_bg = theme.get('disabled_bg', '#e5e7eb')
        disabled_text = theme.get('disabled_text', '#9ca3af')
 
        ss = f"""
            QMainWindow {{ background: {self.bg}; color: {self.primary}; }}
            QWidget {{ background: {self.bg}; color: {self.primary}; font-family: Arial; }}
            QScrollArea {{ background: {self.bg}; }}
            QTabWidget::pane {{ border: 0; background: {self.bg}; }}
            QTabBar::tab {{ padding: 8px 14px; margin: 2px; border-radius: 6px; background: transparent; color: {self.primary}; }}
            QTabBar::tab:selected {{ background: {self.card}; border: 1px solid {input_border}; color: {self.primary}; }}
            QPushButton {{ background: {self.accent}; color: white; border: none; padding: 6px 10px; border-radius: 6px; }}
            QPushButton:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}
            QPushButton:pressed {{ background: #217dbb; }}
            QCheckBox {{ color: {self.primary}; }}
            QLineEdit, QComboBox {{ padding: 6px; border: 1px solid {input_border}; border-radius: 6px; background: {input_bg}; color: {self.primary}; }}
            QLineEdit:disabled, QComboBox:disabled {{ background: {disabled_bg}; color: {disabled_text}; border: 1px solid {disabled_bg}; }}
            QComboBox QAbstractItemView {{ background: {self.card}; color: {self.primary}; selection-background-color: {self.accent}; selection-color: white; }}
            QTreeWidget {{ background: {self.card}; border: 1px solid {input_border}; border-radius: 6px; color: {self.primary}; selection-background-color: {self.accent}; selection-color: white; }}
            QTreeWidget::item {{ background: {self.card}; color: {self.primary}; }}
            QHeaderView::section {{ background: {header_bg}; padding: 6px; border: none; color: {self.primary}; }}
            QLabel#title {{ color: {self.primary}; font-size: 16px; font-weight: bold; }}
            QStatusBar {{ background: {self.primary}; color: white; }}
            QToolButton {{ color: {self.primary}; font-weight: bold; }}
            QMenu {{ background: {self.card}; color: {self.primary}; }}
            QMenu::item:selected {{ background: {self.accent}; color: white; }}
        """""

        self.setStyleSheet(ss)
        if PYQTGRAPH_AVAILABLE:
            if theme_name == 'Dark':
                pg.setConfigOptions(background=self.card, foreground=self.primary)
            else:
                pg.setConfigOptions(background='w', foreground='#2c3e50')

    def toggle_dark_mode(self, state):
        theme_name = 'Dark' if state == QtCore.Qt.CheckState.Checked else 'Light'
        self.theme_selector.blockSignals(True)
        self.theme_selector.setCurrentText(theme_name)
        self.theme_selector.blockSignals(False)
        self.set_theme(theme_name)

    def toggle_admin_mode(self, state=None):
        # Keep the admin dashboard tab always visible, but refresh it when admin mode changes.
        self.refresh_admin_dashboard()

    def change_theme(self, theme_name):
        self.set_theme(theme_name)

    def set_theme(self, theme_name: str):
        self.apply_theme(theme_name)
        self.theme_selector.blockSignals(True)
        self.theme_selector.setCurrentText(self.current_theme)
        self.theme_selector.blockSignals(False)
        self.dark_mode_chk.blockSignals(True)
        self.dark_mode_chk.setChecked(self.current_theme == 'Dark')
        self.dark_mode_chk.blockSignals(False)
        self.save_theme_setting(self.current_theme)
        self.refresh_all()

    def load_theme_setting(self):
        try:
            if os.path.exists(self.THEME_CONFIG_PATH):
                with open(self.THEME_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    theme_name = data.get('theme', 'Light')
                    if theme_name in self.theme_presets:
                        return theme_name
        except Exception:
            pass
        return 'Light'

    def save_theme_setting(self, theme_name: str):
        try:
            with open(self.THEME_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump({'theme': theme_name}, f, indent=2)
        except Exception:
            pass

    def refresh_usb_logs(self):
        self.usb_tree.clear()
        logs = fetch_all_logs()
        # Prepare filters
        search_text = (self.usb_search_input.text() or '').strip().lower() if hasattr(self, 'usb_search_input') else ''
        event_filter = (self.usb_event_filter.currentText() if hasattr(self, 'usb_event_filter') else 'All')
        user_filter = (self.usb_user_filter.currentText() if hasattr(self, 'usb_user_filter') else 'All')

        # Populate event/user filter choices
        events_set = set()
        users_set = set()

        for log in logs:
            events_set.add(log[1] or '')
            users_set.add(log[11] or '')

        # Update combo boxes (keep current selection if possible)
        try:
            cur_event = self.usb_event_filter.currentText()
            self.usb_event_filter.blockSignals(True)
            self.usb_event_filter.clear()
            self.usb_event_filter.addItem('All')
            for e in sorted(events_set):
                if e:
                    self.usb_event_filter.addItem(e)
            idx = self.usb_event_filter.findText(cur_event) if cur_event else 0
            if idx >= 0:
                self.usb_event_filter.setCurrentIndex(idx)
            self.usb_event_filter.blockSignals(False)
        except Exception:
            pass

        try:
            cur_user = self.usb_user_filter.currentText()
            self.usb_user_filter.blockSignals(True)
            self.usb_user_filter.clear()
            self.usb_user_filter.addItem('All')
            for u in sorted(users_set):
                if u:
                    self.usb_user_filter.addItem(u)
            idx = self.usb_user_filter.findText(cur_user) if cur_user else 0
            if idx >= 0:
                self.usb_user_filter.setCurrentIndex(idx)
            self.usb_user_filter.blockSignals(False)
        except Exception:
            pass

        # Filter and add items
        for log in logs:
            event = log[1] or ''
            user = log[11] or ''
            searchable = ' '.join([str(x) for x in (log[2], log[6], event, user, log[7]) if x]).lower()

            if event_filter != 'All' and event != event_filter:
                continue
            if user_filter != 'All' and user != user_filter:
                continue
            if search_text and search_text not in searchable:
                continue

            duration_str = format_duration(log[10]) if log[10] else ''
            item = QTreeWidgetItem([
                str(log[0]),
                event,
                log[2] or '',
                log[4] or '',
                log[5] or '',
                log[6] or '',
                user,
                log[7] or '',
                duration_str
            ])
            self.usb_tree.addTopLevelItem(item)
        # Update details box
        try:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.usb_details_label.setText(f"Rows: {len(logs)} | Last updated: {now}")
        except Exception:
            pass
        return len(logs)

    def refresh_file_logs(self):
        self.file_tree.clear()
        logs = fetch_file_logs(limit=500)
        # Prepare filters
        search_text = (self.file_search_input.text() or '').strip().lower() if hasattr(self, 'file_search_input') else ''
        event_filter = (self.file_event_filter.currentText() if hasattr(self, 'file_event_filter') else 'All')
        risk_filter = (self.file_risk_filter.currentText() if hasattr(self, 'file_risk_filter') else 'All')
        user_filter = (self.file_user_filter.currentText() if hasattr(self, 'file_user_filter') else 'All')

        events_set = set()
        risks_set = set()
        users_set = set()
        for log in logs:
            events_set.add(log[3] or '')
            risks_set.add(log[7] or '')
            users_set.add(log[5] or '')

        try:
            cur_event = self.file_event_filter.currentText()
            self.file_event_filter.blockSignals(True)
            self.file_event_filter.clear()
            self.file_event_filter.addItem('All')
            for e in sorted(events_set):
                if e:
                    self.file_event_filter.addItem(e)
            idx = self.file_event_filter.findText(cur_event) if cur_event else 0
            if idx >= 0:
                self.file_event_filter.setCurrentIndex(idx)
            self.file_event_filter.blockSignals(False)
        except Exception:
            pass

        try:
            cur_risk = self.file_risk_filter.currentText()
            self.file_risk_filter.blockSignals(True)
            self.file_risk_filter.clear()
            self.file_risk_filter.addItem('All')
            for r in sorted(risks_set):
                if r:
                    self.file_risk_filter.addItem(r)
            idx = self.file_risk_filter.findText(cur_risk) if cur_risk else 0
            if idx >= 0:
                self.file_risk_filter.setCurrentIndex(idx)
            self.file_risk_filter.blockSignals(False)
        except Exception:
            pass

        try:
            cur_user = self.file_user_filter.currentText()
            self.file_user_filter.blockSignals(True)
            self.file_user_filter.clear()
            self.file_user_filter.addItem('All')
            for u in sorted(users_set):
                if u:
                    self.file_user_filter.addItem(u)
            idx = self.file_user_filter.findText(cur_user) if cur_user else 0
            if idx >= 0:
                self.file_user_filter.setCurrentIndex(idx)
            self.file_user_filter.blockSignals(False)
        except Exception:
            pass

        # Filter and add items
        for log in logs:
            event = log[3] or ''
            risk = log[7] or ''
            user = log[5] or ''
            searchable = ' '.join([str(x) for x in (log[2], event, user) if x]).lower()

            if event_filter != 'All' and event != event_filter:
                continue
            if risk_filter != 'All' and risk != risk_filter:
                continue
            if user_filter != 'All' and user != user_filter:
                continue
            if search_text and search_text not in searchable:
                continue

            size_str = format_file_size(log[4]) if log[4] else '0 B'
            device_id_short = (log[1][:20] + '...') if log[1] and len(log[1]) > 20 else (log[1] or '')
            item = QTreeWidgetItem([
                str(log[0]),
                device_id_short,
                log[2] or '',
                event,
                size_str,
                risk,
                user,
                log[6] or ''
            ])
            self.file_tree.addTopLevelItem(item)
        # Update details box
        try:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.file_details_label.setText(f"Rows: {len(logs)} | Last updated: {now}")
        except Exception:
            pass
        return len(logs)

    def refresh_analytics(self):
        sessions = count_sessions_today()
        file_events = count_total_file_events()
        large_transfers = count_large_transfers()
        self.sessions_label.setText(f"Sessions Today: {sessions}")
        self.file_events_label.setText(f"Total File Events: {file_events}")
        self.large_transfers_label.setText(f"Large Transfers: {large_transfers}")

        # Update plots
        if PYQTGRAPH_AVAILABLE:
            # Events over last 30 minutes bucketed per minute
            logs = fetch_file_logs(limit=1000)
            now = datetime.datetime.now()
            minutes = 30
            # initialize buckets
            times = [now - datetime.timedelta(minutes=i) for i in reversed(range(minutes))]
            labels = [t.strftime('%H:%M') for t in times]
            counts = [0] * minutes

            for log in logs:
                ts = log[6]  # timestamp string
                try:
                    t = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    continue
                delta = now - t
                if 0 <= delta.total_seconds() < minutes * 60:
                    idx = minutes - 1 - int(delta.total_seconds() // 60)
                    if 0 <= idx < minutes:
                        counts[idx] += 1

            # Plot line
            self.events_plot.clear()
            x = list(range(minutes))
            pen = pg.mkPen(color=(31, 119, 180), width=2)
            self.events_plot.plot(x, counts, pen=pen, symbol='o', symbolBrush=(31, 119, 180))
            self.events_plot.getAxis('bottom').setTicks([list(zip(x, labels))])

            # Large transfers by username
            # Aggregate file_logs where risk_flag = 'LARGE_TRANSFER'
            large_logs = [l for l in logs if len(l) > 7 and l[7] == 'LARGE_TRANSFER']
            by_user = {}
            for l in large_logs:
                user = l[5] or 'Unknown'
                by_user[user] = by_user.get(user, 0) + 1

            self.large_bar_plot.clear()
            if by_user:
                users = list(by_user.keys())
                vals = [by_user[u] for u in users]
                x2 = list(range(len(users)))
                bg = pg.BarGraphItem(x=x2, height=vals, width=0.6, brush=(200, 50, 50))
                self.large_bar_plot.addItem(bg)
                self.large_bar_plot.getAxis('bottom').setTicks([list(zip(x2, users))])
            else:
                # show empty message
                pass

    def refresh_admin_dashboard(self):
        """Refresh read-only display labels only (not input fields)."""
        config = get_app_config()
        email_config = config.get('email_alerts', {})
        enabled = email_config.get('enabled', False)
        sender = email_config.get('sender', 'N/A') or 'N/A'
        recipients = ', '.join(email_config.get('recipients', [])) or 'None'
        whitelist_enabled = config.get('whitelist_enabled', True)
        screenshot_enabled = config.get('capture_screenshots_on_unauthorized_insert', False)
        unauthorized_count = count_unauthorized_events()
        active_sessions = len(get_active_sessions())
        total_usb = len(fetch_all_logs())
        total_file = count_total_file_events()

        self.admin_overview_label.setText(
            f"Whitelist enforcement: {'Enabled' if whitelist_enabled else 'Disabled'}\n"
            f"Screenshot capture: {'Enabled' if screenshot_enabled else 'Disabled'}\n"
            f"Active sessions: {active_sessions}"
        )
        self.admin_total_usb_label.setText(f"Total USB events: {total_usb}")
        self.admin_total_file_label.setText(f"Total file events: {total_file}")
        self.admin_email_label.setText(
            f"Email Alerts: {'Enabled' if enabled else 'Disabled'}\n"
            f"Sender: {sender}\n"
            f"Recipients: {recipients}"
        )
        self.admin_whitelist_label.setText(f"Unauthorized events: {unauthorized_count}")
        self.admin_unauthorized_label.setText(f"SMTP server: {email_config.get('smtp_host', 'N/A')} | Port: {email_config.get('smtp_port', 587)}")

    def populate_admin_input_fields(self):
        """Populate input fields from config (called on load and after save only)."""
        config = get_app_config()
        email_config = config.get('email_alerts', {})
        sender = email_config.get('sender', '') or ''
        recipients = ', '.join(email_config.get('recipients', []))
        self.admin_sender_input.setText(sender)
        self.admin_recipients_input.setText(recipients)

    def save_admin_email_settings(self):
        config = get_app_config()
        email_config = config.get('email_alerts', {})
        email_config['sender'] = self.admin_sender_input.text().strip()
        recipients = [r.strip() for r in self.admin_recipients_input.text().split(',') if r.strip()]
        email_config['recipients'] = recipients
        config['email_alerts'] = email_config
        if save_app_config(config):
            QMessageBox.information(self, 'Saved', 'Email settings saved successfully.')
        else:
            QMessageBox.critical(self, 'Save Failed', 'Unable to save email settings.')
        self.refresh_admin_dashboard()
        self.populate_admin_input_fields()

    def refresh_security(self):
        sessions = get_active_sessions()
        self.active_sessions_tree.clear()
        now = datetime.datetime.now()
        for session in sessions.values():
            device_info = session.get('device_info', {})
            device_name = device_info.get('name', 'Unknown')
            drive = session.get('drive_letter') or 'N/A'
            user = session.get('username') or 'Unknown'
            connected = session.get('connect_time') or '-'
            duration = ''
            try:
                if connected and connected != '-':
                    delta = now - datetime.datetime.strptime(connected, '%Y-%m-%d %H:%M:%S')
                    duration = format_duration(int(delta.total_seconds()))
            except Exception:
                duration = ''

            item = QTreeWidgetItem([
                device_name,
                drive,
                user,
                connected,
                duration
            ])
            self.active_sessions_tree.addTopLevelItem(item)

        unauthorized_count = count_unauthorized_events()
        self.active_sessions_label.setText(f"Active Sessions: {len(sessions)}")
        self.unauthorized_summary_label.setText(f"Unauthorized Events: {unauthorized_count}")

        self.unauthorized_tree.clear()
        unauthorized_logs = fetch_unauthorized_logs(limit=20)
        for log in unauthorized_logs:
            item = QTreeWidgetItem([
                str(log[0]),
                log[2] or '',
                log[4] or '',
                log[5] or '',
                log[6] or '',
                log[11] or '',
                log[7] or ''
            ])
            self.unauthorized_tree.addTopLevelItem(item)

    def refresh_all(self):
        usb_count = self.refresh_usb_logs()
        file_count = self.refresh_file_logs()
        self.refresh_security()
        self.refresh_analytics()
        self.refresh_admin_dashboard()
        self.status.showMessage(f"Ready | USB Logs: {usb_count} | File Events: {file_count}")

    def load_settings(self):
        config = get_app_config()
        self.whitelist_enabled_chk.setChecked(config.get('whitelist_enabled', True))
        self.alert_on_unknown_chk.setChecked(config.get('alert_on_unknown_device', True))
        self.email_alerts_chk.setChecked(config.get('email_alerts', {}).get('enabled', False))
        self.smtp_host_input.setText(config.get('email_alerts', {}).get('smtp_host', ''))
        self.smtp_port_input.setText(str(config.get('email_alerts', {}).get('smtp_port', 587)))
        self.smtp_username_input.setText(config.get('email_alerts', {}).get('username', ''))
        self.smtp_password_input.setText(config.get('email_alerts', {}).get('password', ''))
        self.sender_input.setText(config.get('email_alerts', {}).get('sender', ''))
        self.recipients_input.setText(', '.join(config.get('email_alerts', {}).get('recipients', [])))
        self.screenshot_capture_chk.setChecked(config.get('capture_screenshots_on_unauthorized_insert', True))
        self.smtp_tls_chk.setChecked(config.get('email_alerts', {}).get('use_tls', True))
        self.admin_mode_chk.setChecked(config.get('admin_mode_enabled', False))
        screenshot_dir = config.get('screenshot_dir', os.path.join(os.path.dirname(__file__), 'screenshots'))
        self.screenshot_dir_input.setText(str(screenshot_dir))
        self.toggle_email_controls(self.email_alerts_chk.checkState())
        self.toggle_admin_mode()

    def refresh_settings(self):
        # Keep the settings panel reflecting current config.
        self.load_settings()

    def save_settings(self):
        config = get_app_config()
        config['whitelist_enabled'] = self.whitelist_enabled_chk.isChecked()
        config['alert_on_unknown_device'] = self.alert_on_unknown_chk.isChecked()
        config['capture_screenshots_on_unauthorized_insert'] = self.screenshot_capture_chk.isChecked()
        screenshot_dir = self.screenshot_dir_input.text().strip() or os.path.join(os.path.dirname(__file__), 'screenshots')
        try:
            os.makedirs(screenshot_dir, exist_ok=True)
        except Exception:
            pass
        config['screenshot_dir'] = screenshot_dir

        email_config = config.get('email_alerts', {})
        email_config['enabled'] = self.email_alerts_chk.isChecked()
        email_config['smtp_host'] = self.smtp_host_input.text().strip()
        try:
            email_config['smtp_port'] = int(self.smtp_port_input.text().strip() or 587)
        except ValueError:
            email_config['smtp_port'] = 587
        email_config['use_tls'] = self.smtp_tls_chk.isChecked()
        email_config['username'] = self.smtp_username_input.text().strip()
        email_config['password'] = self.smtp_password_input.text()
        email_config['sender'] = self.sender_input.text().strip()
        recipients = [r.strip() for r in self.recipients_input.text().split(',') if r.strip()]
        email_config['recipients'] = recipients
        config['email_alerts'] = email_config
        config['admin_mode_enabled'] = self.admin_mode_chk.isChecked()

        if save_app_config(config):
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        else:
            QMessageBox.critical(self, "Save Failed", "Unable to save settings. Please check file permissions.")

    def open_whitelist_file(self):
        try:
            if not os.path.exists(WHITELIST_PATH):
                with open(WHITELIST_PATH, 'w', encoding='utf-8') as f:
                    f.write('{\n  "whitelist_enabled": true,\n  "whitelisted_devices": []\n}')
            os.startfile(WHITELIST_PATH)
        except Exception as e:
            QMessageBox.critical(self, "Open Failed", f"Unable to open whitelist file:\n{e}")

    def toggle_email_controls(self, state=None):
        enabled = self.email_alerts_chk.isChecked()
        for widget in [
                self.smtp_host_input,
                self.smtp_port_input,
                self.smtp_username_input,
                self.smtp_password_input,
                self.smtp_tls_chk,
                self.sender_input,
                self.recipients_input,
                self.test_email_btn]:
            widget.setEnabled(enabled)

    def send_test_email(self):
        try:
            smtp_port = int(self.smtp_port_input.text().strip() or 587)
        except ValueError:
            smtp_port = 587

        smtp_host = self.smtp_host_input.text().strip()
        username = self.smtp_username_input.text().strip()
        password = self.smtp_password_input.text()

        # Validate host is not empty or the old placeholder
        if not smtp_host or smtp_host in ('smtp.example.com', 'SMTP host', ''):
            QMessageBox.warning(
                self, "Test Email",
                "SMTP Host is not set correctly.\n\n"
                "For Gmail, use:  smtp.gmail.com\n"
                "For Outlook, use:  smtp.office365.com\n\n"
                "Please update the SMTP Host field and try again."
            )
            return

        if not username:
            QMessageBox.warning(self, "Test Email", "Please enter your SMTP Username (your email address).")
            return

        if not password:
            QMessageBox.warning(self, "Test Email",
                "Please enter your SMTP Password.\n\n"
                "If using Gmail, you need an App Password.\n"
                "Go to: myaccount.google.com → Security → App Passwords"
            )
            return

        recipients = [r.strip() for r in self.recipients_input.text().split(',') if r.strip()]
        if not recipients:
            QMessageBox.warning(self, "Test Email", "Please specify at least one recipient email address.")
            return

        email_settings = {
            'smtp_host': smtp_host,
            'smtp_port': smtp_port,
            'use_tls': self.smtp_tls_chk.isChecked(),
            'username': username,
            'password': password,
            'sender': self.sender_input.text().strip() or username
        }

        subject = "USB Logger Test Email"
        body = (
            "This is a test email from the USB Logger application.\n\n"
            "If you received this message, your SMTP settings are working correctly."
        )

        # Disable button and show progress during send
        self.test_email_btn.setEnabled(False)
        self.test_email_btn.setText("Sending...")

        def do_send():
            errors = []
            success = send_email_notification(subject, body, recipients, email_settings, error_out=errors)
            # Schedule result callback on main thread
            QtCore.QMetaObject.invokeMethod(
                self, '_on_test_email_done',
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(bool, success),
                QtCore.Q_ARG(str, errors[0] if errors else '')
            )

        import threading
        t = threading.Thread(target=do_send, daemon=True)
        t.start()

    @QtCore.pyqtSlot(bool, str)
    def _on_test_email_done(self, success, error_msg):
        self.test_email_btn.setEnabled(True)
        self.test_email_btn.setText("Send Test Email")
        if success:
            QMessageBox.information(self, "Test Email", "Test email sent successfully!\n\nCheck your inbox.")
        else:
            QMessageBox.critical(
                self, "Test Email",
                f"Unable to send test email.\n\nError:\n{error_msg}\n\n"
                "Troubleshooting tips:\n"
                "• For Gmail: Use an App Password, not your normal password.\n"
                "  Go to: myaccount.google.com → Security → App Passwords\n"
                "• Make sure 2-Step Verification is enabled on your Google account.\n"
                "• Check your internet connection."
            )

    def toggle_auto_refresh(self, state):
        self.auto_refresh = (state == QtCore.Qt.CheckState.Checked)

    def export_logs(self):
        export_format = self.export_format_selector.currentText()
        if export_format == 'JSON':
            success, message, filepath = export_to_json()
        else:
            success, message, filepath = export_to_csv()

        if success:
            QMessageBox.information(self, "Export Successful", f"{message}\nSaved to:\n{filepath}")
        else:
            QMessageBox.critical(self, "Export Failed", message)

    def clear_usb_logs(self):
        resp = QMessageBox.question(self, "Confirm Clear", "Delete ALL USB logs? This cannot be undone.")
        if resp == QMessageBox.StandardButton.Yes:
            ok = clear_all_logs()
            if ok:
                self.refresh_all()

    def clear_file_logs(self):
        resp = QMessageBox.question(self, "Confirm Clear", "Delete ALL file logs? This cannot be undone.")
        if resp == QMessageBox.StandardButton.Yes:
            ok = clear_file_logs()
            if ok:
                self.refresh_all()

    def show_large_transfer_alert(self, file_path, file_size_mb, username, event_type, risk_flag='LARGE_TRANSFER'):
        # Simple Qt alert mirroring tkinter behavior
        filename = file_path.split('/')[-1]
        title = "SECURITY ALERT" if risk_flag == 'LARGE_TRANSFER' else "SUSPICIOUS FILE"
        msg = f"File: {filename}\nFull Path: {file_path}\nSize: {file_size_mb:.2f} MB\nEvent: {event_type}\nUser: {username}\nTime: {get_timestamp()}\nRisk: {risk_flag}"
        QMessageBox.warning(self, title, msg)

    def show_unauthorized_device_alert(self, device_info, username, timestamp):
        device_name = device_info.get('name', 'Unknown Device')
        vid = device_info.get('vid', 'N/A')
        pid = device_info.get('pid', 'N/A')
        serial = device_info.get('serial', 'N/A')
        msg = (
            f"Unauthorized USB device detected:\n\n"
            f"Device: {device_name}\n"
            f"VID: {vid}\n"
            f"PID: {pid}\n"
            f"Serial: {serial}\n"
            f"User: {username}\n"
            f"Time: {timestamp}\n\n"
            "Please review the whitelist configuration if this device is trusted."
        )
        QMessageBox.warning(self, "Unauthorized USB Alert", msg)


def launch_gui():
    """Create QApplication and run the Qt GUI. This function mirrors the Tkinter `launch_gui` API.
    """
    # Ensure QApplication exists only once
    app = QApplication.instance() or QApplication(sys.argv)
    window = USBLoggerQt()

    # Hook file alert callback if monitor is available
    try:
        from monitor import set_file_alert_callback, set_usb_alert_callback
        set_file_alert_callback(window.show_large_transfer_alert)
        set_usb_alert_callback(window.show_unauthorized_device_alert)
    except Exception:
        pass

    window.show()
    app.exec()


if __name__ == '__main__':
    launch_gui()
