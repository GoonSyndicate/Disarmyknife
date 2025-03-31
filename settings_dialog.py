"""
Settings Dialog for the File Concatenator application.

This module provides a dialog for configuring:
- Output formatting options
- Default values for application settings
- Editor preferences
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
from settings_manager import settings
from app_config import OUTPUT_DIR

class SettingsDialog(tk.Toplevel):
    """
    Dialog for configuring application settings.
    
    This dialog organizes settings into tabs:
    - Output: Controls formatting of concatenated output
    - Editor: Editor preferences
    - General: Application-wide settings
    """
    
    def __init__(self, parent):
        """Initialize settings dialog."""
        super().__init__(parent)
        self.parent = parent
        
        # Configure dialog
        self.title("Settings")
        self.geometry("500x400")
        self.resizable(True, True)
        self.transient(parent)  # Make dialog modal
        self.grab_set()  # Prevent interaction with main window
        
        # Center the dialog on the parent window
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_output_tab()
        self.create_editor_tab()
        self.create_general_tab()
        
        # Create buttons
        self.create_buttons()
        
    def create_output_tab(self):
        """Create the output settings tab."""
        output_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(output_tab, text="Output")
        
        # Output filename
        file_frame = ttk.LabelFrame(output_tab, text="Default Output File")
        file_frame.pack(fill='x', pady=5)
        
        filename_frame = ttk.Frame(file_frame)
        filename_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(filename_frame, text="Filename:").pack(side='left')
        self.output_filename = ttk.Entry(filename_frame)
        self.output_filename.pack(side='left', fill='x', expand=True, padx=5)
        self.output_filename.insert(0, settings.get_output_settings()["filename"])
        
        browse_btn = ttk.Button(filename_frame, text="Browse", command=self.browse_output_file)
        browse_btn.pack(side='left')
        
        # Header format
        header_frame = ttk.LabelFrame(output_tab, text="Header Format")
        header_frame.pack(fill='x', pady=5)
        
        self.header_var = tk.StringVar(value=settings.get_header_format())
        
        ttk.Radiobutton(
            header_frame, 
            text="Default (# Content from filename)", 
            variable=self.header_var,
            value="default"
        ).pack(anchor='w', padx=10, pady=2)
        
        ttk.Radiobutton(
            header_frame, 
            text="Markdown (## File: filename)", 
            variable=self.header_var,
            value="markdown"
        ).pack(anchor='w', padx=10, pady=2)
        
        ttk.Radiobutton(
            header_frame, 
            text="Separator (---- FILE: filename ----)", 
            variable=self.header_var,
            value="separator"
        ).pack(anchor='w', padx=10, pady=2)
        
        # Line numbers
        line_frame = ttk.LabelFrame(output_tab, text="Line Numbers")
        line_frame.pack(fill='x', pady=5)
        
        self.line_numbers_var = tk.BooleanVar(value=settings.get_include_line_numbers())
        ttk.Checkbutton(
            line_frame, 
            text="Include line numbers in output", 
            variable=self.line_numbers_var
        ).pack(anchor='w', padx=10, pady=5)
        
        # Preview section
        preview_frame = ttk.LabelFrame(output_tab, text="Preview")
        preview_frame.pack(fill='both', expand=True, pady=5)
        
        self.preview_text = tk.Text(preview_frame, height=5, wrap='none', font=("Courier New", 10))
        self.preview_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Update preview when settings change
        self.header_var.trace('w', self.update_preview)
        self.line_numbers_var.trace('w', self.update_preview)
        self.update_preview()
        
    def create_editor_tab(self):
        """Create the editor settings tab."""
        editor_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(editor_tab, text="Editor")
        
        # Theme selection
        theme_frame = ttk.LabelFrame(editor_tab, text="Default Theme")
        theme_frame.pack(fill='x', pady=5)
        
        # Theme combobox
        theme_select = ttk.Frame(theme_frame)
        theme_select.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(theme_select, text="Theme:").pack(side='left')
        
        # Same themes as in editor_manager
        from pygments.styles import get_all_styles
        available_themes = sorted(list(get_all_styles()))
        
        self.theme_var = tk.StringVar(value=settings.get_editor_theme())
        theme_combo = ttk.Combobox(
            theme_select, 
            textvariable=self.theme_var,
            values=available_themes,
            state='readonly'
        )
        theme_combo.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        # Font settings (could be added in a future enhancement)
        
    def create_general_tab(self):
        """Create the general settings tab."""
        general_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(general_tab, text="General")
        
        # Window settings
        window_frame = ttk.LabelFrame(general_tab, text="Window")
        window_frame.pack(fill='x', pady=5)
        
        window_size = ttk.Frame(window_frame)
        window_size.pack(fill='x', padx=5, pady=5)
        
        window_settings = settings.get_window_settings()
        
        ttk.Label(window_size, text="Default Width:").grid(row=0, column=0, sticky='w')
        self.width_var = tk.StringVar(value=str(window_settings["width"]))
        ttk.Entry(window_size, textvariable=self.width_var, width=6).grid(row=0, column=1, padx=5)
        
        ttk.Label(window_size, text="Default Height:").grid(row=0, column=2, sticky='w')
        self.height_var = tk.StringVar(value=str(window_settings["height"]))
        ttk.Entry(window_size, textvariable=self.height_var, width=6).grid(row=0, column=3, padx=5)
        
        # Remember last directory
        dir_frame = ttk.LabelFrame(general_tab, text="Directories")
        dir_frame.pack(fill='x', pady=5)
        
        last_dir = settings.get_last_directory() or "Not set"
        self.dir_var = tk.StringVar(value=last_dir)
        
        dir_display = ttk.Frame(dir_frame)
        dir_display.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(dir_display, text="Last Directory:").pack(side='left')
        ttk.Label(dir_display, textvariable=self.dir_var).pack(side='left', padx=5)
        
        ttk.Button(dir_display, text="Clear", command=self.clear_last_dir).pack(side='right')
        
        # Encoding settings
        encoding_frame = ttk.LabelFrame(general_tab, text="Encoding")
        encoding_frame.pack(fill='x', pady=5)
        
        encoding_select = ttk.Frame(encoding_frame)
        encoding_select.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(encoding_select, text="Encoding:").pack(side='left')
        
        # Same encodings as in token_utils
        from token_utils import get_available_encodings
        available_encodings = sorted(list(get_available_encodings()))
        
        self.encoding_var = tk.StringVar(value=settings.get_encoding())
        encoding_combo = ttk.Combobox(
            encoding_select, 
            textvariable=self.encoding_var,
            values=available_encodings,
            state='readonly'
        )
        encoding_combo.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
    def create_buttons(self):
        """Create action buttons at the bottom."""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side='right')
        
    def update_preview(self, *args):
        """Update the preview text based on current settings."""
        header_format = self.header_var.get()
        include_line_numbers = self.line_numbers_var.get()
        
        sample_file = "c:\\path\\to\\sample\\file.py"
        sample_content = "def hello_world():\n    print('Hello, World!')\n\nhello_world()"
        
        # Clear the preview
        self.preview_text.delete('1.0', 'end')
        
        # Add the header based on format
        if header_format == "markdown":
            header = f"## File: {sample_file}\n\n"
        elif header_format == "separator":
            header = f"----------------------\nFILE: {sample_file}\n----------------------\n\n"
        else:  # default
            header = f"# Content from {sample_file}\n\n"
            
        self.preview_text.insert('end', header)
        
        # Add content, with line numbers if enabled
        if include_line_numbers:
            lines = sample_content.split('\n')
            for i, line in enumerate(lines):
                self.preview_text.insert('end', f"{i+1:4d}: {line}\n")
        else:
            self.preview_text.insert('end', sample_content)
            
    def browse_output_file(self):
        """Open dialog to select output file."""
        filename = filedialog.asksaveasfilename(
            initialdir=OUTPUT_DIR,
            initialfile=self.output_filename.get(),
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            # Just get the filename without path
            self.output_filename.delete(0, 'end')
            self.output_filename.insert(0, os.path.basename(filename))
            
    def clear_last_dir(self):
        """Clear the last directory setting."""
        self.dir_var.set("Not set")
            
    def save_settings(self):
        """Save all settings."""
        try:
            # Save output settings
            settings.set_output_filename(self.output_filename.get())
            settings.set_header_format(self.header_var.get())
            settings.set_include_line_numbers(self.line_numbers_var.get())
            
            # Save editor settings
            settings.set_editor_theme(self.theme_var.get())
            
            # Save general settings
            try:
                width = int(self.width_var.get())
                height = int(self.height_var.get())
                settings.set_window_settings(width, height)
            except ValueError:
                # Ignore invalid values for width/height
                pass
                
            if self.dir_var.get() == "Not set":
                settings.set_last_directory(None)
                
            # Save encoding setting
            settings.set_encoding(self.encoding_var.get())
                
            # Save all settings to file
            settings.save_settings()
            
            # Destroy dialog
            self.destroy()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            tk.messagebox.showerror("Error", f"Could not save settings: {e}")
