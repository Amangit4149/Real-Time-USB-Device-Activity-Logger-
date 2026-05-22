# 🚀 Quick Setup Guide - Real Time USB Activity Logger

## ⚡ Fast Track Installation (5 minutes)

### Prerequisites
- Windows 10/11
- Python 3.7 or higher
- Internet connection (for installing dependencies)

---

## 📥 Step-by-Step Installation

### Step 1: Verify Python Installation
Open Command Prompt and run:
```bash
python --version
```

**Expected output:** `Python 3.x.x`

**If Python is not installed:**
1. Download from: https://www.python.org/downloads/
2. ✅ **IMPORTANT:** Check "Add Python to PATH" during installation
3. Restart Command Prompt after installation

---

### Step 2: Navigate to Project Directory
```bash
cd "C:\Users\Abhinav Singh\Desktop\clgprjct\usb_logger"
```

---

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**This installs:**
- `pywin32` - Windows API access
- `WMI` - Windows Management Instrumentation

**Installation time:** ~1-2 minutes

---

### Step 4: Run Test Suite (Optional but Recommended)
```bash
python test_suite.py
```

**This verifies:**
- All modules are working
- Dependencies are installed correctly
- Database operations function properly
- USB detection is operational

**Expected result:** All tests should pass ✅

---

### Step 5: Launch the Application

**Option A: Using Batch File (Easiest)**
```bash
start.bat
```

**Option B: Using Python Directly**
```bash
python main.py
```

---

## ✅ Verification Checklist

After launching, you should see:

1. ✅ Console messages:
   ```
   ==================================================
   Real Time USB Activity Logger - INITIALIZATION
   ==================================================
   
   [1/2] Initializing database...
   [✓] Database initialized successfully
   
   [2/2] Starting USB monitoring...
   [✓] USB monitoring started
   
   ==================================================
   ✓ INITIALIZATION COMPLETE
   ==================================================
   
   [✓] Launching GUI...
   ```

2. ✅ GUI window opens with:
   - Title: "🔌 Real Time USB Activity Logger"
   - Buttons: Refresh, Export, Clear, Exit
   - Empty table (if no USB events yet)
   - Status bar showing "Ready | Total Logs: 0"

3. ✅ Database file created:
   - Check for `usb_logs.db` in the project folder

---

## 🧪 Testing the Application

### Test 1: USB Insertion Detection
1. Plug in a USB device (flash drive, mouse, keyboard, etc.)
2. Wait 2-3 seconds
3. Check GUI - should show new "CONNECTED" entry (green background)
4. Verify VID, PID, and Serial Number are displayed

### Test 2: USB Removal Detection
1. Unplug the USB device
2. Wait 2-3 seconds
3. Check GUI - should show new "DISCONNECTED" entry (red background)

### Test 3: CSV Export
1. Click "📤 Export to CSV" button
2. Success message should appear
3. Check project folder for `usb_logs_YYYYMMDD_HHMMSS.csv`
4. Open CSV file - should contain all logged events

### Test 4: Auto-Refresh
1. Uncheck "Auto-Refresh" checkbox
2. Plug/unplug USB device
3. Table should NOT update automatically
4. Click "🔄 Refresh Logs" button
5. Table should now show new events

### Test 5: Clear Logs
1. Click "🗑️ Clear Logs" button
2. Confirm deletion
3. Table should be empty
4. Status bar should show "Total Logs: 0"

---

## 🐛 Troubleshooting

### Problem: "Python is not recognized"
**Solution:** 
- Python is not in PATH
- Reinstall Python with "Add to PATH" checked
- OR manually add Python to PATH

### Problem: "No module named 'wmi'"
**Solution:**
```bash
pip install WMI pywin32
```

### Problem: "ImportError: No module named 'tkinter'"
**Solution:**
- Tkinter should be included with Python
- If missing, reinstall Python with "tcl/tk and IDLE" checked

### Problem: GUI doesn't open
**Solution:**
- Check console for error messages
- Run test suite: `python test_suite.py`
- Verify all dependencies are installed

### Problem: USB devices not detected
**Solution:**
- Ensure you're running on Windows
- Check if WMI service is running:
  ```bash
  sc query winmgmt
  ```
- Try running as Administrator (right-click → Run as administrator)

### Problem: Database errors
**Solution:**
- Delete `usb_logs.db` file
- Restart application (will recreate database)

### Problem: "Access Denied" errors
**Solution:**
- Some USB devices may be protected
- This is normal - the app will skip those devices
- Most standard USB devices should work fine

---

## 📂 File Structure After Setup

```
usb_logger/
│
├── main.py              ✅ Main application
├── monitor.py           ✅ USB monitoring engine
├── database.py          ✅ Database operations
├── gui.py               ✅ GUI dashboard
├── export.py            ✅ CSV export
├── utils.py             ✅ Utility functions
├── whitelist.json       ✅ Security configuration
├── requirements.txt     ✅ Dependencies list
├── test_suite.py        ✅ Test script
├── start.bat            ✅ Quick launch script
├── README.md            ✅ Documentation
├── VIVA_GUIDE.md        ✅ Presentation guide
├── SETUP.md             ✅ This file
│
├── usb_logs.db          🆕 Created on first run
└── usb_logs_*.csv       🆕 Created when exporting
```

---

## 🎯 Next Steps

1. ✅ **Run the application:** `python main.py`
2. ✅ **Test with USB devices:** Plug and unplug devices
3. ✅ **Review the code:** Understand each module
4. ✅ **Read VIVA_GUIDE.md:** Prepare for presentation
5. ✅ **Practice demo:** Be ready to explain everything

---

## 📞 Quick Commands Reference

| Task | Command |
|------|---------|
| Install dependencies | `pip install -r requirements.txt` |
| Run tests | `python test_suite.py` |
| Launch app (batch) | `start.bat` |
| Launch app (python) | `python main.py` |
| Check Python version | `python --version` |
| List installed packages | `pip list` |

---

## 💡 Pro Tips

1. **Before Demo:**
   - Clear old logs for clean demonstration
   - Have a USB device ready
   - Test everything once

2. **During Demo:**
   - Explain while you demonstrate
   - Point out the console messages
   - Show the database file
   - Open exported CSV in Excel

3. **For Viva:**
   - Know every line of code
   - Be ready to explain design decisions
   - Understand the limitations
   - Have future improvements ready

---

## ✨ You're All Set!

Your Real Time USB Activity Logger is now ready to use. The application will:
- ✅ Monitor USB devices in real-time
- ✅ Log all events to database
- ✅ Display in professional GUI
- ✅ Export to CSV format
- ✅ Run reliably in background

**Happy monitoring! 🎉**

---

## 📚 Additional Resources

- **README.md** - Complete project documentation
- **VIVA_GUIDE.md** - Presentation and viva preparation
- **test_suite.py** - Comprehensive testing
- **Code comments** - Detailed inline explanations

---

**For questions or issues, review the code comments and documentation.**
