"""
MAIN APPLICATION
----------------
Entry point for the Real Time USB Activity Logger application.

This module:
1. Initializes the database
2. Starts USB monitoring in background thread
3. Launches the GUI
4. Manages application lifecycle

Threading is crucial here because:
- GUI must remain responsive
- USB monitoring runs continuously
- Both must operate simultaneously
"""

import sys
import os
from database import init_db
from monitor import start_monitoring, stop_monitoring

# Prefer PyQt6 GUI if available, otherwise fall back to Tkinter GUI
try:
    from gui_qt import launch_gui
except Exception:
    from gui import launch_gui
    import tkinter as tk
    from tkinter import messagebox


def initialize_application():
    """
    Initialize all application components.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    print("=" * 50)
    print("Real Time USB Activity Logger - INITIALIZATION")
    print("=" * 50)
    
    # Step 1: Initialize database
    print("\n[1/2] Initializing database...")
    if not init_db():
        print("[ERROR] Database initialization failed!")
        return False
    
    # Step 2: Start USB monitoring
    print("\n[2/2] Starting USB monitoring...")
    if not start_monitoring():
        print("[ERROR] Failed to start USB monitoring!")
        return False
    
    print("\n" + "=" * 50)
    print("INITIALIZATION COMPLETE")
    print("=" * 50 + "\n")
    
    return True


def main():
    """
    Main application entry point.
    
    Execution flow:
    1. Initialize database
    2. Start background USB monitoring thread
    3. Launch GUI (runs in main thread)
    4. Clean shutdown when GUI closes
    """
    try:
        # Initialize application components
        if not initialize_application():
            print("\n[ERROR] Application initialization failed!")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Launch GUI (blocking call - runs until window closed)
        print("[OK] Launching GUI...")
        launch_gui()
        
    except KeyboardInterrupt:
        print("\n\n[!] Keyboard interrupt detected")
    
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup: Stop monitoring
        print("\n[OK] Shutting down...")
        stop_monitoring()
        print("[OK] Application closed successfully")


if __name__ == "__main__":
    # Check if running on Windows
    if sys.platform != 'win32':
        print("[ERROR] This application only works on Windows!")
        print("    WMI (Windows Management Instrumentation) is required.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Run main application
    main()
