"""
Application configuration for the File Concatenator.
"""

import os
import json

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
BACKUP_DIR = os.path.join(OUTPUT_DIR, 'backups')

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Load output filename from settings if available
try:
    # Read directly from config.json to avoid circular imports
    config_path = os.path.join(BASE_DIR, "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            output_filename = config.get("output", {}).get("filename", "master.txt")
    else:
        output_filename = "master.txt"
except Exception:
    output_filename = "master.txt"

# Add this alias to maintain compatibility with gui_components.py
DEFAULT_OUTPUT_FILE = output_filename