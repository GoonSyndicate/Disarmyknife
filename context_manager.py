"""
Context Manager for the File Concatenator application.

This module provides functionality for managing working contexts:
- Saving and loading named contexts
- Importing and exporting contexts
- Managing context metadata

A context represents a workspace state including selected files and notes.
"""

import os
import json
from datetime import datetime
from tkinter import messagebox, filedialog
import file_io_utils
from app_config import OUTPUT_DIR

class ContextManager:
    """
    Manages working contexts for the application.
    
    A context contains:
    - A list of selected files
    - User notes
    - Creation/modification timestamp
    
    This class handles saving, loading, importing and exporting contexts
    to make it easy to switch between different working environments.
    """
    
    def __init__(self, log_callback):
        """
        Initialize the context manager.
        
        Args:
            log_callback (callable): Function to use for logging operations
        """
        self.contexts = {}
        self.current_context = None
        self.log = log_callback
    
    def save_context(self, name, files, notes):
        """
        Save the current workspace as a named context.
        
        Args:
            name (str): Name for the context
            files (list): List of file paths in the context
            notes (str): User notes for the context
            
        Returns:
            bool: True if saved successfully
        """
        if not name.strip():
            messagebox.showwarning("Context Name Required", 
                                 "Please enter a name for your working context.")
            return False
        
        # Store the context
        self.contexts[name] = {
            'files': list(files),
            'notes': notes.strip(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.current_context = name
        self.log(f"Saved context: {name}")
        return True
    
    def get_context_names(self):
        """
        Get a sorted list of available context names.
        
        Returns:
            list: Sorted list of context names
        """
        return sorted(self.contexts.keys())
    
    def load_context(self, name):
        """
        Get the content of a named context.
        
        Args:
            name (str): Name of the context to load
            
        Returns:
            dict: The context data or None if not found
        """
        if name not in self.contexts:
            return None
            
        self.current_context = name
        self.log(f"Loaded context: {name}")
        return self.contexts[name]
    
    def get_current_context(self):
        """
        Get the currently active context.
        
        Returns:
            dict: Current context data or None if no context is active
        """
        if not self.current_context:
            return None
        return self.contexts.get(self.current_context)
    
    def export_context(self, output_format="markdown"):
        """
        Export the current context to a file.
        
        Args:
            output_format (str): Format to export (markdown or json)
            
        Returns:
            bool: True if export was successful
        """
        if not self.current_context:
            messagebox.showwarning("Export Context", "No context selected")
            return False
            
        # Determine file type based on format
        if output_format == "json":
            file_types = [("JSON files", "*.json"), ("All files", "*.*")]
            default_ext = ".json"
        else:
            file_types = [("Markdown", "*.md"), ("All files", "*.*")]
            default_ext = ".md"
            
        filename = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            initialdir=OUTPUT_DIR,
            initialfile=f"{self.current_context}{default_ext}",
            filetypes=file_types
        )
        
        if not filename:
            return False
            
        try:
            context = self.contexts[self.current_context]
            
            if output_format == "json":
                # Export as JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(context, f, indent=2)
            else:
                # Export as Markdown
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# {self.current_context}\n\n")
                    
                    # Write notes section
                    if context['notes'].strip():
                        f.write("## Notes\n\n")
                        f.write(context['notes'].strip() + "\n\n")
                    
                    # Write files section
                    f.write("## Files\n\n")
                    for file in context['files']:
                        f.write(f"- `{file}`\n")
                    
                    # Add file previews
                    f.write("\n## File Previews\n\n")
                    for file in context['files']:
                        if os.path.exists(file):
                            f.write(f"### {os.path.basename(file)}\n\n")
                            f.write("```\n")
                            content = file_io_utils.load_file(file, self.log)
                            if content:
                                # First 10 lines of each file
                                preview_lines = content.split('\n')[:10]
                                preview = '\n'.join(preview_lines)
                                f.write(preview)
                            else:
                                f.write("(Unable to read file)")
                            f.write("\n```\n\n")
            
            self.log(f"Exported context to {filename}")
            return True
            
        except Exception as e:
            self.log(f"Error exporting context: {e}")
            messagebox.showerror("Export Error", str(e))
            return False
    
    def import_context(self):
        """
        Import a context from a JSON file.
        
        Returns:
            str: Name of imported context or None if import failed
        """
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return None
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                context = json.load(f)
            
            # Use filename as context name
            name = os.path.splitext(os.path.basename(filename))[0]
            self.contexts[name] = context
            
            self.log(f"Imported context from {filename}")
            return name
            
        except Exception as e:
            self.log(f"Error importing context: {e}")
            messagebox.showerror("Import Error", str(e))
            return None
    
    def get_context_summary(self):
        """
        Get a summary of the current context.
        
        Returns:
            str: A short summary of the current context
        """
        if not self.current_context:
            return "No context loaded"
            
        context = self.contexts[self.current_context]
        files_count = len(context['files'])
        notes_preview = context['notes'][:50] + '...' if len(context['notes']) > 50 else context['notes']
        
        return f"Context: {self.current_context}\nFiles: {files_count}\nNotes: {notes_preview}"

    def help_text(self):
        """
        Return help text explaining contexts.
        
        Returns:
            str: Formatted help text
        """
        return """
        📸 Task Snapshots (formerly Working Contexts)

        A Task Snapshot lets you quickly save and restore your work setup:
        • Selected files relevant to your current task
        • Notes, prompts, or instructions for yourself or an LLM
        • Export to share with others or future you

        Example Uses:
        1. Create LLM prompt kits with relevant code files
        2. Switch between different parts of a project instantly
        3. Prepare multiple ChatGPT inputs without losing your place
        4. Track different aspects of a complex task

        How to Use:
        1. Select files related to your current task
        2. Add notes or instructions 
        3. The name will be auto-suggested, or customize it
        4. Click 'Save Snapshot'
        5. Later, select from the dropdown to restore everything

        Tip: The * indicator shows when your current work differs from 
        the saved snapshot. Save frequently to track your progress.
        """
