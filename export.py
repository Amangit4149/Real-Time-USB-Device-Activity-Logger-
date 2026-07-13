"""
EXPORT MODULE
-------------
Handles exporting USB logs to CSV format for external analysis.
"""

import csv
import json
from database import fetch_all_logs, fetch_file_logs
import os
from datetime import datetime


def export_to_csv(filename=None):
    """
    Export all USB logs from database to a CSV file.
    
    CSV Format:
    - Header row with column names
    - One row per log entry
    - Comma-separated values
    - Can be opened in Excel, Google Sheets, etc.
    
    Args:
        filename (str): Optional custom filename. If None, generates timestamped filename.
    
    Returns:
        tuple: (success: bool, message: str, filepath: str)
    """
    try:
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"usb_logs_{timestamp}.csv"
        
        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # Get full path (save in same directory as script)
        script_dir = os.path.dirname(__file__)
        filepath = os.path.join(script_dir, filename)
        
        # Fetch all logs from database
        logs = fetch_all_logs()
        
        if not logs:
            return (False, "No logs to export", "")
        
        # Write to CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row
            writer.writerow([
                'ID',
                'Event Type',
                'Device Name',
                'Device ID',
                'Vendor ID',
                'Product ID',
                'Serial Number',
                'Timestamp',
                'Connect Time',
                'Disconnect Time',
                'Usage Duration',
                'Username'
            ])
            
            # Write data rows
            for log in logs:
                writer.writerow(log)
        
        success_msg = f"Successfully exported {len(logs)} logs to {filename}"
        print(f"[OK] {success_msg}")
        
        return (True, success_msg, filepath)
        
    except Exception as e:
        error_msg = f"Export failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return (False, error_msg, "")


def export_filtered_logs(event_type=None, start_date=None, end_date=None, filename=None):
    """
    Export filtered logs to CSV.
    
    This is an advanced feature for future enhancement.
    Currently exports all logs, but can be extended to support filtering.
    
    Args:
        event_type (str): Filter by 'CONNECTED' or 'DISCONNECTED'
        start_date (str): Start date for filtering
        end_date (str): End date for filtering
        filename (str): Output filename
    
    Returns:
        tuple: (success: bool, message: str, filepath: str)
    """
    # For now, just export all logs
    # Future enhancement: implement filtering logic
    return export_to_csv(filename)


def export_to_json(filename=None):
    """
    Export USB and file logs to a JSON file.
    """
    try:
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"usb_logs_{timestamp}.json"

        if not filename.endswith('.json'):
            filename += '.json'

        script_dir = os.path.dirname(__file__)
        filepath = os.path.join(script_dir, filename)

        usb_logs = fetch_all_logs()
        file_logs = fetch_file_logs()

        if not usb_logs and not file_logs:
            return (False, 'No logs to export', '')

        payload = {
            'usb_logs': [
                {
                    'id': log[0],
                    'event_type': log[1],
                    'device_name': log[2],
                    'device_id': log[3],
                    'vendor_id': log[4],
                    'product_id': log[5],
                    'serial_number': log[6],
                    'timestamp': log[7],
                    'connect_time': log[8],
                    'disconnect_time': log[9],
                    'usage_duration': log[10],
                    'username': log[11]
                }
                for log in usb_logs
            ],
            'file_logs': [
                {
                    'id': log[0],
                    'device_id': log[1],
                    'file_path': log[2],
                    'event_type': log[3],
                    'file_size': log[4],
                    'username': log[5],
                    'timestamp': log[6],
                    'risk_flag': log[7]
                }
                for log in file_logs
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as json_file:
            json.dump(payload, json_file, indent=2)

        success_msg = f"Successfully exported {len(usb_logs)} USB logs and {len(file_logs)} file logs to {filename}"
        print(f"[OK] {success_msg}")
        return (True, success_msg, filepath)

    except Exception as e:
        error_msg = f"JSON export failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return (False, error_msg, "")


def get_export_directory():
    """
    Get the directory where CSV exports are saved.
    
    Returns:
        str: Absolute path to export directory
    """
    return os.path.dirname(__file__)
