"""
File Tree Manager for the File Concatenator application.

This module provides a tree-based file explorer with:
- Directory navigation
- File type icons
- File selection
- Context menu support
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog
import threading

class FileTreeManager:
    """
    Manages the file explorer tree view component.
    
    This class encapsulates:
    - Directory browsing and navigation
    - File type visualization with icons
    - File selection functionality
    - Context menu handling
    
    It provides a complete file navigation experience while isolating
    tree logic from the main application.
    """
    
    def __init__(self, parent, log_callback, on_select_callback=None, 
                 on_double_click=None, on_context_menu=None, status_update=None):
        """
        Initialize the file tree manager.
        
        Args:
            parent: Parent widget to contain the tree view
            log_callback: Function to use for logging operations
            on_select_callback: Function to call when file is selected
            on_double_click: Function to call when item is double-clicked
            on_context_menu: Function to call to handle context menu
            status_update: Function to call to update status bar (optional)
        """
        self.parent = parent
        self.log = log_callback
        self.on_select = on_select_callback
        self.on_double_click = on_double_click
        self.on_context_menu = on_context_menu
        self.status_update = status_update
        
        self.tree_item_to_path = {}
        self.tree_item_original_text = {}
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and configure the tree view widgets."""
        # Button to load a directory with icon
        self.btn_load_dir = ttk.Button(self.parent, text="📂 Load Directory", 
                                      command=self.load_directory, compound='left')
        self.btn_load_dir.pack(padx=5, pady=5, anchor="n")

        # Legend frame: Shows filetype indicators - with consistent styling
        frame_legend = ttk.LabelFrame(self.parent, text="File Types")
        frame_legend.pack(padx=5, pady=5, fill="x")
        legend_text = (
            "Legend:  📁 Folder    🐍 Python    📜 JavaScript    ⚛️ TSX/JSX    🔷 TypeScript    "
            "🎨 CSS    🌐 HTML    📄 Other"
        )
        lbl_legend = ttk.Label(frame_legend, text=legend_text, wraplength=250, justify="center")
        lbl_legend.pack(padx=5, pady=5)

        # Frame to hold treeview and its scrollbar
        frame_tree = ttk.Frame(self.parent)
        frame_tree.pack(fill="both", expand=True)

        # Treeview for showing directories and files
        self.tree = ttk.Treeview(frame_tree)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bind events
        if self.on_select:
            self.tree.bind("<<TreeviewSelect>>", self.on_tree_selection)
        if self.on_double_click:
            self.tree.bind("<Double-1>", self.on_tree_item_double_click)
        if self.on_context_menu:
            self.tree.bind("<Button-3>", self.on_tree_context_menu)
            
        # Add support for triple-click
        self.tree.bind("<Triple-1>", self.on_tree_item_triple_click)
        
        # Bind treeview expand event to load child nodes
        self.tree.bind("<<TreeviewOpen>>", self.load_tree_node)

        # Add vertical scrollbar for tree
        tree_scroll = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        
    def load_directory(self):
        """Open dialog to select and load a directory."""
        dir_selected = filedialog.askdirectory(title="Select Directory")
        if not dir_selected:
            return None

        # Clear existing data
        self.tree.delete(*self.tree.get_children())
        self.tree_item_to_path.clear()
        self.tree_item_original_text.clear()

        # Update status if available
        if hasattr(self, 'status_update') and self.status_update:
            self.status_update(f"Loading directory: {dir_selected}")

        # Start loading in a separate thread
        threading.Thread(
            target=self.populate_tree, 
            args=("", dir_selected), 
            daemon=True
        ).start()
        
        self.log(f"Loading directory: {dir_selected}")
        return dir_selected
        
    def populate_tree(self, parent, path):
        """
        Populate the tree using scandir for improved performance.
        
        Args:
            parent: Parent node in the tree
            path: File system path to populate
        """
        try:
            entries = list(os.scandir(path))
            entries.sort(key=lambda e: e.name.lower())  # Sort entries

            for entry in entries:
                full_entry = os.path.join(path, entry.name)
                icon = self._get_file_icon(full_entry)
                display_text = f"{icon} {entry.name}"
                node = self.tree.insert(parent, 'end', text=display_text, open=False)
                self.tree_item_to_path[node] = full_entry
                self.tree_item_original_text[node] = display_text
                
                if entry.is_dir():
                    # Insert a dummy child to show the expand arrow
                    self.tree.insert(node, 'end', text='Loading...')
        except PermissionError:
            pass  # Skip directories that cannot be accessed
            
    def load_tree_node(self, event):
        """
        Load the child nodes when a tree node is expanded.
        
        Args:
            event: The TreeviewOpen event
        """
        item = self.tree.selection()[0]
        path = self.tree_item_to_path[item]

        # Remove dummy child
        if (children := self.tree.get_children(item)):
            first_child = children[0]
            if self.tree.item(first_child, 'text') == 'Loading...':
                self.tree.delete(first_child)

        try:
            entries = list(os.scandir(path))
            entries.sort(key=lambda e: e.name.lower())

            for entry in entries:
                full_entry = os.path.join(path, entry.name)
                icon = self._get_file_icon(full_entry)
                display_text = f"{icon} {entry.name}"
                node = self.tree.insert(item, 'end', text=display_text, open=False)
                self.tree_item_to_path[node] = full_entry
                self.tree_item_original_text[node] = display_text
                
                if entry.is_dir():
                    self.tree.insert(node, 'end', text='Loading...')
        except PermissionError:
            pass
            
    def _get_file_icon(self, path):
        """
        Return an icon based on file type or folder.
        
        Args:
            path: Path to file or folder
            
        Returns:
            str: Emoji icon representing the file type
        """
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
            '.json': '🔧',
            '.md': '📝',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.xml': '📋',
            '.svg': '🖼️',
            '.png': '🖼️',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.gif': '🖼️'
        }
        return mapping.get(ext, "📄")
        
    def on_tree_selection(self, event):
        """
        Handle tree selection events.
        
        Args:
            event: The TreeviewSelect event
        """
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        path = self.tree_item_to_path.get(item)
        if path and os.path.isfile(path) and self.on_select:
            self.on_select(path)
            
    def on_tree_item_double_click(self, event):
        """
        Handle double-click events on tree items.
        
        Args:
            event: The double-click event
        """
        if self.on_double_click:
            item = self.tree.identify_row(event.y)
            if item:
                path = self.tree_item_to_path.get(item)
                if path:
                    self.on_double_click(path)
            
    def on_tree_context_menu(self, event):
        """
        Handle right-click events for context menu.
        
        Args:
            event: The right-click event
        """
        if self.on_context_menu:
            item = self.tree.identify_row(event.y)
            if item:
                path = self.tree_item_to_path.get(item)
                if path:
                    self.tree.selection_set(item)
                    self.on_context_menu(path, event.x_root, event.y_root)
                    
    def on_tree_item_triple_click(self, event):
        """
        Handle triple-click events on folder items.
        
        Args:
            event: The triple-click event
        
        Returns:
            list: List of file paths if a folder was triple-clicked,
                  None otherwise
        """
        item = self.tree.identify_row(event.y)
        if not item:
            return None
            
        path = self.tree_item_to_path.get(item)
        if not path or not os.path.isdir(path):
            return None
            
        # Collect all files in the folder
        file_paths = []
        for root, _, files in os.walk(path):
            for file in files:
                file_paths.append(os.path.join(root, file))
                
        # Update visual indication
        original = self.tree_item_original_text.get(item, "")
        self.tree.item(item, text=f"{original} ✓", tags=("selected",))
        self.tree.tag_configure("selected", background="lightblue")
        
        self.log(f"Selected all files from folder: {path}")
        return file_paths
        
    def mark_file_selected(self, path, selected=True):
        """
        Mark a file in the tree as selected or unselected.
        
        Args:
            path: Path to the file
            selected: True if file should be marked as selected,
                     False otherwise
        """
        # Find the tree item for this path
        item = None
        for tree_id, tree_path in self.tree_item_to_path.items():
            if tree_path == path:
                item = tree_id
                break
                
        if not item:
            return
            
        original = self.tree_item_original_text.get(item, "")
        if selected:
            self.tree.item(item, text=f"{original} ✓", tags=("selected",))
            self.tree.tag_configure("selected", background="lightblue")
        else:
            self.tree.item(item, text=original, tags=())
            
    def get_selected_path(self):
        """
        Get the file path of the currently selected tree item.
        
        Returns:
            str: Path to selected file, or None if no file is selected
        """
        selected = self.tree.selection()
        if not selected:
            return None
            
        item = selected[0]
        path = self.tree_item_to_path.get(item)
        if path and os.path.isfile(path):
            return path
        return None
        
    def refresh(self):
        """Refresh the current tree view."""
        # Remember the current selection
        selected = self.tree.selection()
        selected_paths = [self.tree_item_to_path.get(item) for item in selected]
        
        # Remember expanded nodes
        expanded = []
        for item in self.tree_item_to_path:
            if self.tree.item(item, 'open'):
                expanded.append(self.tree_item_to_path.get(item))
                
        # Find the root directory
        root_items = self.tree.get_children("")
        if not root_items:
            return
            
        root_path = None
        for item in root_items:
            if item in self.tree_item_to_path:
                root_path = os.path.dirname(self.tree_item_to_path[item])
                break
                
        if not root_path:
            return
            
        # Reload the tree
        self.tree.delete(*self.tree.get_children())
        self.tree_item_to_path.clear()
        self.tree_item_original_text.clear()
        
        threading.Thread(
            target=self.populate_tree, 
            args=("", root_path), 
            daemon=True
        ).start()
        
        self.log(f"Refreshed file tree")
