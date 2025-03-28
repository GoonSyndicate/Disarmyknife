"""
Editor Manager for the File Concatenator application.

This module provides a rich text editing component with:
- Syntax highlighting for various languages
- Line numbering
- File loading and saving
- Change tracking
- Find and replace functionality
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.font import Font
import pygments
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.token import Token
from pygments.styles import get_all_styles, get_style_by_name
import file_io_utils
from app_config import OUTPUT_DIR
import re

# Search dialog for find/replace functionality
class SearchDialog(tk.Toplevel):
    """
    Dialog window for text search and replace operations.
    
    Provides:
    - Find functionality
    - Replace functionality
    - Case sensitivity option
    - Regular expression support
    """
    
    def __init__(self, parent, editor, mode="find"):
        """
        Initialize the search dialog.
        
        Args:
            parent: The parent window
            editor: The text editor widget to search in
            mode: Either "find" or "replace"
        """
        super().__init__(parent)
        self.editor = editor
        self.mode = mode
        
        # Configure window
        self.title("Find" if mode == "find" else "Find and Replace")
        self.transient(parent)  # Make dialog modal
        self.resizable(False, False)
        
        # Set window position near the text widget
        x = parent.winfo_rootx() + 50
        y = parent.winfo_rooty() + 50
        self.geometry(f"+{x}+{y}")
        
        # Create dialog contents
        self.create_widgets()
        
        # Bind keys
        self.bind("<Escape>", lambda e: self.destroy())
        
        # Focus the search entry
        self.search_entry.focus_set()
        
        # Internal state
        self.last_search = None
        self.last_index = "1.0"
        self.wrap_occurred = False
        self.match_indices = []
        self.current_match_index = -1
        
    def create_widgets(self):
        """Create and arrange the dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill='both', expand=True)
        
        # Search entry
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', pady=3)
        
        ttk.Label(search_frame, text="Find:").pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='left', fill='x', expand=True)
        
        # Replace entry (if in replace mode)
        if self.mode == "replace":
            replace_frame = ttk.Frame(main_frame)
            replace_frame.pack(fill='x', pady=3)
            
            ttk.Label(replace_frame, text="Replace with:").pack(side='left', padx=(0, 5))
            
            self.replace_var = tk.StringVar()
            self.replace_entry = ttk.Entry(replace_frame, textvariable=self.replace_var, width=30)
            self.replace_entry.pack(side='left', fill='x', expand=True)
        
        # Options frame
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill='x', pady=(10, 3))
        
        # Case sensitivity checkbox
        self.case_sensitive = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Match case", variable=self.case_sensitive).pack(side='left')
        
        # Regexp checkbox
        self.use_regexp = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Regular expression", variable=self.use_regexp).pack(side='left', padx=(10, 0))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=(10, 0))
        
        # Find buttons
        ttk.Button(buttons_frame, text="Find Next", command=self.find_next).pack(side='left')
        ttk.Button(buttons_frame, text="Find All", command=self.find_all).pack(side='left', padx=(5, 0))
        
        # Replace buttons (if in replace mode)
        if self.mode == "replace":
            ttk.Button(buttons_frame, text="Replace", command=self.replace_current).pack(side='left', padx=(5, 0))
            ttk.Button(buttons_frame, text="Replace All", command=self.replace_all).pack(side='left', padx=(5, 0))
        
        # Close button
        ttk.Button(buttons_frame, text="Close", command=self.destroy).pack(side='right')
        
        # Status label
        self.status_var = tk.StringVar()
        ttk.Label(main_frame, textvariable=self.status_var).pack(pady=(10, 0))

    def find_next(self, from_current=True):
        """
        Find the next occurrence of the search text.
        
        Args:
            from_current: If True, search from the current cursor position
                          If False, search from the beginning of the document
        
        Returns:
            bool: True if a match was found, False otherwise
        """
        search_text = self.search_var.get()
        if not search_text:
            self.status_var.set("Please enter text to search for")
            return False
            
        # Remove any existing highlight
        self.editor.tag_remove("search_highlight", "1.0", "end")
        self.editor.tag_remove("current_match", "1.0", "end")
        
        # Get the search parameters
        if from_current:
            start_pos = self.editor.index("insert")
        else:
            start_pos = "1.0"
            
        case_sensitive = self.case_sensitive.get()
        use_regexp = self.use_regexp.get()
        
        # Perform the search
        if use_regexp:
            try:
                if case_sensitive:
                    pattern = re.compile(search_text)
                else:
                    pattern = re.compile(search_text, re.IGNORECASE)
                    
                # Get text content to search
                content = self.editor.get(start_pos, "end")
                
                # Convert start position to character offset
                start_line, start_char = map(int, start_pos.split("."))
                start_offset = sum(len(line) + 1 for line in self.editor.get("1.0", start_pos).split("\n")) - 1
                
                # Search for match
                match = pattern.search(content)
                if match:
                    match_start, match_end = match.span()
                    match_start += start_offset
                    match_end += start_offset
                    
                    # Convert to line.char format
                    start_index = self.editor.index(f"1.0 + {match_start} chars")
                    end_index = self.editor.index(f"1.0 + {match_end} chars")
                    
                    # Move cursor and highlight
                    self.editor.mark_set("insert", start_index)
                    self.editor.see(start_index)
                    self.editor.tag_add("current_match", start_index, end_index)
                    self.editor.tag_config("current_match", background="yellow")
                    
                    self.status_var.set(f"Match found")
                    return True
                else:
                    # If not found and we're already searching from the beginning
                    if not from_current:
                        self.status_var.set("No matches found")
                        return False
                    
                    # Otherwise wrap around and search from the beginning
                    self.wrap_occurred = True
                    return self.find_next(False)
            except re.error as e:
                self.status_var.set(f"Invalid regular expression: {e}")
                return False
        else:
            # Standard text search
            kwargs = {"backwards": False, "nocase": not case_sensitive}
            
            result = self.editor.search(search_text, start_pos, "end", **kwargs)
            
            if result:
                match_end = f"{result}+{len(search_text)}c"
                
                # Move cursor and highlight
                self.editor.mark_set("insert", result)
                self.editor.see(result)
                self.editor.tag_add("current_match", result, match_end)
                self.editor.tag_config("current_match", background="yellow")
                
                self.status_var.set("Match found")
                return True
            else:
                # If not found and we're already searching from the beginning
                if not from_current:
                    self.status_var.set("No matches found")
                    return False
                
                # Otherwise wrap around and search from the beginning
                self.wrap_occurred = True
                return self.find_next(False)

    def find_all(self):
        """Find and highlight all occurrences of the search text."""
        search_text = self.search_var.get()
        if not search_text:
            self.status_var.set("Please enter text to search for")
            return
            
        # Clear existing highlights
        self.editor.tag_remove("search_highlight", "1.0", "end")
        self.editor.tag_remove("current_match", "1.0", "end")
        
        # Get search parameters
        case_sensitive = self.case_sensitive.get()
        use_regexp = self.use_regexp.get()
        
        count = 0
        start_pos = "1.0"
        
        if use_regexp:
            try:
                if case_sensitive:
                    pattern = re.compile(search_text)
                else:
                    pattern = re.compile(search_text, re.IGNORECASE)
                    
                content = self.editor.get("1.0", "end")
                
                for match in pattern.finditer(content):
                    match_start, match_end = match.span()
                    
                    # Convert to line.char format
                    start_index = self.editor.index(f"1.0 + {match_start} chars")
                    end_index = self.editor.index(f"1.0 + {match_end} chars")
                    
                    # Highlight match
                    self.editor.tag_add("search_highlight", start_index, end_index)
                    count += 1
            except re.error as e:
                self.status_var.set(f"Invalid regular expression: {e}")
                return
        else:
            # Standard text search
            kwargs = {"backwards": False, "nocase": not case_sensitive}
            
            while True:
                result = self.editor.search(search_text, start_pos, "end", **kwargs)
                if not result:
                    break
                    
                match_end = f"{result}+{len(search_text)}c"
                self.editor.tag_add("search_highlight", result, match_end)
                start_pos = match_end
                count += 1
                
        # Configure the highlight tag
        self.editor.tag_config("search_highlight", background="lightgreen")
        
        # Update status
        self.status_var.set(f"{count} matches found")

    def replace_current(self):
        """Replace the current match with the replacement text."""
        if not self.editor.tag_ranges("current_match"):
            # No current selection, try to find next match first
            if not self.find_next():
                return
                
        replace_text = self.replace_var.get()
        
        # Get the current match range
        start, end = self.editor.tag_ranges("current_match")[0], self.editor.tag_ranges("current_match")[1]
        
        # Replace the text
        self.editor.delete(start, end)
        self.editor.insert(start, replace_text)
        
        # Update status
        self.status_var.set("Replaced occurrence")
        
        # Find next occurrence
        self.find_next()

    def replace_all(self):
        """Replace all occurrences of the search text with the replacement text."""
        search_text = self.search_var.get()
        replace_text = self.replace_var.get()
        
        if not search_text:
            self.status_var.set("Please enter text to search for")
            return
            
        # Get search parameters
        case_sensitive = self.case_sensitive.get()
        use_regexp = self.use_regexp.get()
        
        # Clear existing highlights
        self.editor.tag_remove("search_highlight", "1.0", "end")
        self.editor.tag_remove("current_match", "1.0", "end")
        
        if use_regexp:
            try:
                # Prepare regexp
                if case_sensitive:
                    pattern = re.compile(search_text)
                else:
                    pattern = re.compile(search_text, re.IGNORECASE)
                
                # Get content
                content = self.editor.get("1.0", "end-1c")
                
                # Perform replacement
                new_content, count = pattern.subn(replace_text, content)
                
                # Update editor content
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", new_content)
            except re.error as e:
                self.status_var.set(f"Invalid regular expression: {e}")
                return
        else:
            # Simple text replacement
            count = 0
            start_pos = "1.0"
            kwargs = {"backwards": False, "nocase": not case_sensitive}
            
            # Use a modified algorithm to prevent position shifts during replacement
            while True:
                result = self.editor.search(search_text, start_pos, "end", **kwargs)
                if not result:
                    break
                    
                match_end = f"{result}+{len(search_text)}c"
                
                # Replace text
                self.editor.delete(result, match_end)
                self.editor.insert(result, replace_text)
                
                # Move to position after replacement
                start_pos = f"{result}+{len(replace_text)}c"
                count += 1
        
        # Update status
        self.status_var.set(f"Replaced {count} occurrences")

class EditorManager:
    """
    Manages the text editor component with advanced features.
    
    This class encapsulates:
    - Syntax highlighting with multiple themes
    - Line numbering
    - File opening and saving
    - Editor state tracking
    - Undo/redo capability
    
    It provides a complete editing experience while isolating editor
    logic from the main application.
    """
    
    def __init__(self, parent, log_callback, status_update=None):
        """
        Initialize the editor manager.
        
        Args:
            parent: Parent widget to contain the editor
            log_callback: Function to use for logging operations
            status_update: Function to call to update status bar (optional)
        """
        self.parent = parent
        self.log = log_callback
        self.status_update = status_update
        self.current_file = None
        self.modified = False
        self.theme_name = "monokai"  # Default theme
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and configure the editor widgets."""
        # Create main editor frame
        self.frame = ttk.LabelFrame(self.parent, text="File Editor")
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Toolbar for editor actions with icons
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(toolbar, text="💾 Save", 
                 command=self.save_file, 
                 compound='left').pack(side="left", padx=2)
        
        ttk.Button(toolbar, text="📝 Save As", 
                 command=self.save_file_as, 
                 compound='left').pack(side="left", padx=2)
        
        ttk.Button(toolbar, text="↩️ Revert", 
                 command=self.revert_changes, 
                 compound='left').pack(side="left", padx=2)
        
        self.file_label = ttk.Label(toolbar, text="No file open")
        self.file_label.pack(side="right", padx=5)
        
        # Editor container with line numbers
        editor_container = ttk.Frame(self.frame)
        editor_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Line numbers widget
        self.line_numbers = tk.Text(editor_container, width=4, padx=3, takefocus=0,
                                  cursor="arrow", state="disabled",
                                  font=Font(family="Consolas", size=10))
        self.line_numbers.pack(side="left", fill="y")
        
        # Main editor widget
        self.editor = tk.Text(editor_container, wrap="none",
                            font=Font(family="Consolas", size=10),
                            undo=True, maxundo=-1)
        self.editor.pack(side="left", fill="both", expand=True)
        
        # Scrollbars
        x_scroll = ttk.Scrollbar(self.frame, orient="horizontal",
                               command=self.editor.xview)
        y_scroll = ttk.Scrollbar(editor_container, orient="vertical",
                               command=self._on_scroll)
        
        self.editor.config(xscrollcommand=x_scroll.set,
                          yscrollcommand=y_scroll.set)
        self.line_numbers.config(yscrollcommand=y_scroll.set)
        
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        
        # Bind editor events
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<Key>", self.update_line_numbers)
        self.editor.bind("<Button-1>", self.update_line_numbers)
        
        # Add key bindings for find/replace
        self.editor.bind("<Control-f>", self.show_find_dialog)
        self.editor.bind("<Control-h>", self.show_replace_dialog)
        
        # Theme selection
        self._create_theme_selector()

    def _create_theme_selector(self):
        """Create the theme selector widget with consistent styling."""
        style_frame = ttk.LabelFrame(self.parent, text="Editor Theme")
        style_frame.pack(fill='x', padx=5, pady=5)
        
        # Theme selector with preview
        select_frame = ttk.Frame(style_frame)
        select_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(select_frame, text="Theme:").pack(side='left')
        
        self.style_var = tk.StringVar(value=self.theme_name)
        styles = sorted(list(get_all_styles()))
        style_combo = ttk.Combobox(select_frame, textvariable=self.style_var,
                                 values=styles, state='readonly', width=20)
        style_combo.pack(side='left', padx=(5,0))
        style_combo.bind('<<ComboboxSelected>>', self._on_theme_change)
        
        # Quick theme buttons with consistent styling
        quick_themes = ttk.Frame(style_frame)
        quick_themes.pack(fill='x', padx=5, pady=2)
        
        for theme in ['monokai', 'vs', 'github-dark', 'solarized-dark', 'solarized-light']:
            if theme in styles:
                btn = ttk.Button(quick_themes, text=theme.title(),
                               command=lambda t=theme: self.set_theme(t))
                btn.pack(side='left', padx=2)

    def load_file(self, path):
        """
        Load a file into the editor.
        
        Args:
            path (str): Path to the file to load
            
        Returns:
            bool: True if file was loaded successfully
        """
        try:
            content = file_io_utils.load_file(path, self.log)
            if content is None:
                return False
            
            # Update editor
            self.editor.delete('1.0', tk.END)
            self.editor.insert('1.0', content)
            
            # Apply syntax highlighting
            self._apply_syntax_highlighting(path)
            
            # Update state
            self.current_file = path
            self.file_label.config(text=os.path.basename(path))
            self.modified = False
            self.update_line_numbers()
            
            return True
            
        except Exception as e:
            self.log(f"Error opening file: {e}")
            return False
    
    def save_file(self):
        """Save changes to the current file."""
        if not self.current_file or not self.modified:
            return False
            
        try:
            content = self.editor.get("1.0", "end-1c")
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.modified = False
            self.file_label.config(text=os.path.basename(self.current_file))
            self.log(f"Saved changes to {self.current_file}")
            
            # Update status if available
            if hasattr(self, 'status_update') and self.status_update:
                self.status_update(f"Saved: {os.path.basename(self.current_file)}")
                
            return True
            
        except Exception as e:
            self.log(f"Error saving file: {e}")
            
            # Update status if available
            if hasattr(self, 'status_update') and self.status_update:
                self.status_update(f"Error saving file: {e}")
                
            messagebox.showerror("Save Error", str(e))
            return False
    
    def save_file_as(self):
        """Save the current content to a new file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialdir=OUTPUT_DIR,
            initialfile=os.path.basename(self.current_file) if self.current_file else None,
            filetypes=[("All files", "*.*"), ("Text files", "*.txt")]
        )
        
        if filename:
            self.current_file = filename
            return self.save_file()
        return False
    
    def open_file_dialog(self):
        """Open a file dialog to select and open a file."""
        filename = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("All files", "*.*"),
                ("Python files", "*.py"),
                ("Text files", "*.txt")
            ]
        )
        if filename:
            return self.load_file(filename)
        return False
    
    def revert_changes(self):
        """Revert unsaved changes in the editor."""
        if self.modified and self.current_file:
            if messagebox.askyesno("Revert Changes?", 
                                 "Discard all unsaved changes?"):
                return self.load_file(self.current_file)
        return False
    
    def has_unsaved_changes(self):
        """Check if the editor has unsaved changes."""
        return self.modified
    
    def prompt_save_changes(self):
        """Prompt the user to save changes if needed.
        
        Returns:
            bool: True if the operation can proceed (changes saved or discarded),
                 False if the user canceled the operation
        """
        if not self.modified:
            return True
            
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"Save changes to {os.path.basename(self.current_file) if self.current_file else 'document'}?"
        )
        
        if response is None:  # Cancel
            return False
        if response is True:  # Yes, save
            return self.save_file()
        return True  # No, discard changes
    
    def set_theme(self, theme_name):
        """Set the syntax highlighting theme."""
        self.style_var.set(theme_name)
        self.theme_name = theme_name
        if self.current_file:
            self._apply_syntax_highlighting(self.current_file)
    
    def _on_theme_change(self, event=None):
        """Handle theme change events."""
        self.theme_name = self.style_var.get()
        if self.current_file:
            self._apply_syntax_highlighting(self.current_file)
    
    def _apply_syntax_highlighting(self, path):
        """Apply syntax highlighting based on file type."""
        try:
            # Get an appropriate lexer for the file type
            try:
                lexer = get_lexer_for_filename(path, stripnl=False)
                lexer.stripnl = False
            except:
                lexer = TextLexer()
            
            # Apply the selected style
            style = get_style_by_name(self.theme_name)
            
            content = self.editor.get("1.0", "end-1c")
            tokens = lexer.get_tokens(content)

            # Clear existing tags
            for tag in self.editor.tag_names():
                if tag != "sel":  # Preserve selection tag
                    self.editor.tag_delete(tag)
            
            # Function to ensure colors are in proper hex format
            def ensure_hex_color(color, default="#000000"):
                if not color:
                    return default
                if color.startswith('#'):
                    return color
                # Handle 6-char hex without #
                if len(color) == 6 and all(c in '0123456789abcdefABCDEF' for c in color):
                    return f"#{color}"
                # Handle 3-char hex without #
                if len(color) == 3 and all(c in '0123456789abcdefABCDEF' for c in color):
                    return f"#{color[0]*2}{color[1]*2}{color[2]*2}"
                return default
            
            # Configure editor colors
            bg_color = ensure_hex_color(style.background_color, "#ffffff")
            fg_color = ensure_hex_color(style.style_for_token(Token)['color'], "#000000")
            
            self.editor.configure(
                background=bg_color,
                foreground=fg_color,
                insertbackground=fg_color
            )
            
            # Apply highlighting
            self.editor.mark_set("range_start", "1.0")
            for token, value in tokens:
                token_style = style.style_for_token(token)
                tag_name = str(token).replace('.', '_')
                
                # Get and validate colors
                fg = ensure_hex_color(token_style['color'], fg_color)
                bg = ensure_hex_color(token_style.get('bgcolor'), None)
                
                # Configure tag
                tag_config = {'foreground': fg}
                if bg:
                    tag_config['background'] = bg
                
                # Add font styles
                if token_style['bold']:
                    tag_config['font'] = Font(family="Consolas", size=10, weight="bold")
                elif token_style['italic']:
                    tag_config['font'] = Font(family="Consolas", size=10, slant="italic")
                    
                self.editor.tag_configure(tag_name, **tag_config)
                
                # Calculate end position for tag
                if '\n' in value:
                    end_row = str(int(self.editor.index("range_start").split('.')[0]) + value.count('\n'))
                    end_col = len(value.split('\n')[-1])
                    end = f"{end_row}.{end_col}"
                else:
                    cur_pos = self.editor.index("range_start")
                    row, col = cur_pos.split('.')
                    end = f"{row}.{int(col) + len(value)}"
                
                # Apply tag
                self.editor.tag_add(tag_name, "range_start", end)
                self.editor.mark_set("range_start", end)

            # Update line numbers
            self.line_numbers.configure(
                background=bg_color,
                foreground=fg_color
            )
                
        except Exception as e:
            self.log(f"Error applying syntax highlighting: {e}")
    
    def update_line_numbers(self, event=None):
        """Update the line numbers display."""
        if not hasattr(self, 'line_numbers'):
            return
            
        lines = self.editor.get("1.0", "end-1c").split("\n")
        line_count = len(lines)
        
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        for i in range(1, line_count + 1):
            self.line_numbers.insert("end", f"{i}\n")
        self.line_numbers.config(state="disabled")
    
    def _on_scroll(self, *args):
        """Synchronize scrolling between editor and line numbers."""
        self.editor.yview(*args)
        self.line_numbers.yview(*args)
    
    def _on_modified(self, event=None):
        """Handle editor content modifications."""
        if self.editor.edit_modified():
            self.modified = True
            if self.current_file:
                self.file_label.config(text=f"*{os.path.basename(self.current_file)} (modified)")
        self.editor.edit_modified(False)
    
    def get_editor_widget(self):
        """Return the editor widget for binding external events."""
        return self.editor
    
    def get_frame(self):
        """Return the main frame containing all editor components."""
        return self.frame
        
    def show_find_dialog(self, event=None):
        """Show the find dialog."""
        SearchDialog(self.parent, self.editor, mode="find")
        return "break"  # Prevent default behavior
        
    def show_replace_dialog(self, event=None):
        """Show the find and replace dialog."""
        SearchDialog(self.parent, self.editor, mode="replace")
        return "break"  # Prevent default behavior
