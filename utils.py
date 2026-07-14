"""
UTILITY MODULE
--------------
Helper functions for parsing USB device information and formatting data.
"""

import os
import re
from datetime import datetime


def parse_device_id(device_id):
    """
    Parse a Windows USB Device ID string to extract VID, PID, and Serial Number.
    
    Windows Device ID Format Example:
    USB\\VID_0781&PID_5567\\4C530001234567890123

    Where:
    - VID = Vendor ID (identifies manufacturer)
    - PID = Product ID (identifies specific product)
    - Serial = Unique device serial number
    
    Args:
        device_id (str): Full Windows device ID string
    
    Returns:
        dict: Dictionary containing 'vid', 'pid', and 'serial'
              Returns None values if parsing fails
    """
    result = {
        'vid': None,
        'pid': None,
        'serial': None
    }
    
    if not device_id:
        return result
    
    try:
        # Extract Vendor ID (VID) using regex
        # Pattern: VID_ followed by 4 hexadecimal characters
        vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', device_id)
        if vid_match:
            result['vid'] = vid_match.group(1).upper()
        
        # Extract Product ID (PID) using regex
        # Pattern: PID_ followed by 4 hexadecimal characters
        pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', device_id)
        if pid_match:
            result['pid'] = pid_match.group(1).upper()
        
        # Extract Serial Number
        # Usually the part after the last backslash
        parts = device_id.split('\\')
        if len(parts) >= 3:
            # Serial is typically the third part
            serial_candidate = parts[2]
            # Remove any additional identifiers (like &0, &1, etc.)
            serial_candidate = serial_candidate.split('&')[0]
            result['serial'] = serial_candidate
        
    except Exception as e:
        print(f"[!] Error parsing device ID: {e}")
    
    return result


def get_timestamp():
    """
    Get current timestamp in a readable format.
    
    Returns:
        str: Formatted timestamp (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def format_device_info(device_name, vid, pid, serial):
    """
    Format device information for display or logging.
    
    Args:
        device_name (str): Device name
        vid (str): Vendor ID
        pid (str): Product ID
        serial (str): Serial number
    
    Returns:
        str: Formatted device information string
    """
    info = f"Device: {device_name or 'Unknown'}\n"
    info += f"VID: {vid or 'N/A'}\n"
    info += f"PID: {pid or 'N/A'}\n"
    info += f"Serial: {serial or 'N/A'}"
    return info


def is_valid_usb_device(device_id):
    """
    Check if a device ID string appears to be a valid USB device.
    
    Args:
        device_id (str): Device ID to validate
    
    Returns:
        bool: True if appears to be a USB device, False otherwise
    """
    if not device_id:
        return False
    
    # Check if it contains USB identifier
    if 'USB' not in device_id.upper():
        return False
    
    # Check if it has VID and PID
    has_vid = bool(re.search(r'VID_[0-9A-Fa-f]{4}', device_id))
    has_pid = bool(re.search(r'PID_[0-9A-Fa-f]{4}', device_id))
    
    return has_vid and has_pid


def sanitize_string(text, max_length=100):
    """
    Sanitize a string for safe database storage.
    
    Args:
        text (str): Text to sanitize
        max_length (int): Maximum allowed length
    
    Returns:
        str: Sanitized string
    """
    if not text:
        return ""
    
    # Remove any null bytes
    text = text.replace('\x00', '')
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()


# ============================================================================
# PHASE 2: SESSION TRACKING UTILITIES
# ============================================================================

def get_username():
    """
    Get the current Windows username.
    
    PHASE 2 NEW FUNCTION: For accountability tracking
    
    Returns:
        str: Current username, or 'Unknown' if error
    """
    try:
        import os
        username = os.getlogin()
        return username if username else 'Unknown'
    except Exception as e:
        print(f"[!] Error getting username: {e}")
        return 'Unknown'


def get_drive_letter_for_device(device_id):
    """
    Get the drive letter for a USB device.
    
    PHASE 2 NEW FUNCTION: Maps device ID to drive letter
    
    Uses WMI to query logical disk associations.
    
    Args:
        device_id (str): USB device ID
    
    Returns:
        str: Drive letter (e.g., 'E:'), or None if not found
    """
    try:
        import wmi
        c = wmi.WMI()
        
        # Query all logical disks
        for disk in c.Win32_LogicalDisk():
            if disk.DriveType == 2:  # Removable disk (USB)
                # Try to match with device
                # This is a simplified approach - in production, you'd need more robust matching
                if disk.DeviceID:
                    return disk.DeviceID
        
        # Alternative: Check all removable drives
        for disk in c.Win32_LogicalDisk(DriveType=2):
            if disk.DeviceID:
                return disk.DeviceID
                
    except Exception as e:
        print(f"[!] Error getting drive letter: {e}")
    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass
    
    return None


def get_all_removable_drives():
    """
    Get all removable drive letters currently mounted.
    
    PHASE 2 NEW FUNCTION: Lists all USB drives
    
    Returns:
        list: List of drive letters (e.g., ['E:', 'F:'])
    """
    try:
        import wmi
        import pythoncom
        pythoncom.CoInitialize()
        c = wmi.WMI()
        
        drives = []
        for disk in c.Win32_LogicalDisk(DriveType=2):  # Removable
            if disk.DeviceID:
                drives.append(disk.DeviceID)
        
        return drives
        
    except Exception as e:
        print(f"[!] Error getting removable drives: {e}")
        return []
    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass


def format_file_size(size_bytes):
    """
    Format file size in human-readable format.
    
    PHASE 2 NEW FUNCTION: For GUI display
    
    Args:
        size_bytes (int): File size in bytes
    
    Returns:
        str: Formatted size (e.g., '1.5 MB', '500 KB')
    """
    if size_bytes is None or size_bytes == 0:
        return '0 B'
    
    # Define units
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    # Convert to appropriate unit
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    # Format with appropriate precision
    if unit_index == 0:  # Bytes
        return f'{int(size)} {units[unit_index]}'
    else:
        return f'{size:.2f} {units[unit_index]}'


def calculate_duration(start_time_str, end_time_str):
    """
    Calculate duration between two timestamps.
    
    PHASE 2 NEW FUNCTION: For session duration tracking
    
    Args:
        start_time_str (str): Start timestamp (YYYY-MM-DD HH:MM:SS)
        end_time_str (str): End timestamp (YYYY-MM-DD HH:MM:SS)
    
    Returns:
        int: Duration in seconds, or 0 if error
    """
    try:
        from datetime import datetime
        
        start = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        
        duration = (end - start).total_seconds()
        return int(duration)
        
    except Exception as e:
        print(f"[!] Error calculating duration: {e}")
        return 0


def format_duration(seconds):
    """
    Format duration in human-readable format.
    
    PHASE 2 NEW FUNCTION: For GUI display
    
    Args:
        seconds (int): Duration in seconds
    
    Returns:
        str: Formatted duration (e.g., '2h 15m 30s')
    """
    if seconds is None or seconds <= 0:
        return '0s'
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f'{hours}h')
    if minutes > 0:
        parts.append(f'{minutes}m')
    if secs > 0 or not parts:
        parts.append(f'{secs}s')
    
    return ' '.join(parts)


def capture_screenshot(save_dir=None, prefix='screenshot'):
    """Capture the current screen and save it as a PNG file."""
    try:
        from PIL import ImageGrab
    except ImportError:
        print('[!] Pillow is required for screenshot capture. Install Pillow to enable this feature.')
        return None

    try:
        if not save_dir:
            save_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
        elif not os.path.isabs(save_dir):
            save_dir = os.path.join(os.path.dirname(__file__), save_dir)
        os.makedirs(save_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(save_dir, filename)

        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        print(f'[OK] Screenshot saved: {filepath}')
        return filepath
    except Exception as e:
        print(f'[ERROR] Screenshot capture failed: {e}')
        return None


def send_email_notification(subject, body, recipients, smtp_config, error_out=None, attachment_path=None):
    """Send a notification email using SMTP settings, optionally with an attachment."""
    try:
        if not recipients:
            err_msg = 'No recipients configured for email alerts.'
            print(f'[!] {err_msg}')
            if isinstance(error_out, list):
                error_out.append(err_msg)
            return False

        import smtplib
        from email.message import EmailMessage
        import ssl
        import mimetypes

        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = smtp_config.get('sender', 'usb-logger@example.com')
        message['To'] = ', '.join(recipients)
        message.set_content(body)

        if attachment_path and os.path.exists(attachment_path):
            try:
                ctype, encoding = mimetypes.guess_type(attachment_path)
                if ctype is None or encoding is not None:
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                with open(attachment_path, 'rb') as fp:
                    message.add_attachment(
                        fp.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=os.path.basename(attachment_path)
                    )
                print(f'[OK] Attached file to email: {attachment_path}')
            except Exception as attachment_err:
                print(f'[WARNING] Failed to attach file {attachment_path}: {attachment_err}')

        host = smtp_config.get('smtp_host')
        port = smtp_config.get('smtp_port', 587)
        use_tls = smtp_config.get('use_tls', True)
        username = smtp_config.get('username')
        password = smtp_config.get('password')

        if not host or not username or not password:
            err_msg = 'Incomplete SMTP configuration (Host, Username, or Password missing).'
            print(f'[!] {err_msg}')
            if isinstance(error_out, list):
                error_out.append(err_msg)
            return False

        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, timeout=10, context=context) as server:
                server.login(username, password)
                server.send_message(message)
        elif use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.starttls(context=context)
                server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.login(username, password)
                server.send_message(message)

        print('[OK] Email alert sent successfully')
        return True

    except Exception as e:
        print(f'[ERROR] Email alert failed: {e}')
        if isinstance(error_out, list):
            error_out.append(str(e))
        return False
