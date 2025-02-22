import os

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
BACKUP_DIR = os.path.join(OUTPUT_DIR, 'backups')

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# File paths
DEFAULT_OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'master.txt')
