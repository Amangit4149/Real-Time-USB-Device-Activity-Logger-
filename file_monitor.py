"""
FILE SYSTEM MONITORING MODULE
------------------------------
PHASE 2: File-level activity tracking on USB drives

This module monitors file operations on mounted USB drives using the Watchdog library.

Why Watchdog?
- Cross-platform file system event monitoring
- Efficient event-driven architecture (not polling)
- Handles file creation, deletion, and modification
- Lightweight and reliable

How It Works:
1. When USB is inserted, we detect the drive letter
2. Start a Watchdog Observer for that drive
3. Monitor all file operations in real-time
4. Log events to database with risk assessment
5. Stop observer when USB is removed

Limitations (User-Space Only):
- Cannot detect read-only file access
- Cannot detect encrypted file transfers
- Cannot block file operations
- May miss very rapid file operations
- Requires drive to be mounted with a letter
"""

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from database import insert_file_log
from utils import get_timestamp

# File size threshold for risk flagging (50MB in bytes)
LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 50 MB

# Global dictionary to track active observers
# Format: {device_id: observer_instance}
active_observers = {}


class USBFileMonitor(FileSystemEventHandler):
    """
    File system event handler for USB drives.
    
    Monitors and logs:
    - File creation
    - File deletion
    - File modification
    
    Performs risk assessment:
    - Files > 50MB are flagged as LARGE_TRANSFER
    - Triggers alerts for potential data exfiltration
    """
    
    def __init__(self, device_id, drive_letter, username, alert_callback=None):
        """
        Initialize the file monitor.
        
        Args:
            device_id (str): USB device ID
            drive_letter (str): Drive letter (e.g., 'E:')
            username (str): Current user
            alert_callback (callable): Function to call for alerts (optional)
        """
        super().__init__()
        self.device_id = device_id
        self.drive_letter = drive_letter
        self.username = username
        self.alert_callback = alert_callback
        
        print(f"[OK] File monitor initialized for {drive_letter} ({username})")
    
    def _get_file_size(self, file_path):
        """
        Safely get file size.
        
        Args:
            file_path (str): Path to file
        
        Returns:
            int: File size in bytes, or 0 if error
        """
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return os.path.getsize(file_path)
        except (OSError, PermissionError):
            pass
        return 0
    
    def _assess_risk(self, file_size, file_path):
        """
        Assess risk level based on file size and extension.
        
        Args:
            file_size (int): File size in bytes
            file_path (str): Full path to the file
        
        Returns:
            str: 'SUSPICIOUS_FILE', 'LARGE_TRANSFER', or 'NORMAL'
        """
        # Check for suspicious extensions
        suspicious_exts = ['.exe', '.bat', '.ps1', '.vbs', '.cmd', '.msi', '.com', '.scr', '.pif']
        _, ext = os.path.splitext(file_path)
        if ext.lower() in suspicious_exts:
            return 'SUSPICIOUS_FILE'
            
        # Check for large file size
        if file_size > LARGE_FILE_THRESHOLD:
            return 'LARGE_TRANSFER'
            
        return 'NORMAL'
    
    def _log_file_event(self, file_path, event_type):
        """
        Log a file event to the database.
        
        Args:
            file_path (str): Full path to the file
            event_type (str): 'CREATED', 'DELETED', or 'MODIFIED'
        """
        try:
            # Get file size (0 for deleted files)
            file_size = self._get_file_size(file_path) if event_type != 'DELETED' else 0
            
            # Assess risk
            risk_flag = self._assess_risk(file_size, file_path)
            
            # Get timestamp
            timestamp = get_timestamp()
            
            # Log to database
            insert_file_log(
                device_id=self.device_id,
                file_path=file_path,
                event_type=event_type,
                file_size=file_size,
                username=self.username,
                timestamp=timestamp,
                risk_flag=risk_flag
            )
            
            # Trigger alert for high risk events
            if (risk_flag == 'LARGE_TRANSFER' or risk_flag == 'SUSPICIOUS_FILE') and self.alert_callback:
                file_size_mb = file_size / (1024 * 1024)
                self.alert_callback(
                    file_path=file_path,
                    file_size_mb=file_size_mb,
                    username=self.username,
                    event_type=event_type,
                    risk_flag=risk_flag
                )
        
        except Exception as e:
            print(f"[ERROR] Error logging file event: {e}")
    
    def on_created(self, event):
        """
        Called when a file or directory is created.
        
        Args:
            event: FileSystemEvent object
        """
        if not event.is_directory:
            # Ignore temporary and system files
            if not self._should_ignore(event.src_path):
                self._log_file_event(event.src_path, 'CREATED')
    
    def on_deleted(self, event):
        """
        Called when a file or directory is deleted.
        
        Args:
            event: FileSystemEvent object
        """
        if not event.is_directory:
            if not self._should_ignore(event.src_path):
                self._log_file_event(event.src_path, 'DELETED')
    
    def on_modified(self, event):
        """
        Called when a file or directory is modified.
        
        Args:
            event: FileSystemEvent object
        """
        if not event.is_directory:
            if not self._should_ignore(event.src_path):
                self._log_file_event(event.src_path, 'MODIFIED')
    
    def _should_ignore(self, file_path):
        """
        Determine if a file should be ignored.
        
        Ignores:
        - Temporary files (~, .tmp)
        - System files (.sys, desktop.ini)
        - Hidden files (starting with .)
        
        Args:
            file_path (str): Path to check
        
        Returns:
            bool: True if should ignore, False otherwise
        """
        filename = os.path.basename(file_path).lower()
        
        # Ignore patterns
        ignore_patterns = [
            '~',           # Temporary files
            '.tmp',        # Temp files
            '.temp',       # Temp files
            'desktop.ini', # Windows system
            'thumbs.db',   # Windows thumbnails
            '.ds_store',   # Mac system
            '$recycle',    # Recycle bin
        ]
        
        for pattern in ignore_patterns:
            if pattern in filename:
                return True
        
        # Ignore hidden files (starting with .)
        if filename.startswith('.') and filename != '.':
            return True
        
        return False


def start_file_monitoring(device_id, drive_letter, username, alert_callback=None):
    """
    Start monitoring file operations on a USB drive.
    
    Args:
        device_id (str): USB device ID
        drive_letter (str): Drive letter (e.g., 'E:')
        username (str): Current user
        alert_callback (callable): Function to call for alerts
    
    Returns:
        bool: True if started successfully, False otherwise
    """
    global active_observers
    
    try:
        # Check if already monitoring this device
        if device_id in active_observers:
            print(f"[!] Already monitoring {device_id}")
            return False
        
        # Verify drive exists
        if not os.path.exists(drive_letter):
            print(f"[ERROR] Drive {drive_letter} not found")
            return False
        
        # Create event handler
        event_handler = USBFileMonitor(device_id, drive_letter, username, alert_callback)
        
        # Create and start observer
        observer = Observer()
        observer.schedule(event_handler, drive_letter, recursive=True)
        observer.start()
        
        # Store observer
        active_observers[device_id] = observer
        
        print(f"[OK] File monitoring started for {drive_letter}")
        
        # SCAN EXISTING FILES
        # Run in a separate thread to avoid blocking
        import threading
        scan_thread = threading.Thread(
            target=scan_existing_files,
            args=(drive_letter, device_id, username, alert_callback)
        )
        scan_thread.daemon = True
        scan_thread.start()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to start file monitoring: {e}")
        return False


def scan_existing_files(drive_path, device_id, username, alert_callback):
    """
    Scan drive for existing suspicious files.
    """
    print(f"[?] Scanning {drive_path} for existing files...")
    
    suspicious_exts = ['.exe', '.bat', '.ps1', '.vbs', '.cmd', '.msi', '.com', '.scr', '.pif']
    
    try:
        # Walk through directory tree
        for root, dirs, files in os.walk(drive_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                # Check extension
                _, ext = os.path.splitext(filename)
                if ext.lower() in suspicious_exts:
                    try:
                        file_size = os.path.getsize(file_path)
                        timestamp = get_timestamp()
                        
                        # Log finding
                        insert_file_log(
                            device_id=device_id,
                            file_path=file_path,
                            event_type='FOUND_ON_SCAN',
                            file_size=file_size,
                            username=username,
                            timestamp=timestamp,
                            risk_flag='SUSPICIOUS_FILE'
                        )
                        
                        # Trigger alert
                        if alert_callback:
                            file_size_mb = file_size / (1024 * 1024)
                            alert_callback(
                                file_path=file_path,
                                file_size_mb=file_size_mb,
                                username=username,
                                event_type='FOUND_ON_SCAN',
                                risk_flag='SUSPICIOUS_FILE'
                            )
                            
                    except Exception as e:
                        print(f"[!] Error scanning file {filename}: {e}")
                        
    except Exception as e:
        print(f"[ERROR] Scan failed: {e}")


def stop_file_monitoring(device_id):
    """
    Stop monitoring file operations for a USB drive.
    
    Args:
        device_id (str): USB device ID
    
    Returns:
        bool: True if stopped successfully, False otherwise
    """
    global active_observers
    
    try:
        if device_id not in active_observers:
            print(f"[!] No active monitor for {device_id}")
            return False
        
        # Get observer
        observer = active_observers[device_id]
        
        # Stop observer
        observer.stop()
        observer.join(timeout=5)  # Wait up to 5 seconds
        
        # Remove from active list
        del active_observers[device_id]
        
        print(f"[OK] File monitoring stopped for {device_id}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to stop file monitoring: {e}")
        return False


def stop_all_monitors():
    """
    Stop all active file monitors.
    
    Used during application shutdown.
    """
    global active_observers
    
    device_ids = list(active_observers.keys())
    
    for device_id in device_ids:
        stop_file_monitoring(device_id)
    
    print("[OK] All file monitors stopped")


def is_monitoring(device_id):
    """
    Check if a device is currently being monitored.
    
    Args:
        device_id (str): USB device ID
    
    Returns:
        bool: True if monitoring, False otherwise
    """
    return device_id in active_observers


def get_active_monitor_count():
    """
    Get the number of active file monitors.
    
    Returns:
        int: Number of active monitors
    """
    return len(active_observers)
