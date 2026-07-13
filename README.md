# 🔌 Real Time USB Activity Logger with GUI Dashboard

## 📋 Project Overview

A Windows-based Real Time USB Activity Logger that monitors, logs, and displays USB device insertion and removal events in real-time. Built with Python, this application demonstrates system-level monitoring, database management, GUI development, and multi-threaded programming.

**Academic Project Status:** 60-70% Complete (Fully Functional Core Features)

---

## 🎯 Key Features

✅ **Real-time USB Detection**
- Detects USB device insertion
- Detects USB device removal
- Extracts detailed device information (VID, PID, Serial Number)

✅ **Database Logging**
- SQLite database for persistent storage
- Secure parameterized queries
- Complete event history

✅ **GUI Dashboard**
- Professional Tkinter + modern PyQt6 interface
- Color-coded event display
- Auto-refresh capability
- Scrollable table view
- Security dashboard for active sessions and unauthorized USB alerts

✅ **Data Export**
- Export logs to CSV or JSON format
- Timestamped filenames
- Excel/Sheets compatible

✅ **Modular Architecture**
- Clean separation of concerns
- Easy to understand and extend
- Well-commented for academic presentation

✅ **Optional Security Feature**
- Device whitelist support
- Unauthorized device alerts
- Email notification support for high-risk events
- Screenshot capture on unauthorized USB insertion
- Configurable via JSON

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Real Time USB Activity Logger                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   main.py    │────▶│  monitor.py  │────▶│  database.py │
│ (Entry Point)│     │ (USB Events) │     │  (Storage)   │
└──────────────┘     └──────────────┘     └──────────────┘
       │                     │                     │
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    gui.py    │────▶│   export.py  │     │   utils.py   │
│ (Dashboard)  │     │ (CSV Export) │     │  (Helpers)   │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │
       ▼
┌──────────────┐
│whitelist.json│
│  (Security)  │
└──────────────┘

DATA FLOW:
1. WMI detects USB event → monitor.py
2. Parse device details → utils.py
3. Store in database → database.py
4. Display in GUI → gui.py
5. Export to CSV/JSON → export.py
```

---

## 📁 Project Structure

```
usb_logger/
│
├── main.py              # Application entry point
├── monitor.py           # USB monitoring engine (WMI)
├── database.py          # SQLite database operations
├── gui.py               # Tkinter GUI dashboard
├── gui_qt.py            # Modern PyQt6 dashboard
├── export.py            # CSV/JSON export functionality
├── utils.py             # Helper functions (parsing, validation)
├── config.py            # Application configuration loader
├── whitelist.json       # Security whitelist configuration
├── app_config.json      # User settings and alert configuration
├── usb_logs.db          # SQLite database (auto-created)
└── README.md            # This file
```

---

## 🛠️ Technologies Used

| Technology | Purpose | Why Used |
|------------|---------|----------|
| **Python 3.x** | Core language | Cross-platform, easy to learn, rich libraries |
| **WMI** | USB detection | Windows Management Instrumentation for hardware events |
| **SQLite** | Database | Lightweight, serverless, no installation required |
| **Tkinter** | GUI | Built-in Python GUI library, no extra dependencies |
| **Threading** | Concurrency | Prevents GUI freezing during monitoring |
| **CSV** | Export format | Universal data format, Excel compatible |

| **PyQt6 / pyqtgraph (optional)** | Modern GUI + Charts | Provides a more polished UI and fast plotting for analytics |

---

## 📦 Dependencies

Install required Python packages:

```bash
pip install pywin32 wmi
```

**Note:** Tkinter and SQLite are included with standard Python installation.

If you want the modern PyQt6 UI and charts, install the full requirements:

```powershell
pip install -r requirements.txt
```

The `requirements.txt` includes `PyQt6` and `pyqtgraph` for the new GUI (`gui_qt.py`). If those are not installed the application will fall back to the original Tkinter UI.

The new GUI also includes a theme selector and dark mode toggle. The selected theme is saved automatically and restored on the next launch.

---

## 🚀 How to Run

### Step 1: Install Dependencies
```bash
pip install pywin32 wmi
```

### Step 2: Run the Application
```bash
python main.py
```

### Step 3: Use the Dashboard
- The GUI will open automatically
- USB monitoring starts in the background
- Insert/remove USB devices to see logs
- Use buttons to refresh, export, or clear logs

---

## 💡 How It Works

### 1. **USB Detection (monitor.py)**
- Uses **WMI (Windows Management Instrumentation)** to access system hardware events
- Polls for USB device changes every 2 seconds
- Compares current devices with previous state
- Detects insertions and removals

### 2. **Device Information Extraction (utils.py)**
- Parses Windows Device ID string
- Extracts **VID** (Vendor ID) - identifies manufacturer
- Extracts **PID** (Product ID) - identifies specific product
- Extracts **Serial Number** - unique device identifier

Example Device ID:
```
USB\VID_0781&PID_5567\4C530001234567890123
     ^^^^      ^^^^   ^^^^^^^^^^^^^^^^^^^^
     VID       PID    Serial Number
```

### 3. **Database Storage (database.py)**
- **SQLite** stores all events persistently
- Uses **parameterized queries** to prevent SQL injection
- Schema includes: ID, Event Type, Device Name, VID, PID, Serial, Timestamp

### 4. **GUI Display (gui.py)**
- **Tkinter Treeview** widget displays logs in table format
- **Color coding**: Green for CONNECTED, Red for DISCONNECTED
- **Auto-refresh** updates display every 3 seconds
- **Responsive design** with scrollbars

### 5. **Threading (main.py)**
- **Main thread**: Runs GUI (must not be blocked)
- **Background thread**: Runs USB monitoring continuously
- **Daemon thread**: Automatically stops when GUI closes

---

## 📊 Database Schema

```sql
CREATE TABLE usb_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,           -- 'CONNECTED' or 'DISCONNECTED'
    device_name TEXT,                   -- Human-readable name
    device_id TEXT,                     -- Full Windows device ID
    vendor_id TEXT,                     -- VID (4 hex chars)
    product_id TEXT,                    -- PID (4 hex chars)
    serial_number TEXT,                 -- Unique serial
    timestamp TEXT NOT NULL             -- Event time
);
```

---

## 🔐 Security Feature (Optional)

### Whitelist Configuration

Edit `whitelist.json` to enable device authorization:

```json
{
  "whitelist_enabled": true,
  "alert_on_unauthorized": true,
  "whitelist": [
    {
      "vendor_id": "0781",
      "product_id": "5567",
      "description": "SanDisk USB Drive",
      "authorized": true
    }
  ]
}
```

**Note:** This feature is implemented at basic level for demonstration. Full implementation would require additional monitoring logic.

---

##  Known Limitations

1. **Windows Only**: Requires WMI (Windows Management Instrumentation)
2. **Polling-based**: Checks every 2 seconds (not instant detection)
3. **Basic Whitelist**: Security feature is demonstrative, not enforced
4. **No Encryption**: Database is not encrypted
5. **Local Only**: No network/remote monitoring capability

---

## 📝 Testing Checklist

- [x] Database initialization
- [x] USB insertion detection
- [x] USB removal detection
- [x] VID/PID/Serial extraction
- [x] GUI display
- [x] Auto-refresh
- [x] CSV export
- [x] Clear logs function
- [x] Thread management
- [x] Error handling
- [ ] Whitelist enforcement (basic implementation only)
- [ ] Performance under heavy load
- [ ] Multi-device simultaneous events

---

##  References

- [Python WMI Documentation](https://pypi.org/project/WMI/)
- [SQLite Python Tutorial](https://docs.python.org/3/library/sqlite3.html)
- [Tkinter GUI Programming](https://docs.python.org/3/library/tkinter.html)
- [USB Device ID Format](https://docs.microsoft.com/en-us/windows-hardware/drivers/install/device-identification-strings)

---

