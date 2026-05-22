"""
EXPORT MODULE
-------------
Handles exporting USB logs to CSV format for external analysis.
"""

import csv
from database import fetch_all_logs
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
                'Timestamp'
            ])
            
            # Write data rows
            for log in logs:
                writer.writerow(log)
        
        success_msg = f"Successfully exported {len(logs)} logs to {filename}"
        print(f"[✓] {success_msg}")
        
        return (True, success_msg, filepath)
        
    except Exception as e:
        error_msg = f"Export failed: {str(e)}"
        print(f"[✗] {error_msg}")
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


def get_export_directory():
    """
    Get the directory where CSV exports are saved.
    
    Returns:
        str: Absolute path to export directory
    """
    return os.path.dirname(__file__)
