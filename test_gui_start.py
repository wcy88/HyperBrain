#!/usr/bin/env python3
"""
Test GUI startup script - minimal test to verify application launches
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtWidgets import QApplication
    from hyperbrain.core.config import get_config
    from hyperbrain.core.brain import get_brain, reset_brain
    from hyperbrain.core.logger import setup_logging
    
    print("=" * 60)
    print("HyperBrain GUI Test Launcher")
    print("=" * 60)
    print()
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    print("[1/4] Loading configuration...")
    config = get_config()
    print("  ✓ Configuration loaded")
    
    print("[2/4] Initializing Brain...")
    import asyncio
    brain = get_brain(config=config)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(brain.initialize())
    loop.run_until_complete(brain.start())
    loop.close()
    print("  ✓ Brain initialized and started")
    
    print("[3/4] Creating QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("HyperBrain-Test")
    print("  ✓ QApplication created")
    
    print("[4/4] Loading MainWindow...")
    from hyperbrain.ui.main_window import MainWindow
    window = MainWindow(brain=brain)
    print("  ✓ MainWindow created")
    
    print()
    print("✓ All tests passed! Application should launch now.")
    print()
    print("Click 'Close' button or use Ctrl+C to exit.")
    print("=" * 60)
    print()
    
    window.show()
    
    exit_code = app.exec()
    
    print()
    print("Cleaning up...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(brain.shutdown())
    loop.close()
    reset_brain()
    print("  ✓ Cleanup complete")
    print()
    print("Application exited normally.")
    
    sys.exit(exit_code)
    
except Exception as e:
    print()
    print("=" * 60)
    print("ERROR: Failed to launch application")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print()
    print("Stack trace:")
    traceback.print_exc()
    print()
    print("=" * 60)
    sys.exit(1)
