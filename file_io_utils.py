"""
File I/O utilities for the File Concatenator application.

This module provides core file operations used by the GUI application:
- Creating backups of the master file
- Loading file contents
- Appending content to the master file
- Writing directory structure information

All operations include error handling and logging support.
"""

import os
import shutil
from datetime import datetime
from app_config import OUTPUT_DIR, BACKUP_DIR

def create_backup(master_filename, log):
    """
    Create a timestamped backup of the master file.
    
    Args:
        master_filename (str): Path to the master file
        log (callable): Function to log operations and errors
        
    The backup filename includes the current timestamp for uniqueness.
    """
    if os.path.exists(master_filename):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_name = f"master_{timestamp}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        try:
            shutil.copy2(master_filename, backup_path)
            log(f"Backup created: {backup_path}")
        except Exception as e:
            log(f"Error creating backup: {e}")
    else:
        log("No existing master file found; skipping backup.")

def load_file(filename, log):
    """
    Read and return the contents of a file.
    
    Args:
        filename (str): Path to the file to read
        log (callable): Function to log operations and errors
        
    Returns:
        str: File contents if successful, None if an error occurs
        
    Uses UTF-8 encoding for file reading.
    """
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            log(f"Error reading {filename}: {e}")
            return None
    else:
        log(f"File not found: {filename}")
        return None

def append_to_master(master_filename, filename, content, log):
    """
    Append file content to the master file with a header.
    
    Args:
        master_filename (str): Path to the master file
        filename (str): Path of the source file (for header)
        content (str): Content to append
        log (callable): Function to log operations and errors
        
    The content is preceded by a header indicating its source file.
    """
    try:
        with open(master_filename, 'a', encoding='utf-8') as master_file:
            master_file.write(f"\n\n# Content from {filename}\n\n")
            master_file.write(content)
        log(f"Appended content from {filename}")
    except Exception as e:
        log(f"Error appending {filename}: {e}")

def write_directory_structure(master_filename, file_list, log):
    try:
        with open(master_filename, 'a', encoding='utf-8') as master_file:
            master_file.write("# Directory Structure\n\n")
            for file in file_list:
                master_file.write(f"{file}\n")
            master_file.write("\n\n")
        log("Directory structure written to master file.")
    except Exception as e:
        log(f"Error writing directory structure: {e}")
