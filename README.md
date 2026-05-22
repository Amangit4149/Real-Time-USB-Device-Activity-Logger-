# 🔌 USB Device Activity Logger with GUI Dashboard

## 📋 Project Overview

A Windows-based USB Device Activity Logger that monitors, logs, and displays USB device insertion and removal events in real-time. Built with Python, this application demonstrates system-level monitoring, database management, GUI development, and multi-threaded programming.

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
- Professional Tkinter interface
- Color-coded event display
- Auto-refresh capability
- Scrollable table view

✅ **Data Export**
- Export logs to CSV format
- Timestamped filenames
- Excel/Sheets compatible

✅ **Modular Architecture**
- Clean separation of concerns
- Easy to understand and extend
- Well-commented for academic presentation

✅ **Optional Security Feature**
- Device whitelist support
- Unauthorized device alerts
- Configurable via JSON

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USB ACTIVITY LOGGER                      │
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
5. Export to CSV → export.py
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
├── export.py            # CSV export functionality
├── utils.py             # Helper functions (parsing, validation)
├── whitelist.json       # Security whitelist configuration
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

---

## 📦 Dependencies

Install required Python packages:

```bash
pip install pywin32 wmi
```

**Note:** Tkinter and SQLite are included with standard Python installation.

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

## 🎓 Academic Demonstration Points

### For Viva/Presentation:

1. **Why WMI?**
   - Windows API for system management
   - Real-time hardware event detection
   - No admin privileges required for reading

2. **Why SQLite?**
   - Serverless (no separate database process)
   - ACID compliant (reliable)
   - Perfect for desktop applications

3. **Why Threading?**
   - GUI runs in main thread (Tkinter requirement)
   - Monitoring runs in background thread
   - Prevents GUI freezing during continuous monitoring

4. **Security Considerations:**
   - Parameterized SQL queries prevent injection
   - Input sanitization in utils.py
   - Optional whitelist for authorized devices

5. **Modular Design Benefits:**
   - Easy to test individual components
   - Easy to extend functionality
   - Clear separation of concerns
   - Maintainable codebase

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

## 📈 Future Improvements

### Phase 2 Enhancements (30-40% remaining):

1. **Advanced Security**
   - Full whitelist enforcement
   - Real-time unauthorized device blocking
   - Email/SMS alerts for security events
   - Device fingerprinting

2. **Enhanced Analytics**
   - Usage statistics and charts
   - Device usage patterns
   - Most frequently used devices
   - Time-based analysis

3. **Reporting**
   - PDF report generation
   - Scheduled reports
   - Custom date range filtering
   - Visual charts and graphs

4. **User Management**
   - Multi-user support
   - Role-based access control
   - Audit logs for admin actions

5. **Network Features**
   - Remote monitoring
   - Centralized logging server
   - Multi-machine deployment

6. **Performance**
   - Event-driven detection (instead of polling)
   - Database indexing
   - Caching frequently accessed data

---

## 🐛 Known Limitations

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

## 👨‍💻 Developer Notes

### Code Style
- Clear, descriptive variable names
- Comprehensive inline comments
- Docstrings for all functions
- Error handling with try-except blocks

### Debugging
- Print statements show execution flow
- Status messages in GUI status bar
- Console output for monitoring events

### Extending the Project
1. Add new columns to database: Modify `database.py` schema
2. Add new GUI features: Edit `gui.py` class methods
3. Change monitoring interval: Modify `time.sleep(2)` in `monitor.py`
4. Add filters: Extend `export.py` filtering functions

---

## 📚 References

- [Python WMI Documentation](https://pypi.org/project/WMI/)
- [SQLite Python Tutorial](https://docs.python.org/3/library/sqlite3.html)
- [Tkinter GUI Programming](https://docs.python.org/3/library/tkinter.html)
- [USB Device ID Format](https://docs.microsoft.com/en-us/windows-hardware/drivers/install/device-identification-strings)

---

## 📄 License

This is an academic project for educational purposes.

---

## 👤 Author

**Academic Project**  
USB Device Activity Logger  
Windows Desktop Application  

---

## 🎯 Project Completion Status

**Current: 60-70% Complete**

✅ **Completed:**
- Core monitoring functionality
- Database operations
- GUI dashboard
- CSV export
- Basic architecture
- Documentation

⏳ **Remaining for 100%:**
- Full whitelist enforcement
- Advanced analytics
- Performance optimization
- Comprehensive testing
- Network features

---

**Perfect for academic demonstration and learning system programming concepts!**
