"""
NIBOR Recon Launcher
Double-click this file to start the app (works from anywhere).
"""
import os
import subprocess
import sys
from pathlib import Path

# Project location (works for all users via USERPROFILE)
project_dir = Path.home() / "OneDrive - Swedbank" / "GroupTreasury-ShortTermFunding - Documents" / "Samba" / "Samba" / "Gitnewnew"

# Run main.py from project directory
subprocess.Popen(
    [sys.executable, "main.py"],
    cwd=str(project_dir),
    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
)
