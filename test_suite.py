"""
TEST SUITE
----------
Comprehensive testing script for USB Activity Logger.
Run this to verify all components are working correctly.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all required modules can be imported."""
    print("\n" + "="*50)
    print("TEST 1: Module Imports")
    print("="*50)
    
    modules = [
        ('database', 'Database operations'),
        ('monitor', 'USB monitoring'),
        ('gui', 'GUI dashboard'),
        ('export', 'CSV export'),
        ('utils', 'Utility functions')
    ]
    
    all_passed = True
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name:12} - {description}")
        except ImportError as e:
            print(f"✗ {module_name:12} - FAILED: {e}")
            all_passed = False
    
    return all_passed


def test_dependencies():
    """Test if external dependencies are installed."""
    print("\n" + "="*50)
    print("TEST 2: External Dependencies")
    print("="*50)
    
    dependencies = [
        ('wmi', 'Windows Management Instrumentation'),
        ('win32com', 'Windows COM (pywin32)'),
        ('tkinter', 'GUI library'),
        ('sqlite3', 'Database'),
        ('csv', 'CSV export'),
        ('threading', 'Multi-threading')
    ]
    
    all_passed = True
    
    for dep_name, description in dependencies:
        try:
            __import__(dep_name)
            print(f"✓ {dep_name:12} - {description}")
        except ImportError as e:
            print(f"✗ {dep_name:12} - FAILED: {e}")
            all_passed = False
    
    return all_passed


def test_database():
    """Test database operations."""
    print("\n" + "="*50)
    print("TEST 3: Database Operations")
    print("="*50)
    
    try:
        from database import init_db, insert_log, fetch_all_logs, get_log_count
        from utils import get_timestamp
        
        # Initialize database
        print("Testing database initialization...")
        if not init_db():
            print("✗ Database initialization failed")
            return False
        print("✓ Database initialized")
        
        # Test insert
        print("Testing log insertion...")
        timestamp = get_timestamp()
        if not insert_log('CONNECTED', 'Test Device', 'USB\\VID_1234&PID_5678\\TEST123', 
                         '1234', '5678', 'TEST123', timestamp):
            print("✗ Insert failed")
            return False
        print("✓ Log inserted")
        
        # Test fetch
        print("Testing log retrieval...")
        logs = fetch_all_logs()
        if not logs:
            print("✗ Fetch failed")
            return False
        print(f"✓ Retrieved {len(logs)} log(s)")
        
        # Test count
        print("Testing log count...")
        count = get_log_count()
        print(f"✓ Total logs: {count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utils():
    """Test utility functions."""
    print("\n" + "="*50)
    print("TEST 4: Utility Functions")
    print("="*50)
    
    try:
        from utils import parse_device_id, get_timestamp, is_valid_usb_device
        
        # Test device ID parsing
        print("Testing device ID parsing...")
        test_id = "USB\\VID_0781&PID_5567\\4C530001234567890123"
        parsed = parse_device_id(test_id)
        
        if parsed['vid'] != '0781':
            print(f"✗ VID parsing failed: expected '0781', got '{parsed['vid']}'")
            return False
        print(f"✓ VID parsed: {parsed['vid']}")
        
        if parsed['pid'] != '5567':
            print(f"✗ PID parsing failed: expected '5567', got '{parsed['pid']}'")
            return False
        print(f"✓ PID parsed: {parsed['pid']}")
        
        if not parsed['serial']:
            print("✗ Serial parsing failed")
            return False
        print(f"✓ Serial parsed: {parsed['serial']}")
        
        # Test timestamp
        print("Testing timestamp generation...")
        timestamp = get_timestamp()
        if not timestamp:
            print("✗ Timestamp generation failed")
            return False
        print(f"✓ Timestamp: {timestamp}")
        
        # Test validation
        print("Testing USB device validation...")
        if not is_valid_usb_device(test_id):
            print("✗ Validation failed for valid device")
            return False
        print("✓ Valid device recognized")
        
        if is_valid_usb_device("NOT_A_USB_DEVICE"):
            print("✗ Validation failed for invalid device")
            return False
        print("✓ Invalid device rejected")
        
        return True
        
    except Exception as e:
        print(f"✗ Utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export():
    """Test CSV export functionality."""
    print("\n" + "="*50)
    print("TEST 5: CSV Export")
    print("="*50)
    
    try:
        from export import export_to_csv
        
        print("Testing CSV export...")
        success, message, filepath = export_to_csv("test_export.csv")
        
        if not success:
            print(f"✗ Export failed: {message}")
            return False
        
        print(f"✓ Export successful: {message}")
        
        # Check if file exists
        if os.path.exists(filepath):
            print(f"✓ File created: {filepath}")
            file_size = os.path.getsize(filepath)
            print(f"✓ File size: {file_size} bytes")
        else:
            print("✗ Export file not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Export test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitor():
    """Test USB monitoring (basic checks only)."""
    print("\n" + "="*50)
    print("TEST 6: USB Monitoring")
    print("="*50)
    
    try:
        from monitor import get_connected_usb_devices, is_monitoring_active
        
        print("Testing USB device enumeration...")
        devices = get_connected_usb_devices()
        print(f"✓ Found {len(devices)} USB device(s)")
        
        if devices:
            print("\nConnected devices:")
            for i, dev in enumerate(devices[:5], 1):  # Show first 5
                print(f"  {i}. {dev['name']}")
                print(f"     VID: {dev['vid']}, PID: {dev['pid']}")
        
        print("\nTesting monitoring status...")
        active = is_monitoring_active()
        print(f"✓ Monitoring active: {active}")
        
        return True
        
    except Exception as e:
        print(f"✗ Monitor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print(" USB ACTIVITY LOGGER - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Dependencies", test_dependencies),
        ("Database", test_database),
        ("Utilities", test_utils),
        ("Export", test_export),
        ("Monitor", test_monitor)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:20} {status}")
    
    print("="*60)
    print(f"TOTAL: {passed}/{total} tests passed ({passed*100//total}%)")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready for use.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        
        print("\n" + "="*60)
        if success:
            print("You can now run the application with: python main.py")
        else:
            print("Please fix the errors before running the application.")
        print("="*60)
        
        input("\nPress Enter to exit...")
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
