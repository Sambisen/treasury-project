"""
NIBOR Recon Launcher
Double-click this file to start the app.
"""
import os
import sys

# Change to the directory where this file is located
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run main.py
exec(open("main.py").read())
