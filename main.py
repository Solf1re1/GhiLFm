"""
ApexClicker - Next-Generation Advanced Windows Auto Clicker.
Main entry point.
"""

import sys
import os

# Add root folder to sys.path so modules resolve cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apex_clicker.ui.main_window import MainWindow
from apex_clicker.core.input_driver import HighPrecisionTimer


def main():
    # Clear one-time bootloader reset flag if present
    if "PYINSTALLER_RESET_ENVIRONMENT" in os.environ:
        del os.environ["PYINSTALLER_RESET_ENVIRONMENT"]

    # Enable high-resolution Windows multimedia timer (1ms granularity)
    HighPrecisionTimer.enable()

    try:
        app = MainWindow()
        app.mainloop()
    finally:
        # Cleanup timer on exit
        HighPrecisionTimer.disable()


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
