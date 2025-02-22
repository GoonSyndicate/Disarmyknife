"""
FileConcatenatorApp: Main GUI application for the file concatenation utility.

This module provides a modern, responsive GUI for selecting, previewing, and concatenating files.
It uses ttk widgets styled with a custom theme for a consistent look and feel.

Key Features:
- File explorer with tree view and file type indicators
- File preview with syntax highlighting
- Selected files management
- Logging and status updates
- File concatenation with backup creation
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, END
from tkinter.font import Font
from datetime import datetime
import os
import threading
import file_io_utils
from theme_config import ThemeConfig
import pygments
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import get_formatter_by_name
from pygments.token import Token  # Add this import
import re
from tkinterdnd2 import DND_FILES, TkinterDnD  # Updated import
from pygments.styles import get_all_styles, get_style_by_name
from app_config import DEFAULT_OUTPUT_FILE, OUTPUT_DIR, BACKUP_DIR

class FileConcatenatorApp(TkinterDnD.Tk):  # Changed parent class to support drag-drop
    """
    Main application window for the File Concatenator utility.
    
    This class inherits from tk.Tk and provides a complete GUI interface for:
    - Browsing and selecting files via a tree view
    - Previewing file contents with syntax highlighting
    - Managing a list of selected files
    - Concatenating selected files into a master file
    
    The GUI is divided into two main panels:
    1. Left panel: File explorer with preview
    2. Right panel: Selected files list and operation log
    
    Attributes:
        master_filename (str): Name of the output concatenated file
        tree_item_to_path (dict): Maps tree items to file system paths
        tree_item_original_text (dict): Stores original display text for tree items
        
    The application maintains a single source of truth for selected files
    through the listbox widget, avoiding state duplication.
    """
    
    def __init__(self):
        """Initialize the application window and set up all GUI components."""
        super().__init__()
        self.title("File Concatenator Utility")
        self.geometry("1200x800")
        self.style, self.colors = ThemeConfig.setup_theme()

        # Remove duplicate state; listbox becomes the single source of truth.
        self.master_filename = DEFAULT_OUTPUT_FILE
        self.tree_item_to_path = {}
        self.tree_item_original_text = {}

        # Use a PanedWindow to separate explorer and file list
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left frame: File Explorer Panel
        self.frame_explorer = ttk.Frame(self.paned)
        self.paned.add(self.frame_explorer, weight=1)

        # Right frame: Selected Files and Log
        self.frame_main = ttk.Frame(self.paned)
        self.paned.add(self.frame_main, weight=2)

        self.create_explorer_widgets()
        self.create_main_widgets()
        self.log("Application started. Use 'Load Directory' to select a folder.")

        # Add status bar
        self.status_bar = ttk.Frame(self, style="StatusBar.TFrame")
        self.status_bar.pack(side="bottom", fill="x")
        
        self.status_label = ttk.Label(self.status_bar, style="StatusBar.TLabel", text="Ready")
        self.status_label.pack(side="left", padx=5)
        
        self.progress_bar = ttk.Progressbar(self.status_bar, mode='determinate', length=200)
        self.progress_bar.pack(side="right", padx=5, pady=2)

        # Add search frame above tree
        self.create_search_widgets()
        
        # Add style selector for preview
        self.create_style_selector()
        
        # Configure drag-drop with updated tkinterdnd2
        self.listbox_files.drop_target_register(DND_FILES)
        self.listbox_files.dnd_bind('<<Drop>>', self.handle_drop)

        # Add context management
        self.contexts = {}
        self.current_context = None
        
        # Add context selector above the file list
        self.create_context_widgets()
        
        # Add focus mode toggle
        self.create_focus_mode_widgets()
        
        # Add quick notes feature
        self.create_quick_notes()

        # Add editor state tracking
        self.current_file = None
        self.editor_modified = False
        self.editor_history = []  # For recently edited files

        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.quit)

        # Bind triple-click to add all files inside a folder
        self.tree_files.bind("<Triple-1>", self.on_tree_item_triple_click)

        # Bind treeview expand event to load child nodes
        self.tree_files.bind("<<TreeviewOpen>>", self.load_tree_node)

    def create_explorer_widgets(self):
        """
        Create and configure the file explorer panel widgets.
        
        Components:
        - Load Directory button
        - File type legend
        - Treeview for file system navigation
        - Preview panel with syntax highlighting support
        """
        # Button to load a directory
        btn_load_dir = ttk.Button(self.frame_explorer, text="Load Directory", command=self.load_directory)
        btn_load_dir.pack(padx=5, pady=5, anchor="n")

        # Legend frame: Shows filetype indicators
        frame_legend = ttk.Frame(self.frame_explorer)
        frame_legend.pack(padx=5, pady=5, fill="x")
        legend_text = (
            "Legend:  📁 Folder    🐍 Python    📜 JavaScript    ⚛️ TSX/JSX    🔷 TypeScript    "
            "🎨 CSS    🌐 HTML    📄 Other"
        )
        lbl_legend = ttk.Label(frame_legend, text=legend_text, wraplength=250, justify="center")
        lbl_legend.pack(padx=5, pady=5)

        # Frame to hold treeview and its scrollbar
        frame_explorer_inner = ttk.Frame(self.frame_explorer)
        frame_explorer_inner.pack(fill="both", expand=True)

        # Treeview for showing directories and files
        self.tree_files = ttk.Treeview(frame_explorer_inner)
        self.tree_files.pack(fill="both", expand=True, padx=5, pady=5)
        # Bind events
        self.tree_files.bind("<Double-1>", self.on_tree_item_double_click)
        self.tree_files.bind("<<TreeviewSelect>>", self.on_tree_selection)
        self.tree_files.bind("<Button-3>", self.show_context_menu)

        # Add vertical scrollbar for tree
        tree_scroll = ttk.Scrollbar(frame_explorer_inner, orient="vertical", command=self.tree_files.yview)
        self.tree_files.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")

        # Enhanced editor panel (replacing preview panel)
        editor_frame = ttk.LabelFrame(self.frame_explorer, text="File Editor")
        editor_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Toolbar for editor
        toolbar = ttk.Frame(editor_frame)
        toolbar.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(toolbar, text="Save", command=self.save_current_file).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Save As", command=self.save_file_as).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Revert", command=self.revert_changes).pack(side="left", padx=2)
        
        self.file_label = ttk.Label(toolbar, text="No file open")
        self.file_label.pack(side="right", padx=5)
        
        # Editor with line numbers
        editor_container = ttk.Frame(editor_frame)
        editor_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.line_numbers = tk.Text(editor_container, width=4, padx=3, takefocus=0,
                                  cursor="arrow", state="disabled",
                                  font=Font(family="Consolas", size=10))
        self.line_numbers.pack(side="left", fill="y")
        
        self.editor = tk.Text(editor_container, wrap="none",
                            font=Font(family="Consolas", size=10),
                            undo=True, maxundo=-1)
        self.editor.pack(side="left", fill="both", expand=True)
        
        # Scrollbars
        editor_xscroll = ttk.Scrollbar(editor_frame, orient="horizontal",
                                     command=self.editor.xview)
        editor_yscroll = ttk.Scrollbar(editor_container, orient="vertical",
                                     command=self.on_editor_scroll)
        
        self.editor.config(xscrollcommand=editor_xscroll.set,
                          yscrollcommand=editor_yscroll.set)
        self.line_numbers.config(yscrollcommand=editor_yscroll.set)
        
        editor_yscroll.pack(side="right", fill="y")
        editor_xscroll.pack(side="bottom", fill="x")
        
        # Bind editor events
        self.editor.bind("<<Modified>>", self.on_editor_modified)
        self.editor.bind("<Key>", self.update_line_numbers)
        self.editor.bind("<Button-1>", self.update_line_numbers)
        
        # Add editor keyboard shortcuts
        self.bind("<Control-s>", lambda e: self.save_current_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-z>", lambda e: self.editor.edit_undo())
        self.bind("<Control-y>", lambda e: self.editor.edit_redo())

    def create_main_widgets(self):
        """
        Create and configure the main panel widgets.
        
        Components:
        - Selected files listbox
        - Operation buttons (Add, Remove, Clear, Exit, Concatenate)
        - Log panel for operation feedback
        """
        # --- Frame for Selected Files List ---
        self.frame_files = ttk.LabelFrame(self.frame_main, text="Selected Files")  # Store frame reference
        self.frame_files.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        self.listbox_files = tk.Listbox(self.frame_files, selectmode="extended")
        self.listbox_files.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar = ttk.Scrollbar(self.frame_files, orient="vertical", command=self.listbox_files.yview)
        scrollbar.pack(side="left", fill="y", padx=(0, 10), pady=10)
        self.listbox_files.config(yscrollcommand=scrollbar.set)

        # --- Frame for Buttons ---
        frame_buttons = ttk.Frame(self.frame_main)
        frame_buttons.pack(fill="x", padx=10, pady=5)

        btn_add = ttk.Button(frame_buttons, text="Add Files", command=self.add_files)
        btn_add.pack(side="left", padx=5)

        btn_remove = ttk.Button(frame_buttons, text="Remove Selected", command=self.remove_selected)
        btn_remove.pack(side="left", padx=5)

        btn_clear = ttk.Button(frame_buttons, text="Clear List", command=self.clear_list)
        btn_clear.pack(side="left", padx=5)

        btn_exit = ttk.Button(frame_buttons, text="Exit", command=self.quit)
        btn_exit.pack(side="right", padx=5)

        btn_concat = ttk.Button(frame_buttons, text="Concatenate Files", command=self.concatenate_files)
        btn_concat.pack(side="right", padx=5)

        # --- Log Panel ---
        frame_log = ttk.LabelFrame(self.frame_main, text="Log")
        frame_log.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text = scrolledtext.ScrolledText(frame_log, wrap="word", height=10)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, message):
        """
        Add a timestamped message to the log panel.
        
        Args:
            message (str): The message to log
        """
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        self.log_text.insert("end", timestamp + message + "\n")
        self.log_text.see("end")

    def add_files(self):
        """Open a file dialog to add one or more files to the list."""
        files = filedialog.askopenfilenames(title="Select Files to Concatenate")
        if files:
            count = 0
            current_files = self.listbox_files.get(0, END)
            for file in files:
                if file not in current_files:
                    self.listbox_files.insert(END, file)
                    count += 1
            self.log(f"Added {count} file(s).")

    def remove_selected(self):
        """Remove the selected file(s) from the list."""
        selected_indices = list(self.listbox_files.curselection())
        selected_indices.sort(reverse=True)
        for index in selected_indices:
            self.listbox_files.delete(index)
        self.log("Removed selected file(s).")

    def clear_list(self):
        """Clear all files from the selection list."""
        self.listbox_files.delete(0, END)
        self.log("Cleared file list.")

    def create_backup(self):
        """Create a backup of the master file (if it exists) with a timestamp."""
        if os.path.exists(self.master_filename):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_filename = f"{self.master_filename}.{timestamp}.bak"
            try:
                shutil.copy2(self.master_filename, backup_filename)
                self.log(f"Backup created: {backup_filename}")
            except Exception as e:
                self.log(f"Error creating backup: {str(e)}")
        else:
            self.log("No existing master file found; skipping backup.")

    def load_file(self, filename):
        """Load and return the content of a file."""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    return file.read()
            except Exception as e:
                self.log(f"Error reading {filename}: {str(e)}")
                return None
        else:
            self.log(f"File not found: {filename}")
            return None

    def append_to_master_file(self, filename, content):
        """Append the given content to the master file, including a header."""
        try:
            with open(self.master_filename, 'a', encoding='utf-8') as master_file:
                master_file.write(f"\n\n# Content from {filename}\n\n")
                master_file.write(content)
            self.log(f"Appended content from {filename}")
        except Exception as e:
            self.log(f"Error appending {filename}: {str(e)}")

    def write_directory_structure(self):
        """Write the list of selected files (i.e. the directory structure) into the master file."""
        try:
            with open(self.master_filename, 'a', encoding='utf-8') as master_file:
                master_file.write("# Directory Structure\n\n")
                for file in self.selected_files:
                    master_file.write(f"{file}\n")
                master_file.write("\n\n")
            self.log("Directory structure written to master file.")
        except Exception as e:
            self.log(f"Error writing directory structure: {str(e)}")

    def concatenate_files(self):
        """
        Initiate the file concatenation process in a separate thread.
        
        The process:
        1. Validates file selection
        2. Confirms user intention
        3. Creates backup of existing master file
        4. Concatenates selected files
        5. Updates status and log
        """
        files = self.listbox_files.get(0, END)
        if not files:
            messagebox.showwarning("No Files Selected", "Please add files to concatenate.")
            return
        if not messagebox.askyesno("Confirm Concatenation",
                                   "This will create a backup of the existing master file (if any) and overwrite it. Continue?"):
            return

        self.log("Starting concatenation process...")
        t = threading.Thread(target=self.run_concatenation, args=(files,))
        t.start()

    def run_concatenation(self, files):
        file_io_utils.create_backup(self.master_filename, self.log)
        try:
            open(self.master_filename, 'w').close()
            self.log("Cleared existing master file.")
        except Exception as e:
            self.log(f"Error clearing master file: {e}")
            return
        file_io_utils.write_directory_structure(self.master_filename, files, self.log)
        for file in files:
            content = file_io_utils.load_file(file, self.log)
            if content is not None:
                file_io_utils.append_to_master(self.master_filename, file, content, self.log)
        self.log("Concatenation process completed.")
        messagebox.showinfo("Completed", f"Files have been concatenated into {self.master_filename}.")

    def load_directory(self):
        """Load the directory in a separate thread."""
        dir_selected = filedialog.askdirectory(title="Select Directory")
        if not dir_selected:
            return

        # Clear existing data
        self.tree_files.delete(*self.tree_files.get_children())
        self.tree_item_to_path.clear()
        self.tree_item_original_text.clear()

        # Start loading in a separate thread
        threading.Thread(target=self.populate_tree, args=("", dir_selected), daemon=True).start()
        self.log(f"Loading directory: {dir_selected}")

    def get_indicator(self, path):
        """Return an icon based on file type or folder."""
        if os.path.isdir(path):
            return "📁"
        ext = os.path.splitext(path)[1].lower()
        mapping = {
            '.py': '🐍',
            '.js': '📜',
            '.tsx': '⚛️',
            '.jsx': '⚛️',
            '.ts': '🔷',
            '.css': '🎨',
            '.html': '🌐',
            '.txt': '📄',
            '.json': '🔧'
        }
        return mapping.get(ext, "📄")

    def populate_tree(self, parent, path):
        """Populate the tree using scandir for improved performance."""
        try:
            entries = list(os.scandir(path))
            entries.sort(key=lambda e: e.name.lower())  # Sort entries

            for entry in entries:
                full_entry = os.path.join(path, entry.name)
                icon = self.get_indicator(full_entry)
                display_text = f"{icon} {entry.name}"
                node = self.tree_files.insert(parent, 'end', text=display_text, open=False)
                self.tree_item_to_path[node] = full_entry
                self.tree_item_original_text[node] = display_text
                
                if entry.is_dir():
                    # Insert a dummy child to show the expand arrow
                    self.tree_files.insert(node, 'end', text='Loading...')
        except PermissionError:
            pass  # Skip directories that cannot be accessed

    def load_tree_node(self, event):
        """Load the child nodes when a tree node is expanded."""
        item = self.tree_files.selection()[0]
        path = self.tree_item_to_path[item]

        # Remove dummy child
        if self.tree_files.get_children(item):
            first_child = self.tree_files.get_children(item)[0]
            if self.tree_files.item(first_child, 'text') == 'Loading...':
                self.tree_files.delete(first_child)

        try:
            entries = list(os.scandir(path))
            entries.sort(key=lambda e: e.name.lower())

            for entry in entries:
                full_entry = os.path.join(path, entry.name)
                icon = self.get_indicator(full_entry)
                display_text = f"{icon} {entry.name}"
                node = self.tree_files.insert(item, 'end', text=display_text, open=False)
                self.tree_item_to_path[node] = full_entry
                self.tree_item_original_text[node] = display_text
                
                if entry.is_dir():
                    self.tree_files.insert(node, 'end', text='Loading...')
        except PermissionError:
            pass

    def on_tree_item_double_click(self, event):
        """Toggle file inclusion when a user double-clicks a file node."""
        selected_items = self.tree_files.selection()
        if not selected_items:
            return
        item = selected_items[0]
        path = self.tree_item_to_path.get(item)
        if not path or os.path.isdir(path):
            return  # Only handle files

        # Toggle inclusion using the listbox as a single source.
        current_files = self.listbox_files.get(0, END)
        if path in current_files:
            # Remove from listbox.
            try:
                idx = current_files.index(path)
                self.listbox_files.delete(idx)
            except ValueError:
                pass
            self.log(f"Removed: {path}")
            original = self.tree_item_original_text.get(item, "")
            self.tree_files.item(item, text=original, tags=())
        else:
            self.listbox_files.insert(END, path)
            self.log(f"Added: {path}")
            original = self.tree_item_original_text.get(item, "")
            self.tree_files.item(item, text=f"{original} ✓", tags=("selected",))
            self.tree_files.tag_configure("selected", background="lightblue")

    def on_tree_selection(self, event):
        """Update editor panel with selected file content."""
        selected = self.tree_files.selection()
        if not selected:
            return
            
        item = selected[0]
        path = self.tree_item_to_path.get(item)
        if path and os.path.isfile(path):
            self.preview_file(path)  # Use existing preview_file method which now uses the editor
        else:
            # Clear editor if no file is selected
            self.editor.delete("1.0", END)
            self.current_file = None
            self.file_label.config(text="No file open")
            self.editor_modified = False

    def open_file(self, event=None):
        """Open a file in the editor."""
        filename = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("All files", "*.*"),
                ("Python files", "*.py"),
                ("Text files", "*.txt")
            ]
        )
        if filename:
            self.preview_file(filename)

    def show_context_menu(self, event):
        """Show a context menu to toggle file inclusion on right-click."""
        item = self.tree_files.identify_row(event.y)
        if not item:
            return
        
        path = self.tree_item_to_path.get(item)
        if not path:
            return

        self.tree_files.selection_set(item)
        menu = tk.Menu(self, tearoff=0)
        
        if os.path.isfile(path):
            menu.add_command(label="Toggle Include", 
                           command=lambda: self.on_tree_item_double_click(event))
            menu.add_command(label="Preview",
                           command=lambda: self.preview_file(path))
            menu.add_command(label="Open in Default Editor",
                           command=lambda: os.startfile(path))
            menu.add_separator()
            menu.add_command(label="Show File Properties",
                           command=lambda: self.show_file_properties(path))
        
        menu.tk_popup(event.x_root, event.y_root)

    def preview_file(self, path):
        """Display file contents in the editor with syntax highlighting."""
        try:
            # Open and read the new file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update editor
            self.editor.delete('1.0', tk.END)
            self.editor.insert('1.0', content)
            
            # Enhanced syntax highlighting
            try:
                lexer = get_lexer_for_filename(path, stripnl=False)
                lexer.stripnl = False
            except:
                lexer = TextLexer()
            
            style = get_style_by_name(self.style_var.get())
            self.apply_syntax_highlighting(lexer, style)
            
            # Update state and appearance
            self.current_file = path
            self.file_label.config(text=os.path.basename(path))
            self.editor_modified = False
            self.update_line_numbers()
            
            # Configure line numbers appearance
            self.line_numbers.configure(
                background=style.background_color,
                foreground=style.style_for_token(Token.Text)['color']
            )
            
        except Exception as e:
            self.log(f"Error opening file: {e}")

    def apply_syntax_highlighting(self, lexer, style):
        """Apply syntax highlighting to the editor content."""
        content = self.editor.get("1.0", "end-1c")
        tokens = lexer.get_tokens(content)

        # Clear existing tags
        for tag in self.editor.tag_names():
            if tag != "sel":  # Preserve selection tag
                self.editor.tag_delete(tag)
        
        def ensure_hex_color(color):
            """Convert color names/values to proper hex format."""
            if not color:
                return self.colors['fg']
            if color.startswith('#'):
                return color
            # Handle 6-char hex without #
            if len(color) == 6 and all(c in '0123456789abcdefABCDEF' for c in color):
                return f"#{color}"
            # Handle 3-char hex without #
            if len(color) == 3 and all(c in '0123456789abcdefABCDEF' for c in color):
                return f"#{color[0]*2}{color[1]*2}{color[2]*2}"
            return self.colors['fg']
        
        # Configure editor colors
        bg_color = ensure_hex_color(style.background_color) or self.colors['bg']
        fg_color = ensure_hex_color(style.style_for_token(Token)['color']) or self.colors['fg']
        
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
            fg = ensure_hex_color(token_style['color'])
            bg = ensure_hex_color(token_style.get('bgcolor'))
            
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

    def save_current_file(self):
        """Save changes to the current file."""
        if not self.current_file or not self.editor_modified:
            return
            
        try:
            content = self.editor.get("1.0", "end-1c")
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.editor_modified = False
            self.file_label.config(text=self.current_file)
            self.log(f"Saved changes to {self.current_file}")
        except Exception as e:
            self.log(f"Error saving file: {e}")
            messagebox.showerror("Save Error", str(e))

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
            self.save_current_file()

    def revert_changes(self):
        """Revert unsaved changes in the editor."""
        if self.editor_modified and self.current_file:
            if messagebox.askyesno("Revert Changes?", 
                                 "Discard all unsaved changes?"):
                self.preview_file(self.current_file)

    def update_status(self, message):
        self.status_label.config(text=message)
        self.update_idletasks()

    def create_search_widgets(self):
        """Create search bar and options for file explorer."""
        search_frame = ttk.Frame(self.frame_explorer)
        search_frame.pack(fill='x', padx=5, pady=5, before=self.tree_files)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_tree)
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True)
        
        self.search_type = tk.StringVar(value="name")
        type_menu = ttk.OptionMenu(search_frame, self.search_type, 
                                 "name", "name", "content", "extension",
                                 command=self.filter_tree)
        type_menu.pack(side='right', padx=(5,0))

    def filter_tree(self, *args):
        """Filter treeview items based on search criteria."""
        search_text = self.search_var.get().lower()
        search_type = self.search_type.get()
        
        # Clear all tags first
        for item in self.tree_files.get_children():
            self.clear_tree_tags(item)
        
        if not search_text:
            return
        
        # Search and highlight matching items
        for item in self.tree_files.get_children():
            self.search_tree_item(item, search_text, search_type, depth=3) # Limit depth

    def search_tree_item(self, item, search_text, search_type, depth):
        """Recursively search through tree items."""
        if depth <= 0:
            return  # Stop recursion if depth is reached
        
        path = self.tree_item_to_path.get(item)
        match = False
        
        if search_type == "name":
            match = search_text in os.path.basename(path).lower()
        elif search_type == "extension":
            match = search_text in os.path.splitext(path)[1].lower()
        elif search_type == "content" and os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(1024)  # Read first 1KB only
                    match = search_text in content.lower()
            except:
                pass
        
        if match:
            self.tree_files.item(item, tags=('match',))
            self.tree_files.see(item)
        
        for child in self.tree_files.get_children(item):
            self.search_tree_item(child, search_text, search_type, depth - 1)

    def clear_tree_tags(self, item):
        """Recursively clear tags from tree items."""
        self.tree_files.item(item, tags=())
        for child in self.tree_files.get_children(item):
            self.clear_tree_tags(child)

    def create_style_selector(self):
        """Create syntax highlighting style selector with preview."""
        style_frame = ttk.LabelFrame(self.frame_explorer, text="Editor Theme")
        style_frame.pack(fill='x', padx=5, pady=5)
        
        # Theme selector with preview
        select_frame = ttk.Frame(style_frame)
        select_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(select_frame, text="Theme:").pack(side='left')
        
        self.style_var = tk.StringVar(value="monokai")  # Default to monokai
        styles = sorted(list(get_all_styles()))
        style_combo = ttk.Combobox(select_frame, textvariable=self.style_var,
                                 values=styles, state='readonly', width=20)
        style_combo.pack(side='left', padx=(5,0))
        style_combo.bind('<<ComboboxSelected>>', self.update_preview_style)
        
        # Quick theme buttons
        quick_themes = ttk.Frame(style_frame)
        quick_themes.pack(fill='x', padx=5, pady=2)
        
        for theme in ['monokai', 'vs', 'github-dark', 'solarized-dark', 'solarized-light']:
            if theme in styles:
                btn = ttk.Button(quick_themes, text=theme.title(),
                               command=lambda t=theme: self.quick_change_theme(t))
                btn.pack(side='left', padx=2)

    def quick_change_theme(self, theme_name):
        """Quickly switch to a preset theme."""
        self.style_var.set(theme_name)
        self.update_preview_style()

    def update_preview_style(self, event=None):
        """Update the preview panel with selected style."""
        try:
            selected = self.tree_files.selection()[0]
            path = self.tree_item_to_path.get(selected)
            if path and os.path.isfile(path):
                self.preview_file(path)
        except IndexError:
            pass

    def handle_drop(self, event):
        """Handle drag and drop of files."""
        # Updated to handle tkinterdnd2 data format
        if event.data:
            # Process each file
            count = 0
            current_files = self.listbox_files.get(0, tk.END)
            
            # Split data into individual files (handles multiple files)
            files = event.data.split()
            
            for file in files:
                # Clean up file path based on system
                file = file.strip('{}').replace('\\', '/')
                if file not in current_files:
                    self.listbox_files.insert(tk.END, file)
                    count += 1
            
            self.log(f"Added {count} dropped file(s).")

    def create_context_widgets(self):
        """Create widgets for managing different file contexts."""
        # Create a more prominent context management section
        self.context_frame = ttk.LabelFrame(self.frame_main, text="💼 Working Context")
        self.context_frame.pack(fill="x", padx=10, pady=5, before=self.frame_files)
        
        # Add help/info button
        ttk.Button(self.context_frame, text="ℹ️", width=3,
                  command=self.show_context_help).pack(side="right", padx=5)
        
        # Context naming and saving
        name_frame = ttk.Frame(self.context_frame)
        name_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(name_frame, text="Context Name:").pack(side="left")
        self.context_name = ttk.Entry(name_frame)
        self.context_name.pack(side="left", fill="x", expand=True, padx=5)
        
        # Context actions
        btn_frame = ttk.Frame(self.context_frame)
        btn_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(btn_frame, text="💾 Save Context",
                  command=self.save_current_context).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📤 Export",
                  command=self.export_context).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📥 Import",
                  command=self.import_context).pack(side="left", padx=2)
        
        # Context selector
        select_frame = ttk.Frame(self.context_frame)
        select_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(select_frame, text="Load Context:").pack(side="left")
        self.context_combo = ttk.Combobox(select_frame, state="readonly")
        self.context_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.context_combo.bind("<<ComboboxSelected>>", self.load_context)

    def show_context_help(self):
        """Show help dialog explaining contexts."""
        help_text = """
        💼 Working Contexts

        A context lets you save and restore your work setup:
        • Selected files
        • Notes and comments
        • Export to share with others

        Example Uses:
        1. Save different groups of related files
        2. Keep notes about what you're working on
        3. Switch between different tasks easily
        4. Share file groupings with ChatGPT

        How to Use:
        1. Select files you want to group together
        2. Add any notes about the files/task
        3. Give your context a name
        4. Click 'Save Context'
        5. Later, select it from the dropdown to restore
        """
        messagebox.showinfo("About Working Contexts", help_text.strip())

    def export_context(self):
        """Export the current context to a markdown file."""
        if not self.current_context:
            messagebox.showwarning("Export Context", "No context selected")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            initialdir=OUTPUT_DIR,
            initialfile=f"{self.current_context}.md",
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                context = self.contexts[self.current_context]
                
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
                            try:
                                with open(file, 'r', encoding='utf-8') as src:
                                    # First 10 lines of each file
                                    preview = ''.join(src.readlines()[:10])
                                    f.write(preview)
                            except Exception as e:
                                f.write(f"Error reading file: {e}")
                            f.write("\n```\n\n")
                
                self.log(f"Exported context to {filename}")
            except Exception as e:
                self.log(f"Error exporting context: {e}")
                messagebox.showerror("Export Error", str(e))

    def import_context(self):
        """Import a context from a JSON file."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import json
                with open(filename) as f:
                    context = json.load(f)
                
                name = os.path.splitext(os.path.basename(filename))[0]
                self.contexts[name] = context
                self.update_context_combo()
                self.log(f"Imported context from {filename}")
            except Exception as e:
                self.log(f"Error importing context: {e}")
                messagebox.showerror("Import Error", str(e))

    def toggle_focus_mode(self):
        """Toggle focus mode to reduce visual distractions."""
        if self.focus_var.get():
            # Simplify UI
            self.frame_explorer.pack_forget()
            self.paned.remove(self.frame_explorer)
            self.geometry("800x600")
        else:
            # Restore full UI
            self.paned.add(self.frame_explorer, weight=1)
            self.paned.add(self.frame_main, weight=2)
            self.geometry("1200x800")
    
    def save_note(self):
        """Save current note to the context."""
        if self.current_context:
            self.contexts[self.current_context]['notes'] = \
                self.notes_text.get("1.0", END).strip()
            self.log("Note saved to current context")

    def update_context_combo(self):
        """Update the context combo box with saved contexts."""
        contexts = sorted(self.contexts.keys())
        self.context_combo['values'] = contexts
        if contexts:
            self.context_combo.set(contexts[0])

    def handle_drag_start(self, event):
        """Handle the start of drag operations."""
        # Get selected items
        selections = self.tree_files.selection()
        if selections:
            # Store the paths for dragging
            paths = [self.tree_item_to_path[item] for item in selections]
            event.data = ' '.join(paths)
            return True
        return False

    def handle_drag_motion(self, event):
        """Handle drag motion over drop targets."""
        return event.action

    def clear_search(self):
        """Clear the search box and reset tree view."""
        self.search_var.set('')
        self.filter_tree()

    def get_context_summary(self):
        """Get a summary of the current context."""
        if not self.current_context:
            return "No context loaded"
            
        context = self.contexts[self.current_context]
        files_count = len(context['files'])
        notes_preview = context['notes'][:50] + '...' if len(context['notes']) > 50 else context['notes']
        
        return f"Context: {self.current_context}\nFiles: {files_count}\nNotes: {notes_preview}"

    def on_editor_scroll(self, *args):
        """Sync line numbers with editor scrolling."""
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

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

    def on_editor_modified(self, event=None):
        """Handle editor content modifications."""
        if self.editor.edit_modified():
            self.editor_modified = True
            if self.current_file:
                self.file_label.config(text=f"*{self.current_file} (modified)")
        self.editor.edit_modified(False)

    def create_quick_notes(self):
        """Create a quick notes panel for temporary thoughts."""
        notes_frame = ttk.LabelFrame(self.frame_main, text="✏️ Quick Notes")
        notes_frame.pack(fill="x", padx=10, pady=5, after=self.context_frame)
        
        self.notes_text = scrolledtext.ScrolledText(notes_frame, height=3,
                                                  font=Font(family="Segoe UI", size=10))
        self.notes_text.pack(fill="x", padx=5, pady=5)

    def save_current_context(self):
        """Save the current workspace as a named context."""
        name = self.context_name.get().strip()
        if not name:
            messagebox.showwarning("Context Name Required", 
                                 "Please enter a name for your working context.")
            return
        
        # Get current workspace state
        self.contexts[name] = {
            'files': list(self.listbox_files.get(0, END)),
            'notes': self.notes_text.get("1.0", END).strip(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.current_context = name
        self.update_context_combo()
        self.log(f"Saved context: {name}")
        
    def load_context(self, event=None):
        """Load a previously saved context."""
        name = self.context_combo.get()
        if not name or name not in self.contexts:
            return
        
        # Check for unsaved changes
        if self.editor_modified:
            if not messagebox.askyesno("Unsaved Changes",
                                     "Loading a new context will discard unsaved changes. Continue?"):
                return
        
        context = self.contexts[name]
        
        # Clear current state
        self.listbox_files.delete(0, END)
        self.notes_text.delete("1.0", END)
        
        # Load context state
        for file in context['files']:
            self.listbox_files.insert(END, file)
        
        self.notes_text.insert("1.0", context.get('notes', ''))
        self.current_context = name
        
        # Update UI
        self.context_name.delete(0, END)
        self.context_name.insert(0, name)
        self.log(f"Loaded context: {name}")

    def create_focus_mode_widgets(self):
        """Create focus mode toggle in status bar."""
        focus_frame = ttk.Frame(self.status_bar)
        focus_frame.pack(side="right", padx=10)
        
        self.focus_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(focus_frame, text="Focus Mode", 
                       variable=self.focus_var,
                       command=self.toggle_focus_mode).pack()

    def quit(self):
        """Override quit to check for unsaved changes."""
        if self.editor_modified:
            if messagebox.askyesno("Unsaved Changes", 
                                 f"Save changes to {self.current_file}?"):
                self.save_current_file()
        super().quit()

    def on_tree_item_triple_click(self, event):
        """Handle triple-click on a folder to add all its files to the list."""
        item = self.tree_files.identify_row(event.y)
        if not item:
            return
        path = self.tree_item_to_path.get(item)
        if path and os.path.isdir(path):
            # Recursively add all files in the folder
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    current_files = self.listbox_files.get(0, 'end')
                    if full_path not in current_files:
                        self.listbox_files.insert('end', full_path)
            self.log(f"Added all files from folder: {path}")
            original = self.tree_item_original_text.get(item, "")
            self.tree_files.item(item, text=f"{original} ✓", tags=("selected",))
            self.tree_files.tag_configure("selected", background="lightblue")
