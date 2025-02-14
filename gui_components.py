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
import re
from tkinterdnd2 import DND_FILES, TkinterDnD  # Updated import
from pygments.styles import get_all_styles, get_style_by_name

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
        self.master_filename = 'master.txt'
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

        # Enhanced preview panel
        preview_frame = ttk.LabelFrame(self.frame_explorer, text="File Preview")
        preview_frame.pack(fill="x", padx=5, pady=5)
        
        self.preview_text = tk.Text(preview_frame, height=10, wrap="none",
                                  font=Font(family="Consolas", size=10))
        preview_xscroll = ttk.Scrollbar(preview_frame, orient="horizontal",
                                      command=self.preview_text.xview)
        preview_yscroll = ttk.Scrollbar(preview_frame, orient="vertical",
                                      command=self.preview_text.yview)
        
        self.preview_text.config(xscrollcommand=preview_xscroll.set,
                               yscrollcommand=preview_yscroll.set)
        
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        preview_yscroll.grid(row=0, column=1, sticky="ns")
        preview_xscroll.grid(row=1, column=0, sticky="ew")
        
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)

    def create_main_widgets(self):
        """
        Create and configure the main panel widgets.
        
        Components:
        - Selected files listbox
        - Operation buttons (Add, Remove, Clear, Exit, Concatenate)
        - Log panel for operation feedback
        """
        # --- Frame for Selected Files List ---
        frame_files = ttk.LabelFrame(self.frame_main, text="Selected Files")
        frame_files.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        self.listbox_files = tk.Listbox(frame_files, selectmode="extended")
        self.listbox_files.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar = ttk.Scrollbar(frame_files, orient="vertical", command=self.listbox_files.yview)
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
        """Let the user choose a directory to display in the file explorer."""
        dir_selected = filedialog.askdirectory(title="Select Directory")
        if not dir_selected:
            return
        self.tree_files.delete(*self.tree_files.get_children())
        self.tree_item_to_path.clear()
        self.tree_item_original_text.clear()
        self.populate_tree("", dir_selected)
        self.log(f"Loaded directory: {dir_selected}")

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
        """Recursively populate the tree with directories and files from the given path."""
        basename = os.path.basename(path)
        if not basename:
            basename = path  # For root directories
        icon = self.get_indicator(path)
        display_text = f"{icon} {basename}"
        node = self.tree_files.insert(parent, 'end', text=display_text, open=False)
        self.tree_item_to_path[node] = path
        self.tree_item_original_text[node] = display_text
        try:
            for entry in os.listdir(path):
                full_entry = os.path.join(path, entry)
                if os.path.isdir(full_entry):
                    self.populate_tree(node, full_entry)
                else:
                    file_icon = self.get_indicator(full_entry)
                    file_display = f"{file_icon} {entry}"
                    file_node = self.tree_files.insert(node, 'end', text=file_display)
                    self.tree_item_to_path[file_node] = full_entry
                    self.tree_item_original_text[file_node] = file_display
        except PermissionError:
            pass  # Skip directories that cannot be accessed

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
        """Update preview panel with first few lines of the selected file."""
        selected = self.tree_files.selection()
        if not selected:
            self.preview_text.delete("1.0", END)
            return
        item = selected[0]
        path = self.tree_item_to_path.get(item)
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[:10]
                preview = "".join(lines)
            except Exception as e:
                preview = f"Error previewing file: {e}"
        else:
            preview = ""
        self.preview_text.delete("1.0", END)
        self.preview_text.insert("1.0", preview)

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
        """
        Display file contents in the preview panel with syntax highlighting.
        
        Args:
            path (str): Path to the file to preview
            
        Uses Pygments for syntax highlighting based on file extension.
        Falls back to plain text if syntax highlighting fails.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Syntax highlighting
            try:
                lexer = get_lexer_for_filename(path)
            except:
                lexer = TextLexer()
            
            style = get_style_by_name(self.style_var.get())
            formatter = get_formatter_by_name('html',
                                           style=style,
                                           full=True)
            
            highlighted = pygments.highlight(content, lexer, formatter)
            
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', content)
            
            # Apply style colors
            self.preview_text.configure(bg=style.background_color,
                                     fg=style.styles['Text'].color or 'black')
            
        except Exception as e:
            self.log(f"Error previewing file: {e}")

    def show_file_properties(self, path):
        stats = os.stat(path)
        size = f"{stats.st_size / 1024:.1f} KB"
        modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        props = f"""
        Path: {path}
        Size: {size}
        Modified: {modified}
        """
        
        messagebox.showinfo("File Properties", props.strip())

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
            self.search_tree_item(item, search_text, search_type)

    def search_tree_item(self, item, search_text, search_type):
        """Recursively search through tree items."""
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
            self.search_tree_item(child, search_text, search_type)

    def clear_tree_tags(self, item):
        """Recursively clear tags from tree items."""
        self.tree_files.item(item, tags=())
        for child in self.tree_files.get_children(item):
            self.clear_tree_tags(child)

    def create_style_selector(self):
        """Create syntax highlighting style selector."""
        style_frame = ttk.Frame(self.frame_explorer)
        style_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(style_frame, text="Preview Theme:").pack(side='left')
        
        self.style_var = tk.StringVar(value="default")
        styles = sorted(list(get_all_styles()))
        style_combo = ttk.Combobox(style_frame, textvariable=self.style_var,
                                 values=styles, state='readonly')
        style_combo.pack(side='left', padx=(5,0))
        style_combo.bind('<<ComboboxSelected>>', self.update_preview_style)

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
