"""
Search Handler for the File Concatenator application.

This module provides file search functionality with:
- Filename search
- Content search
- File extension filtering
- Real-time search results
"""

import os
import tkinter as tk
from tkinter import ttk

class SearchHandler:
    """
    Manages file search functionality for the application.
    
    This class encapsulates:
    - Search interface creation
    - Different search types (name, content, extension)
    - Search result highlighting
    - Search state management
    
    It provides a complete search experience while isolating
    search logic from the main application.
    """
    
    def __init__(self, parent, tree_manager, log_callback):
        """
        Initialize the search handler.
        
        Args:
            parent: Parent widget to contain search controls
            tree_manager: FileTreeManager instance to search within
            log_callback: Function to use for logging operations
        """
        self.parent = parent
        self.tree_manager = tree_manager
        self.log = log_callback
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and configure the search widgets."""
        search_frame = ttk.Frame(self.parent)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True)
        
        self.search_type = tk.StringVar(value="name")
        type_menu = ttk.OptionMenu(search_frame, self.search_type, 
                                 "name", "name", "content", "extension",
                                 command=self._on_search_type_changed)
        type_menu.pack(side='right', padx=(5,0))
        
        # Clear button with icon
        ttk.Button(search_frame, text="❌", width=3, 
                  command=self.clear_search).pack(side='right', padx=2)

    def clear_search(self):
        """Clear the search box and reset tree view."""
        self.search_var.set('')
        self._clear_tree_tags()
        
    def _on_search_changed(self, *args):
        """Handle search text changes."""
        self._filter_tree()
        
    def _on_search_type_changed(self, *args):
        """Handle search type changes."""
        self._filter_tree()
        
    def _filter_tree(self):
        """Filter treeview items based on search criteria."""
        search_text = self.search_var.get().lower()
        search_type = self.search_type.get()
        
        # Clear all tags first
        self._clear_tree_tags()
        
        if not search_text:
            return
        
        # Get tree and tree_item_to_path from tree_manager
        tree = self.tree_manager.tree
        tree_item_to_path = self.tree_manager.tree_item_to_path
        
        # Search and highlight matching items
        for item in tree.get_children():
            self._search_tree_item(tree, tree_item_to_path, item, search_text, search_type, depth=3)
    
    def _clear_tree_tags(self):
        """Clear search highlighting from the tree."""
        tree = self.tree_manager.tree
        for item in tree.get_children():
            self._clear_item_tags(tree, item)
    
    def _clear_item_tags(self, tree, item):
        """Recursively clear tags from a tree item and its children."""
        # Keep 'selected' tag if it exists
        tags = tree.item(item, 'tags')
        if 'selected' in tags:
            tree.item(item, tags=('selected',))
        else:
            tree.item(item, tags=())
        
        # Process children
        for child in tree.get_children(item):
            self._clear_item_tags(tree, child)
    
    def _search_tree_item(self, tree, tree_item_to_path, item, search_text, search_type, depth):
        """
        Recursively search through tree items.
        
        Args:
            tree: The Treeview widget
            tree_item_to_path: Mapping from tree items to file paths
            item: Current tree item to search
            search_text: Text to search for
            search_type: Type of search (name, content, extension)
            depth: Maximum recursion depth
        """
        if depth <= 0:
            return  # Stop recursion if depth is reached
        
        path = tree_item_to_path.get(item)
        if not path:
            return
            
        match = False
        
        if search_type == "name":
            match = search_text in os.path.basename(path).lower()
        elif search_type == "extension" and os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            match = search_text in ext
        elif search_type == "content" and os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(1024)  # Read first 1KB only for performance
                    match = search_text in content.lower()
            except:
                pass  # Ignore files that can't be read
        
        if match:
            # Keep existing tags and add 'match' tag
            tags = list(tree.item(item, 'tags'))
            if 'match' not in tags:
                tags.append('match')
                tree.item(item, tags=tags)
                tree.tag_configure('match', background='lightyellow')
                
            # Make sure the item is visible
            tree.see(item)
        
        # Recursively search children
        for child in tree.get_children(item):
            self._search_tree_item(tree, tree_item_to_path, child, search_text, search_type, depth - 1)
