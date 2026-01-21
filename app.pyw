"""
Nibor Calculation Terminal - Windows Launcher (no console)

This .pyw file runs the application without showing a console window.
Double-click this file to start the app on Windows.
"""
import sys
import os
import runpy

# Ensure the script directory is in the path
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Run main.py as __main__
runpy.run_path(os.path.join(script_dir, "main.py"), run_name="__main__")
