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
from tkinterdnd2 import DND_FILES, TkinterDnD
from app_config import DEFAULT_OUTPUT_FILE, OUTPUT_DIR
from context_manager import ContextManager
from editor_manager import EditorManager
from file_tree_manager import FileTreeManager
from search_handler import SearchHandler

# Simple tooltip implementation
class ToolTip:
    """Provides a tooltip for any widget."""
    
    def __init__(self, widget, text):
        """
        Initialize a tooltip for a widget.
        
        Args:
            widget: The widget to attach the tooltip to
            text: The tooltip text
        """
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        """Display the tooltip."""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip, 
            text=self.text, 
            background="#FFFFE0", 
            relief='solid', 
            borderwidth=1,
            font=("Segoe UI", "8", "normal")
        )
        label.pack()

    def hide_tip(self, event=None):
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = None

class FileConcatenatorApp(TkinterDnD.Tk):
    """
    Main application window for the File Concatenator utility.
    
    This class serves as the orchestrator for the application, integrating
    the various component managers (editor, file tree, search, context) and
    providing the overall application flow.
    
    The GUI is divided into two main panels:
    1. Left panel: File explorer with preview
    2. Right panel: Selected files list and operation log
    """
    
    def __init__(self):
        """Initialize the application window and set up all GUI components."""
        super().__init__()
        self.title("File Concatenator Utility")
        self.geometry("1200x800")
        self.style, self.colors = ThemeConfig.setup_theme()

        # Core application state
        self.master_filename = DEFAULT_OUTPUT_FILE

        # Create the main split pane
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left frame: File Explorer Panel
        self.frame_explorer = ttk.Frame(self.paned)
        self.paned.add(self.frame_explorer, weight=1)
        
        # Create vertical paned window inside the left frame
        self.explorer_paned = ttk.PanedWindow(self.frame_explorer, orient="vertical")
        self.explorer_paned.pack(fill="both", expand=True)
        
        # Create frames for tree area and editor area
        self.frame_tree_area = ttk.Frame(self.explorer_paned)
        self.frame_editor_area = ttk.Frame(self.explorer_paned)
        
        # Add frames to the vertical paned window
        self.explorer_paned.add(self.frame_tree_area, weight=1)  # Give tree more initial space
        self.explorer_paned.add(self.frame_editor_area, weight=1)

        # Right frame: Selected Files and Log
        self.frame_main = ttk.Frame(self.paned)
        self.paned.add(self.frame_main, weight=2)

        # Set up component managers
        self._setup_component_managers()
        
        # Create the UI components
        self._create_explorer_panel()
        self._create_main_panel()
        
        # Set up status bar
        self._create_status_bar()

        # Configure drag-drop support
        self.listbox_files.drop_target_register(DND_FILES)
        self.listbox_files.dnd_bind('<<Drop>>', self.handle_drop)

        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.quit)

        # Start the application
        self.log("Application started. Use 'Load Directory' to select a folder.")

    def _setup_component_managers(self):
        """Initialize the component managers."""
        # Initialize context manager first as others might need it
        self.context_manager = ContextManager(self.log)
        
        # Initialize file tree manager with callbacks - use tree area as parent
        self.file_tree_manager = FileTreeManager(
            self.frame_tree_area,
            self.log,
            on_select_callback=self.on_file_selected,
            on_double_click=self.toggle_file_inclusion,
            on_context_menu=self.show_context_menu
        )
        
        # Initialize search handler - use tree area as parent
        self.search_handler = SearchHandler(
            self.frame_tree_area,
            self.file_tree_manager,
            self.log
        )
        
        # Initialize editor manager - use editor area as parent
        self.editor_manager = EditorManager(self.frame_editor_area, self.log)

    def _create_explorer_panel(self):
        """Configure the file explorer panel."""
        # Search handler already creates its own widgets
        
        # Tree manager creates its widgets in its parent
        
        # Editor manager creates its widgets in its parent

    def _create_main_panel(self):
        """Configure the main panel with file list and log."""
        # Create context management widgets
        self._create_context_widgets()
        
        # Create quick notes area
        self._create_quick_notes()
        
        # Create selected files list
        self._create_file_list()
        
        # Create action buttons
        self._create_action_buttons()
        
        # Create log panel
        self._create_log_panel()

    def _create_context_widgets(self):
        """Create widgets for managing different file contexts."""
        # Create a context management section
        self.context_frame = ttk.LabelFrame(self.frame_main, text="💼 Working Context")
        self.context_frame.pack(fill="x", padx=10, pady=5)
        
        # Add help/info button
        info_btn = ttk.Button(self.context_frame, text="ℹ️", width=3,
                            command=self.show_context_help)
        info_btn.pack(side="right", padx=5)
        ToolTip(info_btn, "Learn more about Working Contexts")
        
        # Context naming and saving
        name_frame = ttk.Frame(self.context_frame)
        name_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(name_frame, text="Context Name:").pack(side="left")
        self.context_name = ttk.Entry(name_frame)
        self.context_name.pack(side="left", fill="x", expand=True, padx=5)
        
        # Context actions with improved icons
        btn_frame = ttk.Frame(self.context_frame)
        btn_frame.pack(fill="x", padx=5, pady=2)
        
        save_btn = ttk.Button(btn_frame, text="💾 Save Context",
                           command=self.save_current_context, compound='left')
        save_btn.pack(side="left", padx=2)
        ToolTip(save_btn, "Save current files and notes as a named context")
        
        export_btn = ttk.Button(btn_frame, text="📤 Export",
                             command=self.export_context, compound='left')
        export_btn.pack(side="left", padx=2)
        ToolTip(export_btn, "Export context to a JSON or Markdown file")
        
        import_btn = ttk.Button(btn_frame, text="📥 Import",
                             command=self.import_context, compound='left')
        import_btn.pack(side="left", padx=2)
        ToolTip(import_btn, "Import context from a JSON file")
        
        # Context selector
        select_frame = ttk.Frame(self.context_frame)
        select_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(select_frame, text="Load Context:").pack(side="left")
        self.context_combo = ttk.Combobox(select_frame, state="readonly")
        self.context_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.context_combo.bind("<<ComboboxSelected>>", self.load_context)
        ToolTip(self.context_combo, "Select a saved context to load")

    def _create_quick_notes(self):
        """Create a quick notes panel for temporary thoughts."""
        notes_frame = ttk.LabelFrame(self.frame_main, text="✏️ Quick Notes")
        notes_frame.pack(fill="x", padx=10, pady=5)
        
        self.notes_text = scrolledtext.ScrolledText(notes_frame, height=3,
                                                  font=Font(family="Segoe UI", size=10))
        self.notes_text.pack(fill="x", padx=5, pady=5)

    def _create_file_list(self):
        """Create the selected files list panel with reordering."""
        # Frame for Selected Files List
        self.frame_files = ttk.LabelFrame(self.frame_main, text="Selected Files")
        self.frame_files.pack(fill="both", expand=True, padx=10, pady=10)

        # File list container
        list_frame = ttk.Frame(self.frame_files)
        list_frame.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        # Listbox
        self.listbox_files = tk.Listbox(list_frame, selectmode="extended", 
                                     bg=self.colors['bg'],
                                     fg=self.colors['fg'],
                                     selectbackground=self.colors['selected'],
                                     selectforeground='#ffffff',
                                     borderwidth=1)
        self.listbox_files.pack(side="left", fill="both", expand=True)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox_files.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox_files.config(yscrollcommand=scrollbar.set)
        
        # Reordering buttons
        btn_frame = ttk.Frame(self.frame_files)
        btn_frame.pack(side="left", fill="y", padx=(5, 10), pady=10)
        
        up_btn = ttk.Button(btn_frame, text="🔼", width=3, command=self.move_item_up)
        up_btn.pack(side="top", pady=2)
        ToolTip(up_btn, "Move selected file(s) up")
        
        down_btn = ttk.Button(btn_frame, text="🔽", width=3, command=self.move_item_down)
        down_btn.pack(side="top", pady=2)
        ToolTip(down_btn, "Move selected file(s) down")

    def _create_action_buttons(self):
        """Create operation buttons with icons and tooltips."""
        frame_buttons = ttk.Frame(self.frame_main)
        frame_buttons.pack(fill="x", padx=10, pady=5)

        btn_add = ttk.Button(frame_buttons, text="➕ Add Files", 
                          command=self.add_files, compound='left')
        btn_add.pack(side="left", padx=5)
        ToolTip(btn_add, "Add files to the list")

        btn_remove = ttk.Button(frame_buttons, text="➖ Remove", 
                             command=self.remove_selected, compound='left')
        btn_remove.pack(side="left", padx=5)
        ToolTip(btn_remove, "Remove selected files from the list")

        btn_clear = ttk.Button(frame_buttons, text="🗑️ Clear", 
                            command=self.clear_list, compound='left')
        btn_clear.pack(side="left", padx=5)
        ToolTip(btn_clear, "Clear the entire file list")

        btn_concat = ttk.Button(frame_buttons, text="⚙️ Concatenate", 
                             command=self.concatenate_files, compound='left')
        btn_concat.pack(side="right", padx=5)
        ToolTip(btn_concat, "Concatenate all files in the list")
        
        btn_exit = ttk.Button(frame_buttons, text="🚪 Exit", 
                           command=self.quit, compound='left')
        btn_exit.pack(side="right", padx=5)
        ToolTip(btn_exit, "Exit the application")

    def _create_log_panel(self):
        """Create the log panel."""
        frame_log = ttk.LabelFrame(self.frame_main, text="Log")
        frame_log.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text = scrolledtext.ScrolledText(frame_log, wrap="word", height=10)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_status_bar(self):
        """Create the application status bar."""
        self.status_bar = ttk.Frame(self, style="StatusBar.TFrame")
        self.status_bar.pack(side="bottom", fill="x")
        
        self.status_label = ttk.Label(self.status_bar, style="StatusBar.TLabel", text="Ready")
        self.status_label.pack(side="left", padx=5)
        
        self.progress_bar = ttk.Progressbar(self.status_bar, mode='determinate', length=200)
        self.progress_bar.pack(side="right", padx=5, pady=2)
        
        # Add focus mode toggle
        self._create_focus_mode_widget()

    def _create_focus_mode_widget(self):
        """Create focus mode toggle in status bar."""
        focus_frame = ttk.Frame(self.status_bar)
        focus_frame.pack(side="right", padx=10)
        
        self.focus_var = tk.BooleanVar(value=False)
        focus_check = ttk.Checkbutton(focus_frame, text="Focus Mode", 
                                    variable=self.focus_var,
                                    command=self.toggle_focus_mode)
        focus_check.pack()
        ToolTip(focus_check, "Hide the file explorer for focused work")

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
            self.status_label.config(text=f"{count} file(s) added. Total: {self.listbox_files.size()} files")

    def remove_selected(self):
        """Remove the selected file(s) from the list."""
        selected_indices = list(self.listbox_files.curselection())
        if not selected_indices:
            self.status_label.config(text="No files selected for removal")
            return
            
        selected_indices.sort(reverse=True)
        for index in selected_indices:
            file_path = self.listbox_files.get(index)
            self.listbox_files.delete(index)
            # Update visual indication in tree if file is visible
            self.file_tree_manager.mark_file_selected(file_path, False)
            
        removed_count = len(selected_indices)
        self.log(f"Removed {removed_count} selected file(s).")
        self.status_label.config(text=f"{removed_count} file(s) removed. Remaining: {self.listbox_files.size()} files")

    def clear_list(self):
        """Clear all files from the selection list."""
        if self.listbox_files.size() == 0:
            self.status_label.config(text="File list is already empty")
            return
            
        file_count = self.listbox_files.size()
        
        # Clear visual indications from the tree
        for file_path in self.listbox_files.get(0, END):
            self.file_tree_manager.mark_file_selected(file_path, False)
            
        # Clear the list
        self.listbox_files.delete(0, END)
        
        self.log(f"Cleared {file_count} file(s) from list.")
        self.status_label.config(text=f"File list cleared ({file_count} files removed)")

    def move_item_up(self):
        """Move selected item(s) up in the listbox."""
        selected_indices = list(self.listbox_files.curselection())
        if not selected_indices:
            self.status_label.config(text="No files selected to move")
            return
            
        # Sort indices to maintain relative order
        selected_indices.sort()
        
        # Skip if top item is already at the top
        if selected_indices[0] == 0:
            self.status_label.config(text="Item(s) already at the top")
            return
            
        # Move each selected item up one position
        for index in selected_indices:
            if index > 0:  # Not already at the top
                item = self.listbox_files.get(index)
                self.listbox_files.delete(index)
                self.listbox_files.insert(index - 1, item)
                self.listbox_files.selection_set(index - 1)
        
        # Update status
        self.status_label.config(text="Item(s) moved up")
        self.log("Reordered file list: item(s) moved up.")

    def move_item_down(self):
        """Move selected item(s) down in the listbox."""
        selected_indices = list(self.listbox_files.curselection())
        if not selected_indices:
            self.status_label.config(text="No files selected to move")
            return
            
        # Sort indices in reverse to maintain relative order when moving down
        selected_indices.sort(reverse=True)
        
        # Skip if bottom item is already at the bottom
        last_index = self.listbox_files.size() - 1
        if selected_indices[0] == last_index:
            self.status_label.config(text="Item(s) already at the bottom")
            return
            
        # Move each selected item down one position
        for index in selected_indices:
            if index < last_index:  # Not already at the bottom
                item = self.listbox_files.get(index)
                self.listbox_files.delete(index)
                self.listbox_files.insert(index + 1, item)
                self.listbox_files.selection_set(index + 1)
        
        # Update status
        self.status_label.config(text="Item(s) moved down")
        self.log("Reordered file list: item(s) moved down.")

    def concatenate_files(self):
        """Initiate file concatenation process in a separate thread."""
        files = self.listbox_files.get(0, END)
        if not files:
            messagebox.showwarning("No Files Selected", "Please add files to concatenate.")
            return
            
        if not messagebox.askyesno("Confirm Concatenation",
                                 "This will create a backup of the existing master file (if any) and overwrite it. Continue?"):
            return

        self.status_label.config(text="Concatenation started...")
        self.log("Starting concatenation process...")
        threading.Thread(target=self.run_concatenation, args=(files,), daemon=True).start()

    def run_concatenation(self, files):
        """Execute the concatenation in a background thread."""
        file_io_utils.create_backup(self.master_filename, self.log)
        try:
            open(self.master_filename, 'w').close()
            self.log("Cleared existing master file.")
        except Exception as e:
            self.log(f"Error clearing master file: {e}")
            self.status_label.config(text=f"Error: {e}")
            return
            
        file_io_utils.write_directory_structure(self.master_filename, files, self.log)
        
        # Update progress as files are processed
        total_files = len(files)
        for i, file in enumerate(files):
            content = file_io_utils.load_file(file, self.log)
            if content is not None:
                file_io_utils.append_to_master(self.master_filename, file, content, self.log)
                
                # Update progress in GUI thread
                progress_pct = int(((i + 1) / total_files) * 100)
                self.progress_bar["value"] = progress_pct
                self.status_label.config(text=f"Concatenating: {i+1}/{total_files} files ({progress_pct}%)")
                self.update_idletasks()  # Force GUI update
                
        self.log("Concatenation process completed.")
        self.status_label.config(text=f"Concatenation complete - {total_files} files processed")
        messagebox.showinfo("Completed", f"Files have been concatenated into {self.master_filename}.")
        
        # Reset progress bar
        self.progress_bar["value"] = 0

    def on_file_selected(self, path):
        """Handle file selection in the tree view."""
        # Load the file in the editor
        if self.editor_manager.load_file(path):
            self.status_label.config(text=f"Loaded: {os.path.basename(path)}")

    def toggle_file_inclusion(self, path):
        """Toggle inclusion of a file in the selection list."""
        if not path or os.path.isdir(path):
            return  # Only handle files
            
        # Check if file is already in the list
        current_files = self.listbox_files.get(0, END)
        if path in current_files:
            # Remove from listbox
            idx = current_files.index(path)
            self.listbox_files.delete(idx)
            self.log(f"Removed: {path}")
            self.file_tree_manager.mark_file_selected(path, False)
            self.status_label.config(text=f"Removed: {os.path.basename(path)}")
        else:
            # Add to listbox
            self.listbox_files.insert(END, path)
            self.log(f"Added: {path}")
            self.file_tree_manager.mark_file_selected(path, True)
            self.status_label.config(text=f"Added: {os.path.basename(path)}")

    def show_context_menu(self, path, x, y):
        """Display a context menu for a file."""
        menu = tk.Menu(self, tearoff=0)
        
        if os.path.isfile(path):
            # Get current state
            current_files = self.listbox_files.get(0, END)
            is_included = path in current_files
            
            # Menu items
            menu.add_command(
                label="Remove from List" if is_included else "Add to List",
                command=lambda: self.toggle_file_inclusion(path)
            )
            
            menu.add_command(
                label="Open in Editor",
                command=lambda: self.editor_manager.load_file(path)
            )
            
            menu.add_command(
                label="Open in Default Application",
                command=lambda: os.startfile(path)
            )
            
        menu.tk_popup(x, y)

    def handle_drop(self, event):
        """Handle drag and drop of files."""
        if event.data:
            # Process each file
            count = 0
            current_files = self.listbox_files.get(0, tk.END)
            
            # Split data into individual files (handles multiple files)
            import shlex
            files = shlex.split(event.data)
            
            for file in files:
                # Clean up file path based on system
                file = file.strip('{}').replace('\\', '/')
                if file not in current_files:
                    self.listbox_files.insert(tk.END, file)
                    # Update visual indication in tree if file is visible
                    self.file_tree_manager.mark_file_selected(file, True)
                    count += 1
            
            self.log(f"Added {count} dropped file(s).")
            self.status_label.config(text=f"{count} file(s) added via drag and drop")

    def show_context_help(self):
        """Show help dialog explaining contexts."""
        help_text = self.context_manager.help_text()
        messagebox.showinfo("About Working Contexts", help_text.strip())

    def export_context(self):
        """Export the current context to a file."""
        result = self.context_manager.export_context()
        if result:
            self.status_label.config(text="Context exported successfully")

    def import_context(self):
        """Import a context from a JSON file."""
        context_name = self.context_manager.import_context()
        if context_name:
            self.update_context_combo()
            self.status_label.config(text=f"Context '{context_name}' imported")

    def save_current_context(self):
        """Save the current workspace as a named context."""
        name = self.context_name.get().strip()
        if not name:
            self.status_label.config(text="Please enter a name for the context")
            return
            
        files = list(self.listbox_files.get(0, END))
        notes = self.notes_text.get("1.0", END)
        
        if self.context_manager.save_context(name, files, notes):
            self.update_context_combo()
            self.status_label.config(text=f"Context '{name}' saved")

    def update_context_combo(self):
        """Update the context combo box with saved contexts."""
        contexts = self.context_manager.get_context_names()
        self.context_combo['values'] = contexts
        if contexts:
            self.context_combo.set(contexts[0])

    def load_context(self, event=None):
        """Load a previously saved context."""
        name = self.context_combo.get()
        if not name:
            return
        
        # Check for unsaved changes
        if self.editor_manager.has_unsaved_changes():
            if not self.editor_manager.prompt_save_changes():
                return
        
        context = self.context_manager.load_context(name)
        if not context:
            return
        
        # Clear current selected files and update tree indications
        for file_path in self.listbox_files.get(0, END):
            self.file_tree_manager.mark_file_selected(file_path, False)
            
        # Clear current state
        self.listbox_files.delete(0, END)
        self.notes_text.delete("1.0", END)
        
        # Load context state
        for file in context['files']:
            self.listbox_files.insert(END, file)
            # Update visual indication in tree if file is visible
            self.file_tree_manager.mark_file_selected(file, True)
        
        self.notes_text.insert("1.0", context.get('notes', ''))
        
        # Update UI
        self.context_name.delete(0, END)
        self.context_name.insert(0, name)
        
        self.status_label.config(text=f"Context '{name}' loaded with {len(context['files'])} files")

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
    
    def quit(self):
        """Override quit to check for unsaved changes."""
        if self.editor_manager.has_unsaved_changes():
            if not self.editor_manager.prompt_save_changes():
                return  # Cancel quit if user cancels save
        super().quit()
