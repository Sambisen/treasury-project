"""
NIBOR Recon Launcher
Double-click this file to start the app.
"""
import os
import subprocess
import sys

# Get the directory where this file is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Run main.py from that directory
subprocess.Popen(
    [sys.executable, "main.py"],
    cwd=script_dir,
    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
)
