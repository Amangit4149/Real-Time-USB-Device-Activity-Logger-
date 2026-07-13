"""
USB MONITORING ENGINE - PHASE 2 UPGRADE
----------------------------------------
This module monitors USB device insertion and removal events on Windows.

PHASE 2 ENHANCEMENTS:
- Session tracking (connect time, disconnect time, duration)
- Username logging for accountability
- Drive letter detection
- File system monitoring integration
- Active session management

WMI (Windows Management Instrumentation):
- Windows API for system management
- Allows querying hardware events in real-time
- Can detect device connections/disconnections
- Provides detailed device information

How USB Detection Works:
1. WMI watches for Win32_USBControllerDevice events
2. When a USB device is added/removed, WMI triggers an event
3. We extract device details from the event
4. Parse VID, PID, and serial number
5. Detect drive letter for file monitoring
6. Start/stop file monitoring threads
7. Track session duration
8. Log to database with username

Difference Between Hardware and File Monitoring:
- Hardware Monitoring (this module): Detects USB connection/disconnection
- File Monitoring (file_monitor.py): Tracks file operations on mounted drives
- Both run in separate threads for non-blocking operation
"""

import wmi
import time
import threading
import pythoncom  # Required for WMI in threads
from database import insert_log, update_session_end
from utils import (parse_device_id, get_timestamp, is_valid_usb_device, 
                   sanitize_string, get_username, get_all_removable_drives,
                   calculate_duration, capture_screenshot, send_email_notification)
from config import ensure_config_files, get_app_config, get_email_config, is_device_whitelisted

# Import file monitoring (Phase 2)
try:
    from file_monitor import start_file_monitoring, stop_file_monitoring
    FILE_MONITORING_AVAILABLE = True
except ImportError:
    FILE_MONITORING_AVAILABLE = False
    print("[!] File monitoring not available - install watchdog")

# Global flag to control monitoring
monitoring_active = False
monitor_thread = None

# PHASE 2: Active session tracking
# Format: {device_id: {'connect_time': str, 'drive_letter': str, 'username': str, 'device_info': dict}}
active_sessions = {}

# Alert callback for file monitoring and unauthorized USB detection
file_alert_callback = None
usb_alert_callback = None


def set_file_alert_callback(callback):
    """
    Set the callback function for file transfer alerts.
    
    PHASE 2 NEW FUNCTION
    
    Args:
        callback (callable): Function to call when large file detected
    """
    global file_alert_callback
    file_alert_callback = callback


def set_usb_alert_callback(callback):
    """
    Set the callback function for unauthorized USB alerts.
    """
    global usb_alert_callback
    usb_alert_callback = callback


# Ensure config files are available at import time
ensure_config_files()


def get_connected_usb_devices():
    """
    Get a list of currently connected USB devices.
    
    Returns:
        list: List of device information dictionaries
    """
    devices = []
    
    try:
        c = wmi.WMI()
        
        # Query all USB controller devices
        for usb in c.Win32_USBControllerDevice():
            try:
                # Get the dependent device (the USB device itself)
                device = usb.Dependent
                
                if device and hasattr(device, 'DeviceID'):
                    device_id = device.DeviceID
                    
                    # Only process valid USB devices
                    if is_valid_usb_device(device_id):
                        # Parse device information
                        parsed = parse_device_id(device_id)
                        
                        # Get device name
                        device_name = getattr(device, 'Name', 'Unknown Device')
                        device_name = sanitize_string(device_name)
                        
                        devices.append({
                            'name': device_name,
                            'device_id': device_id,
                            'vid': parsed['vid'],
                            'pid': parsed['pid'],
                            'serial': parsed['serial']
                        })
            except Exception as e:
                # Skip devices that cause errors
                continue
                
    except Exception as e:
        print(f"[ERROR] Error getting USB devices: {e}")
    
    return devices


def monitor_usb_events():
    """
    Continuously monitor for USB insertion and removal events.
    
    PHASE 2 UPGRADE: Now includes session tracking and file monitoring
    
    This function runs in a background thread and:
    1. Tracks currently connected devices
    2. Polls for changes every 2 seconds
    3. Detects new connections (insertion)
    4. Detects disconnections (removal)
    5. Logs all events to database with username
    6. Tracks session duration
    7. Starts/stops file monitoring for each drive
    
    Threading is required because:
    - Prevents GUI from freezing
    - Allows continuous monitoring in background
    - Enables real-time event detection
    """
    global monitoring_active, active_sessions
    
    print("[OK] USB monitoring started (Phase 2 - with session tracking)")
    
    # CRITICAL FIX: Initialize COM for this thread
    # WMI requires COM initialization when running in a separate thread
    pythoncom.CoInitialize()
    
    
    # Get initial state of connected devices and drives
    previous_devices = {dev['device_id']: dev for dev in get_connected_usb_devices()}
    previous_drive_letters = set(get_all_removable_drives())
    
    try:
        while monitoring_active:
            try:
                # Get current connected devices
                current_devices = {dev['device_id']: dev for dev in get_connected_usb_devices()}
                
                # Get current drives to detect new ones
                current_drive_letters = set(get_all_removable_drives())
            
                # Detect NEW devices (insertion)
                for device_id, device_info in current_devices.items():
                    if device_id not in previous_devices:
                        # New device connected!
                        timestamp = get_timestamp()
                        username = get_username()
                        
                        print(f"[USB CONNECTED] {device_info['name']} (User: {username})")
                        
                        # Detect drive letter (NEW logic)
                        drive_letter = None
                        
                        # Find which drive letter is new
                        new_drives = current_drive_letters - previous_drive_letters
                        
                        if new_drives:
                            # Use the new drive letter
                            drive_letter = list(new_drives)[0]
                            print(f"[OK] Detected NEW drive letter: {drive_letter}")
                        else:
                            # Fallback: If no new drive detected, but we have drives
                            # Check if the device matches any available drive (not perfect)
                            # Maybe wait a bit?
                            print(f"[?] No new drive letter detected immediately.")
                            
                            # Try one more time after short delay
                            time.sleep(1)
                            retry_drives = set(get_all_removable_drives())
                            new_retry = retry_drives - previous_drive_letters
                            if new_retry:
                                drive_letter = list(new_retry)[0]
                                print(f"[OK] Detected drive letter after retry: {drive_letter}")
                                current_drive_letters = retry_drives # Update current
                        
                        # Log to database with session tracking
                        insert_log(
                            event_type='CONNECTED',
                            device_name=device_info['name'],
                            device_id=device_id,
                            vendor_id=device_info['vid'],
                            product_id=device_info['pid'],
                            serial_number=device_info['serial'],
                            timestamp=timestamp,
                            connect_time=timestamp,
                            username=username
                        )

                        # Check whitelist and security policy
                        app_config = get_app_config()
                        authorized = is_device_whitelisted(device_info)
                        if not authorized and app_config.get('alert_on_unknown_device', True):
                            # Log an unauthorized event for visibility
                            insert_log(
                                event_type='UNAUTHORIZED',
                                device_name=device_info['name'],
                                device_id=device_id,
                                vendor_id=device_info['vid'],
                                product_id=device_info['pid'],
                                serial_number=device_info['serial'],
                                timestamp=timestamp,
                                connect_time=timestamp,
                                username=username
                            )
                            print(f"[!] Unauthorized USB device detected: {device_info['name']}")

                            # Capture screenshot if configured
                            if app_config.get('capture_screenshots_on_unauthorized_insert', False):
                                screenshot_path = capture_screenshot(app_config.get('screenshot_dir'))
                                if screenshot_path:
                                    print(f"[OK] Unauthorized event screenshot: {screenshot_path}")

                            # Send email alert if configured
                            email_config = get_email_config()
                            if email_config.get('enabled'):
                                subject = f"USB Security Alert - Unauthorized Device Detected"
                                body = (
                                    f"An unauthorized USB device was detected.\n\n"
                                    f"Device Name: {device_info['name']}\n"
                                    f"Vendor ID: {device_info['vid']}\n"
                                    f"Product ID: {device_info['pid']}\n"
                                    f"Serial Number: {device_info['serial']}\n"
                                    f"User: {username}\n"
                                    f"Time: {timestamp}\n"
                                )
                                send_email_notification(subject, body, email_config.get('recipients', []), email_config)

                            if usb_alert_callback:
                                usb_alert_callback(device_info=device_info, username=username, timestamp=timestamp)

                        # Track active session
                        active_sessions[device_id] = {
                            'connect_time': timestamp,
                            'drive_letter': drive_letter,
                            'username': username,
                            'device_info': device_info
                        }
                        
                        # Start file monitoring if drive letter detected
                        if drive_letter and FILE_MONITORING_AVAILABLE:
                            success = start_file_monitoring(
                                device_id=device_id,
                                drive_letter=drive_letter,
                                username=username,
                                alert_callback=file_alert_callback
                            )
                            if not success:
                                print(f"[!] Failed to start file monitor for {drive_letter}")
                
                # Detect REMOVED devices (disconnection)
                for device_id, device_info in previous_devices.items():
                    if device_id not in current_devices:
                        # Device was removed!
                        timestamp = get_timestamp()
                        
                        print(f"[USB DISCONNECTED] {device_info['name']}")
                        
                        # Calculate session duration
                        usage_duration = 0
                        if device_id in active_sessions:
                            session = active_sessions[device_id]
                            connect_time = session['connect_time']
                            usage_duration = calculate_duration(connect_time, timestamp)
                            
                            print(f"[OK] Session duration: {usage_duration}s")
                            
                            # Stop file monitoring
                            if FILE_MONITORING_AVAILABLE:
                                stop_file_monitoring(device_id)
                            
                            # Remove from active sessions
                            del active_sessions[device_id]
                        
                        # Update database with session end
                        update_session_end(
                            device_id=device_id,
                            disconnect_time=timestamp,
                            usage_duration=usage_duration
                        )
                        
                        # Log disconnection event
                        insert_log(
                            event_type='DISCONNECTED',
                            device_name=device_info['name'],
                            device_id=device_id,
                            vendor_id=device_info['vid'],
                            product_id=device_info['pid'],
                            serial_number=device_info['serial'],
                            timestamp=timestamp,
                            disconnect_time=timestamp
                        )
                
                # Update previous state
                previous_devices = current_devices
                previous_drive_letters = current_drive_letters
                
                # Wait before next check (polling interval)
                time.sleep(2)
                
            except Exception as e:
                print(f"[ERROR] Monitoring error: {e}")
                time.sleep(2)  # Wait before retrying
    
    finally:
        # Clean up COM resources
        pythoncom.CoUninitialize()
        print("[OK] USB monitoring stopped")


def start_monitoring():
    """
    Start USB monitoring in a background thread.
    
    Returns:
        bool: True if started successfully, False otherwise
    """
    global monitoring_active, monitor_thread
    
    if monitoring_active:
        print("[!] Monitoring already active")
        return False
    
    try:
        monitoring_active = True
        monitor_thread = threading.Thread(target=monitor_usb_events, daemon=True)
        monitor_thread.start()
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to start monitoring: {e}")
        monitoring_active = False
        return False


def stop_monitoring():
    """
    Stop USB monitoring and all file monitors.
    
    PHASE 2 UPGRADE: Also stops file monitoring
    """
    global monitoring_active
    
    if not monitoring_active:
        print("[!] Monitoring not active")
        return
    
    monitoring_active = False
    
    # Stop all file monitors
    if FILE_MONITORING_AVAILABLE:
        from file_monitor import stop_all_monitors
        stop_all_monitors()
    
    print("[OK] Stopping USB monitoring...")


def is_monitoring_active():
    """
    Check if monitoring is currently active.
    
    Returns:
        bool: True if monitoring, False otherwise
    """
    return monitoring_active


def get_active_sessions():
    """
    Get information about currently active USB sessions.
    
    PHASE 2 NEW FUNCTION
    
    Returns:
        dict: Active sessions dictionary
    """
    return active_sessions.copy()


def get_session_count():
    """
    Get the number of active USB sessions.
    
    PHASE 2 NEW FUNCTION
    
    Returns:
        int: Number of active sessions
    """
    return len(active_sessions)
