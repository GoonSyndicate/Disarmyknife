import os
import shutil
from datetime import datetime

def create_backup(master_filename, log):
    if os.path.exists(master_filename):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f"{master_filename}.{timestamp}.bak"
        try:
            shutil.copy2(master_filename, backup_filename)
            log(f"Backup created: {backup_filename}")
        except Exception as e:
            log(f"Error creating backup: {e}")
    else:
        log("No existing master file found; skipping backup.")

def load_file(filename, log):
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
