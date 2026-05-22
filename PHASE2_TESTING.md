# 🧪 PHASE 2 TESTING GUIDE

## USB Activity Logger - Phase 2 DLP Prototype Testing

**Version:** 2.0  
**Date:** February 10, 2026  
**Status:** Ready for Testing

---

## 🎯 TESTING OBJECTIVES

Verify that all Phase 2 enhancements work correctly:
1. Session tracking (connect time, disconnect time, duration, username)
2. File system monitoring (create, delete, modify)
3. Large file transfer detection (>50MB)
4. Alert popup system
5. Dual-table GUI display
6. Analytics dashboard
7. Database integrity

---

## 📋 PRE-TESTING CHECKLIST

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

**Required packages:**
- ✅ pywin32 (Windows API)
- ✅ WMI (USB detection)
- ✅ watchdog (File monitoring) - **NEW in Phase 2**

### **2. Verify Database Schema**
```bash
python -c "from database import init_db; init_db()"
```

**Expected output:**
```
[✓] Database initialized successfully (Phase 2 schema)
```

### **3. Check File Structure**
```
usb_logger/
├── main.py
├── monitor.py           ✅ Updated
├── file_monitor.py      ✅ NEW
├── database.py          ✅ Updated
├── gui.py               ✅ Updated
├── utils.py             ✅ Updated
├── export.py
└── requirements.txt     ✅ Updated
```

---

## 🧪 TEST SUITE

### **TEST 1: Database Schema Verification**

**Objective:** Verify Phase 2 database tables exist

**Steps:**
```python
python -c "
import sqlite3
conn = sqlite3.connect('usb_logs.db')
cursor = conn.cursor()

# Check usb_logs table has new columns
cursor.execute('PRAGMA table_info(usb_logs)')
columns = [col[1] for col in cursor.fetchall()]
print('USB Logs columns:', columns)

# Check file_logs table exists
cursor.execute('PRAGMA table_info(file_logs)')
file_columns = [col[1] for col in cursor.fetchall()]
print('File Logs columns:', file_columns)

conn.close()
"
```

**Expected output:**
```
USB Logs columns: ['id', 'event_type', 'device_name', 'device_id', 'vendor_id', 
                   'product_id', 'serial_number', 'timestamp', 'connect_time', 
                   'disconnect_time', 'usage_duration', 'username']

File Logs columns: ['id', 'device_id', 'file_path', 'event_type', 'file_size', 
                    'username', 'timestamp', 'risk_flag']
```

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 2: Session Tracking - USB Insertion**

**Objective:** Verify username and connect_time are logged

**Steps:**
1. Launch application: `python main.py`
2. Observe console output
3. Plug in a USB device
4. Wait 3-5 seconds

**Expected console output:**
```
[✓] USB monitoring started (Phase 2 - with session tracking)
[USB CONNECTED] USB Mass Storage Device (User: YourUsername)
[✓] Detected drive letter: E:
[✓] Log inserted: CONNECTED - USB Mass Storage Device
[✓] File monitoring started for E:
```

**Verify in database:**
```python
from database import fetch_all_logs
logs = fetch_all_logs()
latest = logs[0]
print(f"Username: {latest[11]}")
print(f"Connect time: {latest[8]}")
```

**Expected:**
- Username should be your Windows username
- Connect time should be current timestamp

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 3: File Creation Detection**

**Objective:** Verify file creation is logged

**Steps:**
1. With USB still connected, open the USB drive in File Explorer
2. Create a new text file: `test_file.txt`
3. Type some content and save
4. Check console output

**Expected console output:**
```
[✓] File log: CREATED - test_file.txt
```

**Verify in GUI:**
- File Activity Log table should show new entry
- Event Type: CREATED
- File Path: E:\test_file.txt
- Risk Flag: NORMAL
- Username: YourUsername

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 4: File Modification Detection**

**Objective:** Verify file modification is logged

**Steps:**
1. Open `test_file.txt` on USB drive
2. Add more text
3. Save and close

**Expected console output:**
```
[✓] File log: MODIFIED - test_file.txt
```

**Verify in GUI:**
- New entry in File Activity Log
- Event Type: MODIFIED
- Same file path

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 5: File Deletion Detection**

**Objective:** Verify file deletion is logged

**Steps:**
1. Delete `test_file.txt` from USB drive
2. Check console output

**Expected console output:**
```
[✓] File log: DELETED - test_file.txt
```

**Verify in GUI:**
- New entry in File Activity Log
- Event Type: DELETED
- File Size: 0 B (deleted files have no size)

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 6: Large File Transfer Alert**

**Objective:** Verify >50MB files trigger alert popup

**Steps:**
1. Create or copy a file >50MB to USB drive
   - Option A: Download a large file
   - Option B: Create dummy file:
     ```bash
     # In PowerShell on USB drive
     fsutil file createnew large_test.bin 52428800  # 50MB
     ```
2. Wait for alert popup

**Expected:**
- ⚠️ Alert popup appears
- Title: "Large File Transfer Alert"
- Message shows:
  - File name
  - Size in MB (>50)
  - Username
  - Event type (CREATED)

**Verify in GUI:**
- File Activity Log shows entry
- Risk Flag: **LARGE_TRANSFER** (red background)
- Analytics dashboard: "⚠️ Large Transfers" counter increases

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 7: Session Duration Tracking**

**Objective:** Verify session duration is calculated on USB removal

**Steps:**
1. Note the current time
2. Wait at least 30 seconds with USB connected
3. Safely eject and remove USB device
4. Check console output

**Expected console output:**
```
[USB DISCONNECTED] USB Mass Storage Device
[✓] Session duration: 45s
[✓] File monitoring stopped for [device_id]
[✓] Session updated: 45s duration
```

**Verify in GUI:**
- USB Device Activity table
- Latest CONNECTED entry should show Duration (e.g., "45s")
- DISCONNECTED event logged

**Verify in database:**
```python
from database import fetch_all_logs
logs = fetch_all_logs()
for log in logs[:2]:  # Check last 2 entries
    if log[10]:  # usage_duration
        print(f"Duration: {log[10]} seconds")
```

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 8: Analytics Dashboard**

**Objective:** Verify analytics counters update correctly

**Steps:**
1. Perform several USB connections/disconnections
2. Create multiple files on USB
3. Create at least one large file (>50MB)
4. Observe analytics dashboard in GUI

**Expected:**
- **Sessions Today:** Shows count of USB connections today
- **Total File Events:** Shows total file operations (create/delete/modify)
- **⚠️ Large Transfers:** Shows count of >50MB transfers

**Verify programmatically:**
```python
from database import count_sessions_today, count_total_file_events, count_large_transfers

print(f"Sessions: {count_sessions_today()}")
print(f"File Events: {count_total_file_events()}")
print(f"Large Transfers: {count_large_transfers()}")
```

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 9: Dual Table Display**

**Objective:** Verify both tables display correctly

**Steps:**
1. Launch GUI
2. Verify two separate tables are visible

**Table 1: USB Device Activity**
- Columns: ID, Event, Device, VID, PID, Serial, Username, Timestamp, Duration
- Color coding: Green (CONNECTED), Red (DISCONNECTED)

**Table 2: File Activity Log**
- Columns: ID, Device ID, File Path, Event, Size, Risk, Username, Timestamp
- Color coding: White (NORMAL), Red (LARGE_TRANSFER)

**Verify:**
- Both tables scroll independently
- Both tables have separate scrollbars
- Data displays correctly in both

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 10: Refresh Buttons**

**Objective:** Verify separate refresh controls work

**Steps:**
1. Click "🔄 Refresh USB" button
   - USB table should refresh
   - File table should NOT change
2. Click "📁 Refresh Files" button
   - File table should refresh
   - USB table should NOT change

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 11: Clear Logs Functions**

**Objective:** Verify separate clear functions work

**Steps:**
1. Click "🗑️ Clear USB" button
   - Confirmation dialog appears
   - Click "Yes"
   - USB table clears
   - File table remains unchanged

2. Click "🗑️ Clear Files" button
   - Confirmation dialog appears
   - Click "Yes"
   - File table clears
   - USB table remains unchanged

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 12: Auto-Refresh**

**Objective:** Verify auto-refresh updates both tables

**Steps:**
1. Ensure "Auto-Refresh" checkbox is checked
2. Plug in USB device
3. Wait 3 seconds (refresh interval)
4. Verify USB table updates automatically
5. Create a file on USB
6. Wait 3 seconds
7. Verify File table updates automatically

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 13: CSV Export**

**Objective:** Verify export includes both log types

**Steps:**
1. Click "📤 Export CSV" button
2. Open generated CSV file
3. Verify it contains USB logs

**Note:** Current export.py may need update to include file logs.
This is acceptable for Phase 2 demo.

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 14: Thread Safety**

**Objective:** Verify no GUI freezing during monitoring

**Steps:**
1. Launch application
2. Plug/unplug USB multiple times rapidly
3. Create/delete files rapidly on USB
4. Verify GUI remains responsive
5. Verify no crashes or freezes

**Expected:**
- GUI buttons remain clickable
- Tables continue to update
- No "Not Responding" message

**Result:** ✅ PASS / ❌ FAIL

---

### **TEST 15: Graceful Shutdown**

**Objective:** Verify clean shutdown of all threads

**Steps:**
1. With USB connected and file monitoring active
2. Click "❌ Exit" button
3. Confirm exit
4. Check console output

**Expected console output:**
```
[✓] Stopping USB monitoring...
[✓] File monitoring stopped for [device_id]
[✓] All file monitors stopped
[✓] USB monitoring stopped
```

**Verify:**
- No error messages
- Application closes cleanly
- No zombie processes

**Result:** ✅ PASS / ❌ FAIL

---

## 📊 TEST RESULTS SUMMARY

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | Database Schema | ⬜ | |
| 2 | USB Insertion | ⬜ | |
| 3 | File Creation | ⬜ | |
| 4 | File Modification | ⬜ | |
| 5 | File Deletion | ⬜ | |
| 6 | Large File Alert | ⬜ | |
| 7 | Session Duration | ⬜ | |
| 8 | Analytics Dashboard | ⬜ | |
| 9 | Dual Table Display | ⬜ | |
| 10 | Refresh Buttons | ⬜ | |
| 11 | Clear Logs | ⬜ | |
| 12 | Auto-Refresh | ⬜ | |
| 13 | CSV Export | ⬜ | |
| 14 | Thread Safety | ⬜ | |
| 15 | Graceful Shutdown | ⬜ | |

**Legend:** ✅ PASS | ❌ FAIL | ⬜ NOT TESTED

---

## 🐛 TROUBLESHOOTING

### **Issue: "No module named 'watchdog'"**
**Solution:**
```bash
pip install watchdog
```

### **Issue: File monitoring not starting**
**Solution:**
- Verify USB drive has a drive letter (E:, F:, etc.)
- Check console for error messages
- Ensure watchdog is installed

### **Issue: Alert popup not appearing**
**Solution:**
- Verify file is actually >50MB
- Check that file_monitor.py has alert_callback set
- Look for console message: `[⚠️] File log: CREATED - filename`

### **Issue: Duration shows as empty**
**Solution:**
- Duration only shows for CONNECTED events after USB is removed
- Refresh the table after removing USB

### **Issue: Username shows as "Unknown"**
**Solution:**
- This is normal if `os.getlogin()` fails
- Usually works correctly on standard Windows installations

### **Issue: GUI freezes**
**Solution:**
- This should NOT happen with proper threading
- If it does, check for exceptions in console
- Verify daemon threads are being used

---

## 🎯 ACCEPTANCE CRITERIA

**Phase 2 is considered PASSING if:**

✅ At least 13/15 tests pass  
✅ All critical features work (Tests 1-8)  
✅ No crashes or data loss  
✅ GUI remains responsive  
✅ Database integrity maintained  

---

## 📝 TEST REPORT TEMPLATE

```
PHASE 2 TEST REPORT
===================
Date: _______________
Tester: _______________
Environment: Windows ___

Tests Passed: ___/15
Tests Failed: ___/15
Critical Issues: ___

Summary:
_______________________________________
_______________________________________

Recommendations:
_______________________________________
_______________________________________

Signature: _______________
```

---

## 🚀 DEMO SCRIPT

**For presentation/viva:**

1. **Launch:** `python main.py`
2. **Show:** Empty tables, analytics at 0
3. **Insert USB:** Watch console, see CONNECTED event
4. **Show GUI:** USB table updates, username logged
5. **Create file:** On USB drive, show file log appears
6. **Create large file:** >50MB, show alert popup
7. **Show analytics:** Counters updated
8. **Remove USB:** Show duration calculated
9. **Export:** Generate CSV report
10. **Exit:** Clean shutdown

**Total demo time: 5-7 minutes**

---

## ✅ FINAL CHECKLIST

Before declaring Phase 2 complete:

- [ ] All dependencies installed
- [ ] Database schema verified
- [ ] USB insertion/removal works
- [ ] File monitoring works
- [ ] Large file alerts work
- [ ] Session duration calculated
- [ ] Analytics dashboard updates
- [ ] GUI displays both tables
- [ ] No crashes or freezes
- [ ] Clean shutdown works
- [ ] Documentation updated
- [ ] Ready for demo

---

**Happy Testing! 🧪✨**

**Remember:** This is a user-space DLP prototype. Some limitations are expected and acceptable for academic demonstration.
