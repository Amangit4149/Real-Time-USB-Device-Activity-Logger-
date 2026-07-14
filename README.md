# 🔌 USB-Sentry: Real-Time USB Activity Logger & Security Guard

## 📋 Project Overview

**USB-Sentry** is a Windows-based USB activity monitoring and security framework designed to track, log, and display USB device insertion/removal events in real-time. Built with Python, this application integrates system-level hardware hookups, secure database management, multi-threaded background processing, and a high-performance PyQt6 user dashboard.

**Academic Project Status:** Fully Functional Production-Ready Core Features & Advanced Security Suite.

---

## 🎯 Key Features

✅ **Real-time USB Monitoring**
- Detects USB device insertion & removal within 2 seconds.
- Automatically extracts Vendor ID (VID), Product ID (PID), and Serial Number.
- Identifies current Windows username and mounts corresponding drive letters.

✅ **Persistent Database Logging**
- SQLite database backend to store logs safely.
- Parameterized SQL queries to block insertion exploits.
- Complete audit history of USB sessions, connection durations, and file events.

✅ **High-Performance GUI Dashboard**
- Modern PyQt6 desktop client with multiple customizable stylesheets (Light, Dark, Ocean, Professional).
- High-rate auto-refresh display backed by asynchronous thread-safe Qt Signal/Slot communication (eliminating app freezing).
- Integrated analytics charting using `pyqtgraph`.
- Real-time active connection tracker and unauthorized security event logs.

✅ **File Activity Monitor (Watchdog)**
- Monitored USB drive operations (creation, modification, and deletion).
- Automatically checks for suspicious extensions (`.exe`, `.bat`, `.vbs`, etc.) and flags large files (>50MB).

✅ **Advanced Automated Security & Alerts**
- **Always-ON Email Alerts**: Ensures notification settings are permanently active for guaranteed host visibility.
- **Auto Screenshot-Attached Emails**: In the event of unauthorized insertions or suspicious transfers, USB-Sentry instantly captures a screenshot of the system state and automatically emails it as an attachment to the system administrator—completely bypassing blocking alerts so the security notice arrives instantly.
- **Strict Device Whitelisting**: Allows trusted hardware devices while rejecting unknown units.

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USB-Sentry                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   main.py    │────▶│  monitor.py  │────▶│  database.py │
│ (Entry Point)│     │ (USB Events) │     │  (Storage)   │
└──────────────┘     └──────────────┘     └──────────────┘
       │                     │                     │
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  gui_qt.py   │────▶│   export.py  │     │   utils.py   │
│ (PyQt6 UI)   │     │ (Data Export)│     │  (Helpers)   │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │
       ▼
┌──────────────┐
│whitelist.json│
│ (Permissions)│
└──────────────┘

DATA FLOW:
1. WMI detects USB hardware connection/disconnection event → monitor.py
2. Device parameters parsed and validated → utils.py
3. Active mount drive mapped and watchdog file listener started → file_monitor.py
4. Events saved securely to database → database.py
5. PyQt6 UI notified thread-safely via Qt Signals to update views → gui_qt.py
6. Instant screenshot taken & admin alert email dispatched in background → utils.py
```

---

## 📁 Project Structure

```
usb_logger/
│
├── main.py              # Application entry point & thread coordinator
├── monitor.py           # USB monitoring engine (WMI hardware scanner)
├── file_monitor.py      # USB File operation watcher (Watchdog implementation)
├── database.py          # SQLite database CRUD operations & schema
├── gui.py               # Legacy Tkinter GUI dashboard
├── gui_qt.py            # High-performance PyQt6 dashboard with analytics
├── export.py            # CSV/JSON logger export engine
├── utils.py             # Helper tools (email, screenshot, parser, sizing)
├── config.py            # Global application configuration manager
├── whitelist.json       # Whitelist configuration file
├── app_config.json      # Security policies and SMTP email settings
├── usb_logs.db          # SQLite database (generated automatically)
└── README.md            # Project documentation (This file)
```

---

## 🛠️ Technologies Used

| Technology | Purpose | Why Used |
|------------|---------|----------|
| **Python 3.x** | Implementation Language | Platform-friendly scripting, rich library ecosystem |
| **WMI** | Hardware Detection | Interfaces with Windows Management Instrumentation for device updates |
| **Watchdog** | File Monitoring | Event-driven tracking of file systems (no CPU-heavy polling) |
| **SQLite** | Local Database | Embedded database requiring zero external server configuration |
| **PyQt6** | Modern Interface | Fast, high-fidelity native widgets, styling, and charts |
| **Pillow (PIL)** | Security Captures | Performs automated desktop screen grabs during threat triggers |
| **SMTP / SSL** | Instant Messaging | Direct SMTP client for sending TLS/STARTTLS encrypted alert emails |

---

## 📦 Dependencies

Install the core dependencies:

```bash
pip install pywin32 wmi watchdog Pillow
```

For the full dashboard experience (including theme switches, custom stylesheets, and charts), run:

```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

### Step 1: Configure SMTP Mail Settings
Before running, customize email settings in the **Settings** tab of the dashboard (or directly modify `app_config.json`):
- **SMTP Host**: e.g., `smtp.gmail.com`
- **SMTP Port**: `587` or `465`
- **Username / Password**: Your email and credentials (use an App Password for Gmail)
- **Recipients**: Commas-separated email addresses to notify

### Step 2: Launch the App
Run the quickstart batch script or execution script:
```bash
start.bat
```
Or manually:
```bash
python main.py
```

### Step 3: Insert a USB Drive
- Plug in any USB stick.
- If it is unauthorized, a screenshot is instantly snapped and emailed to the configured recipient.
- The UI will update instantly without lagging, using safe Qt Signals.

---

## 💡 How It Works

### 1. **Thread-Safe UI Operations**
Older versions had lags because background tasks invoked GUI popups directly. USB-Sentry handles all communications between the monitor threads and UI using custom `pyqtSignal` events (`large_transfer_alert_signal` and `unauthorized_device_alert_signal`). The background thread triggers the signal, and the main thread renders the prompt, ensuring **100% UI responsiveness (no "Not Responding" hangs)**.

### 2. **Automated Threat Alert Flow**
When a threat is detected (unauthorized USB, suspicious script `.exe`/`.bat`/`.vbs`, or large file transfer > 50MB):
1. **Pillow** takes an instant snapshot of the screen.
2. **SMTP Client** compiles a security report, attaches the screenshot, and pushes it to the server in a background thread.
3. The UI warning dialog pops up on screen *after* the email process starts, preventing any lockups from delaying the alert.

### 3. **Hardware Descriptor Parsing**
Parsing reads the system PNP Device ID string to parse parameters:
```
USB\VID_0781&PID_5567\4C530001234567890123
     ^^^^      ^^^^   ^^^^^^^^^^^^^^^^^^^^
     VID       PID    Serial Number
```

---

## 📊 Database Schema

```sql
-- USB Hardware Logs
CREATE TABLE usb_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,           -- 'CONNECTED', 'DISCONNECTED', 'UNAUTHORIZED'
    device_name TEXT,                   -- Hardware description
    device_id TEXT,                     -- Full hardware PNP string
    vendor_id TEXT,                     -- VID
    product_id TEXT,                    -- PID
    serial_number TEXT,                 -- Serial
    timestamp TEXT NOT NULL,            -- Log date
    connect_time TEXT,
    disconnect_time TEXT,
    usage_duration INTEGER,             -- Connection time in seconds
    username TEXT                       -- Logged in OS user
);

-- USB File Activity Logs
CREATE TABLE file_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    event_type TEXT NOT NULL,           -- 'CREATED', 'DELETED', 'MODIFIED', 'FOUND_ON_SCAN'
    file_size INTEGER,                  -- Bytes
    username TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    risk_flag TEXT NOT NULL             -- 'NORMAL', 'SUSPICIOUS_FILE', 'LARGE_TRANSFER'
);
```

---

## 📝 Testing Checklist

- [x] Database automatic migration (Phase 2 schema support)
- [x] Live USB plug & unplug monitoring (WMI)
- [x] Auto-mounting drive detection and file Watchdog assignment
- [x] Thread-safe signal-slot alert delivery (no UI freeze)
- [x] Automated Pillow screen grabbing
- [x] Background SMTP mail notification with attachment encoding
- [x] Whitelist checking and block logs
- [x] Theme setting persistence (app_config / theme_config)
- [x] CSV and JSON logging export

---

## 🔗 References
- [PyQt6 Framework Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Watchdog System Event Library](https://pypi.org/project/watchdog/)
- [Pillow Image Manipulation](https://python-pillow.org/)
- [Windows WMI hardware specs](https://learn.microsoft.com/en-us/windows/win32/wmisdk/wmi-start-page)
