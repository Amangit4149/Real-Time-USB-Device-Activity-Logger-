"""
PHASE 2 QUICK DEMO SCRIPT
--------------------------
Automated demonstration of Phase 2 features
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import (init_db, insert_log, insert_file_log, fetch_all_logs, 
                      fetch_file_logs, count_sessions_today, count_total_file_events, 
                      count_large_transfers, get_log_count)
from utils import get_timestamp, get_username, format_file_size, format_duration

def demo_phase2():
    """
    Demonstrate Phase 2 features with sample data.
    """
    print("=" * 60)
    print("PHASE 2 DEMO - Real Time USB Activity Logger + File Monitor")
    print("=" * 60)
    print()
    
    # Initialize database
    print("1️⃣  Initializing Phase 2 database schema...")
    init_db()
    print()
    
    # Get username
    username = get_username()
    print(f"2️⃣  Current user: {username}")
    print()
    
    # Simulate USB connection with session tracking
    print("3️⃣  Simulating USB device connection...")
    timestamp = get_timestamp()
    insert_log(
        event_type='CONNECTED',
        device_name='SanDisk USB 3.0',
        device_id='USB\\VID_0781&PID_5567\\4C530001234567890123',
        vendor_id='0781',
        product_id='5567',
        serial_number='4C530001234567890123',
        timestamp=timestamp,
        connect_time=timestamp,
        username=username
    )
    print(f"   ✅ USB connected at {timestamp}")
    print(f"   ✅ Username logged: {username}")
    print()
    
    # Simulate file operations
    print("4️⃣  Simulating file operations on USB drive...")
    
    # Small file creation
    insert_file_log(
        device_id='USB\\VID_0781&PID_5567\\4C530001234567890123',
        file_path='E:\\documents\\report.docx',
        event_type='CREATED',
        file_size=2048576,  # 2 MB
        username=username,
        timestamp=get_timestamp(),
        risk_flag='NORMAL'
    )
    print(f"   ✅ File created: report.docx ({format_file_size(2048576)})")
    
    # File modification
    insert_file_log(
        device_id='USB\\VID_0781&PID_5567\\4C530001234567890123',
        file_path='E:\\documents\\report.docx',
        event_type='MODIFIED',
        file_size=2150000,  # 2.05 MB
        username=username,
        timestamp=get_timestamp(),
        risk_flag='NORMAL'
    )
    print(f"   ✅ File modified: report.docx ({format_file_size(2150000)})")
    
    # Large file transfer (>50MB) - POTENTIAL EXFILTRATION
    large_file_size = 75 * 1024 * 1024  # 75 MB
    insert_file_log(
        device_id='USB\\VID_0781&PID_5567\\4C530001234567890123',
        file_path='E:\\backup\\database_backup.zip',
        event_type='CREATED',
        file_size=large_file_size,
        username=username,
        timestamp=get_timestamp(),
        risk_flag='LARGE_TRANSFER'
    )
    print(f"   ⚠️  LARGE FILE DETECTED: database_backup.zip ({format_file_size(large_file_size)})")
    print(f"   ⚠️  Risk Flag: LARGE_TRANSFER")
    
    # File deletion
    insert_file_log(
        device_id='USB\\VID_0781&PID_5567\\4C530001234567890123',
        file_path='E:\\temp\\old_file.txt',
        event_type='DELETED',
        file_size=0,
        username=username,
        timestamp=get_timestamp(),
        risk_flag='NORMAL'
    )
    print(f"   ✅ File deleted: old_file.txt")
    print()
    
    # Simulate USB disconnection with duration
    print("5️⃣  Simulating USB device disconnection...")
    import time
    time.sleep(1)  # Simulate some usage time
    disconnect_time = get_timestamp()
    
    # In real scenario, this would be calculated from connect_time
    # For demo, we'll use a sample duration
    usage_duration = 125  # 2 minutes 5 seconds
    
    from database import update_session_end
    update_session_end(
        device_id='USB\\VID_0781&PID_5567\\4C530001234567890123',
        disconnect_time=disconnect_time,
        usage_duration=usage_duration
    )
    
    insert_log(
        event_type='DISCONNECTED',
        device_name='SanDisk USB 3.0',
        device_id='USB\\VID_0781&PID_5567\\4C530001234567890123',
        vendor_id='0781',
        product_id='5567',
        serial_number='4C530001234567890123',
        timestamp=disconnect_time,
        disconnect_time=disconnect_time
    )
    print(f"   ✅ USB disconnected at {disconnect_time}")
    print(f"   ✅ Session duration: {format_duration(usage_duration)}")
    print()
    
    # Display analytics
    print("6️⃣  Analytics Dashboard:")
    print(f"   📊 Sessions Today: {count_sessions_today()}")
    print(f"   📊 Total File Events: {count_total_file_events()}")
    print(f"   📊 Large Transfers: {count_large_transfers()}")
    print()
    
    # Display USB logs
    print("7️⃣  USB Device Activity Log:")
    usb_logs = fetch_all_logs()
    for log in usb_logs[:5]:  # Show last 5
        event_type = log[1]
        device_name = log[2]
        username_log = log[11] or 'N/A'
        timestamp_log = log[7]
        duration = format_duration(log[10]) if log[10] else 'N/A'
        
        print(f"   [{event_type:12}] {device_name:20} | User: {username_log:10} | Duration: {duration:8} | {timestamp_log}")
    print()
    
    # Display file logs
    print("8️⃣  File Activity Log:")
    file_logs = fetch_file_logs(limit=10)
    for log in file_logs:
        event_type = log[3]
        file_path = os.path.basename(log[2])
        file_size = format_file_size(log[4]) if log[4] else '0 B'
        risk_flag = log[7] or 'NORMAL'
        risk_indicator = '⚠️ ' if risk_flag == 'LARGE_TRANSFER' else '✅ '
        
        print(f"   {risk_indicator}[{event_type:8}] {file_path:30} | Size: {file_size:10} | Risk: {risk_flag}")
    print()
    
    # Summary
    print("=" * 60)
    print("✅ PHASE 2 DEMO COMPLETE!")
    print("=" * 60)
    print()
    print("Key Features Demonstrated:")
    print("  ✅ Session tracking (connect time, disconnect time, duration)")
    print("  ✅ Username logging for accountability")
    print("  ✅ File operation monitoring (create, modify, delete)")
    print("  ✅ Large file transfer detection (>50MB)")
    print("  ✅ Risk flagging (NORMAL vs LARGE_TRANSFER)")
    print("  ✅ Analytics dashboard")
    print("  ✅ Dual logging (USB hardware + file activity)")
    print()
    print("🎯 Ready for GUI demonstration!")
    print("   Run: python main.py")
    print()

if __name__ == "__main__":
    demo_phase2()
