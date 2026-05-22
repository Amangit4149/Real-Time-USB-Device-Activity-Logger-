"""
DATABASE LAYER
--------------
This module handles all SQLite database operations for USB device logging.
SQLite is used because:
- Lightweight and serverless
- No installation required
- Perfect for desktop applications
- ACID compliant (reliable data storage)
"""

import sqlite3
from datetime import datetime
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'usb_logs.db')


def init_db():
    """
    Initialize the SQLite database and create tables if they don't exist.
    
    PHASE 2 UPGRADE:
    - Added session tracking to usb_logs table
    - Created file_logs table for file system monitoring
    
    usb_logs Table Schema:
    - id: Auto-incrementing primary key
    - event_type: 'CONNECTED' or 'DISCONNECTED'
    - device_name: Human-readable device name
    - device_id: Full Windows device ID string
    - vendor_id: USB Vendor ID (VID)
    - product_id: USB Product ID (PID)
    - serial_number: Device serial number
    - timestamp: When the event occurred
    - connect_time: When device was connected (NEW)
    - disconnect_time: When device was disconnected (NEW)
    - usage_duration: Session duration in seconds (NEW)
    - username: User who connected the device (NEW)
    
    file_logs Table Schema:
    - id: Auto-incrementing primary key
    - device_id: Associated USB device ID
    - file_path: Full path to the file
    - event_type: 'CREATED', 'DELETED', or 'MODIFIED'
    - file_size: File size in bytes
    - username: User who performed the action
    - timestamp: When the event occurred
    - risk_flag: 'NORMAL' or 'LARGE_TRANSFER' (>50MB)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create or upgrade usb_logs table with session tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usb_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                device_name TEXT,
                device_id TEXT,
                vendor_id TEXT,
                product_id TEXT,
                serial_number TEXT,
                timestamp TEXT NOT NULL,
                connect_time TEXT,
                disconnect_time TEXT,
                usage_duration INTEGER,
                username TEXT
            )
        ''')
        
        # Create file_logs table for file system monitoring
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                event_type TEXT NOT NULL,
                file_size INTEGER,
                username TEXT,
                timestamp TEXT NOT NULL,
                risk_flag TEXT DEFAULT 'NORMAL'
            )
        ''')
        
        conn.commit()
        conn.close()
        print("[✓] Database initialized successfully (Phase 2 schema)")
        return True
        
    except sqlite3.Error as e:
        print(f"[✗] Database initialization error: {e}")
        return False


def insert_log(event_type, device_name, device_id, vendor_id, product_id, serial_number, timestamp, 
               connect_time=None, disconnect_time=None, usage_duration=None, username=None):
    """
    Insert a new USB event log into the database.
    
    PHASE 2 UPGRADE: Added session tracking parameters
    
    Uses parameterized queries to prevent SQL injection attacks.
    
    Args:
        event_type (str): Type of event ('CONNECTED' or 'DISCONNECTED')
        device_name (str): Device name
        device_id (str): Full device ID
        vendor_id (str): Vendor ID
        product_id (str): Product ID
        serial_number (str): Serial number
        timestamp (str): Event timestamp
        connect_time (str): Connection timestamp (optional)
        disconnect_time (str): Disconnection timestamp (optional)
        usage_duration (int): Session duration in seconds (optional)
        username (str): Username who connected device (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Parameterized query prevents SQL injection
        cursor.execute('''
            INSERT INTO usb_logs 
            (event_type, device_name, device_id, vendor_id, product_id, serial_number, 
             timestamp, connect_time, disconnect_time, usage_duration, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (event_type, device_name, device_id, vendor_id, product_id, serial_number, 
              timestamp, connect_time, disconnect_time, usage_duration, username))
        
        conn.commit()
        conn.close()
        print(f"[✓] Log inserted: {event_type} - {device_name}")
        return True
        
    except sqlite3.Error as e:
        print(f"[✗] Insert error: {e}")
        return False


def fetch_all_logs():
    """
    Retrieve all USB logs from the database.
    
    Returns:
        list: List of tuples containing all log records
              Each tuple: (id, event_type, device_name, device_id, vendor_id, 
                          product_id, serial_number, timestamp)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Fetch all records ordered by most recent first
        cursor.execute('SELECT * FROM usb_logs ORDER BY id DESC')
        logs = cursor.fetchall()
        
        conn.close()
        return logs
        
    except sqlite3.Error as e:
        print(f"[✗] Fetch error: {e}")
        return []


def clear_all_logs():
    """
    Delete all logs from the database.
    Used for testing or cleanup purposes.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM usb_logs')
        
        conn.commit()
        conn.close()
        print("[✓] All logs cleared")
        return True
        
    except sqlite3.Error as e:
        print(f"[✗] Clear error: {e}")
        return False


def get_log_count():
    """
    Get the total number of logs in the database.
    
    Returns:
        int: Number of log entries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM usb_logs')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
        
    except sqlite3.Error as e:
        print(f"[✗] Count error: {e}")
        return 0


# ============================================================================
# PHASE 2: FILE LOGGING FUNCTIONS
# ============================================================================

def insert_file_log(device_id, file_path, event_type, file_size, username, timestamp, risk_flag='NORMAL'):
    """
    Insert a file system event log into the database.
    
    PHASE 2 NEW FUNCTION: Logs file operations on USB drives
    
    Args:
        device_id (str): Associated USB device ID
        file_path (str): Full path to the file
        event_type (str): 'CREATED', 'DELETED', or 'MODIFIED'
        file_size (int): File size in bytes
        username (str): User who performed the action
        timestamp (str): Event timestamp
        risk_flag (str): 'NORMAL' or 'LARGE_TRANSFER'
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Parameterized query prevents SQL injection
        cursor.execute('''
            INSERT INTO file_logs 
            (device_id, file_path, event_type, file_size, username, timestamp, risk_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (device_id, file_path, event_type, file_size, username, timestamp, risk_flag))
        
        conn.commit()
        conn.close()
        
        # Log with risk indicator
        risk_indicator = "⚠️" if risk_flag == 'LARGE_TRANSFER' else "✓"
        print(f"[{risk_indicator}] File log: {event_type} - {os.path.basename(file_path)}")
        return True
        
    except sqlite3.Error as e:
        print(f"[✗] File log insert error: {e}")
        return False


def fetch_file_logs(limit=None):
    """
    Retrieve file logs from the database.
    
    Args:
        limit (int): Maximum number of records to fetch (None for all)
    
    Returns:
        list: List of tuples containing file log records
              Each tuple: (id, device_id, file_path, event_type, file_size, 
                          username, timestamp, risk_flag)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if limit:
            cursor.execute('SELECT * FROM file_logs ORDER BY id DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM file_logs ORDER BY id DESC')
        
        logs = cursor.fetchall()
        
        conn.close()
        return logs
        
    except sqlite3.Error as e:
        print(f"[✗] File fetch error: {e}")
        return []


def clear_file_logs():
    """
    Delete all file logs from the database.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM file_logs')
        
        conn.commit()
        conn.close()
        print("[✓] All file logs cleared")
        return True
        
    except sqlite3.Error as e:
        print(f"[✗] Clear file logs error: {e}")
        return False


# ============================================================================
# PHASE 2: ANALYTICS FUNCTIONS
# ============================================================================

def count_large_transfers():
    """
    Count the number of large file transfers (>50MB).
    
    Returns:
        int: Number of large transfers
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM file_logs WHERE risk_flag = 'LARGE_TRANSFER'")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
        
    except sqlite3.Error as e:
        print(f"[✗] Count large transfers error: {e}")
        return 0


def count_total_file_events():
    """
    Count the total number of file events.
    
    Returns:
        int: Total file events
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM file_logs')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
        
    except sqlite3.Error as e:
        print(f"[✗] Count file events error: {e}")
        return 0


def count_sessions_today():
    """
    Count the number of USB sessions today.
    
    Returns:
        int: Number of sessions today
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT COUNT(*) FROM usb_logs 
            WHERE event_type = 'CONNECTED' 
            AND timestamp LIKE ?
        ''', (f'{today}%',))
        
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
        
    except sqlite3.Error as e:
        print(f"[✗] Count sessions error: {e}")
        return 0


def update_session_end(device_id, disconnect_time, usage_duration):
    """
    Update a USB session with disconnection time and duration.
    
    PHASE 2 NEW FUNCTION: Updates session tracking data
    
    Args:
        device_id (str): Device ID to update
        disconnect_time (str): Disconnection timestamp
        usage_duration (int): Session duration in seconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update the most recent CONNECTED entry for this device
        cursor.execute('''
            UPDATE usb_logs 
            SET disconnect_time = ?, usage_duration = ?
            WHERE device_id = ? 
            AND event_type = 'CONNECTED'
            AND disconnect_time IS NULL
            ORDER BY id DESC
            LIMIT 1
        ''', (disconnect_time, usage_duration, device_id))
        
        conn.commit()
        conn.close()
        
        print(f"[✓] Session updated: {usage_duration}s duration")
        return True
        
    except sqlite3.Error as e:
        print(f"[✗] Update session error: {e}")
        return False

