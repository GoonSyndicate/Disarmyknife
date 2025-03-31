"""
Settings Manager for the File Concatenator application.

This module provides functionality for:
- Saving application settings to a JSON file
- Loading settings from a JSON file
- Managing default settings
- Providing access to settings throughout the application
"""

import os
import json

# Define base directory here instead of importing from app_config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Default settings
DEFAULT_SETTINGS = {
    # Window configuration
    "window": {
        "width": 1200,
        "height": 800,
        "position_x": None,  # Will be set on first save if not specified
        "position_y": None   # Will be set on first save if not specified
    },
    
    # Directory settings
    "directories": {
        "last_directory": None
    },
    
    # Output settings
    "output": {
        "filename": "master.txt",
        "header_format": "default",  # Options: default, markdown, separator
        "include_line_numbers": False
    },
    
    # Editor settings
    "editor": {
        "theme": "monokai"
    },
    # Encoding settings
    "encoding": "cl100k_base",
    
    # Last session data
    "last_session": {
        "selected_files": [],
        "quick_notes": "",
        "editor_file": None
    }
}

# Settings file path
SETTINGS_FILE = os.path.join(BASE_DIR, "config.json")

class SettingsManager:
    """
    Manages application settings.
    
    This class encapsulates:
    - Loading settings from a JSON file
    - Saving settings to a JSON file
    - Providing defaults for missing settings
    - Getter/setter methods for individual settings
    """
    
    def __init__(self):
        """Initialize settings manager and load settings."""
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()
        
    def load_settings(self):
        """Load settings from the settings file."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                
                # Update defaults with loaded settings
                self._update_nested_dict(self.settings, loaded_settings)
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save current settings to the settings file."""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _update_nested_dict(self, d, u):
        """Recursively update nested dictionary d with values from u."""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    def get_setting(self, section, key, default=None):
        """Get a specific setting by section and key."""
        if section in self.settings and key in self.settings[section]:
            return self.settings[section][key]
        return default
    
    def set_setting(self, section, key, value):
        """Set a specific setting value."""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
    
    def get_window_settings(self):
        """Get window-related settings."""
        return self.settings["window"]
    
    def set_window_settings(self, width, height, x=None, y=None):
        """Update window settings."""
        self.settings["window"]["width"] = width
        self.settings["window"]["height"] = height
        if x is not None:
            self.settings["window"]["position_x"] = x
        if y is not None:
            self.settings["window"]["position_y"] = y
    
    def get_last_directory(self):
        """Get the last used directory."""
        return self.settings["directories"]["last_directory"]
    
    def set_last_directory(self, directory):
        """Set the last used directory."""
        self.settings["directories"]["last_directory"] = directory
    
    def get_output_settings(self):
        """Get output related settings."""
        return self.settings["output"]
    
    def set_output_filename(self, filename):
        """Set the default output filename."""
        self.settings["output"]["filename"] = filename
    
    def get_header_format(self):
        """Get the header format for file concatenation."""
        return self.settings["output"]["header_format"]
    
    def set_header_format(self, format_type):
        """Set the header format for file concatenation."""
        self.settings["output"]["header_format"] = format_type
    
    def get_include_line_numbers(self):
        """Check if line numbers should be included."""
        return self.settings["output"]["include_line_numbers"]
    
    def set_include_line_numbers(self, include):
        """Set whether to include line numbers."""
        self.settings["output"]["include_line_numbers"] = include
    
    def get_editor_theme(self):
        """Get the editor theme."""
        return self.settings["editor"]["theme"]
    
    def set_editor_theme(self, theme):
        """Set the editor theme."""
        self.settings["editor"]["theme"] = theme

    def get_encoding(self):
        """Get the encoding."""
        return self.settings["encoding"]
    
    def set_encoding(self, encoding):
        """Set the encoding."""
        self.settings["encoding"] = encoding
        
    def get_last_session(self):
        """Get the last session data."""
        return self.settings.get("last_session", {})
    
    def set_last_session(self, selected_files, quick_notes, editor_file):
        """
        Save the last session data.
        
        Args:
            selected_files (list): List of file paths in the selected files list
            quick_notes (str): Content of the quick notes text area
            editor_file (str): Path of the currently open file in editor, or None
        """
        self.settings["last_session"] = {
            "selected_files": list(selected_files),  # Convert to list in case it's a tuple
            "quick_notes": quick_notes,
            "editor_file": editor_file
        }

# Create a global instance
settings = SettingsManager()
