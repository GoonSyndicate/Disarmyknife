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
import token_utils
from settings_manager import settings
from settings_dialog import SettingsDialog

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
        
        # Apply window size from settings
        window_settings = settings.get_window_settings()
        geometry = f"{window_settings['width']}x{window_settings['height']}"
        if window_settings["position_x"] and window_settings["position_y"]:
            geometry += f"+{window_settings['position_x']}+{window_settings['position_y']}"
        self.geometry(geometry)
        
        # Save window position on close
        self.bind("<Configure>", self._on_window_configure)
        
        # Add focus event to check for externally modified files
        self.bind("<FocusIn>", self._on_app_focus)
        
        self.style, self.colors = ThemeConfig.setup_theme()

        # Core application state
        output_settings = settings.get_output_settings()
        self.master_filename = os.path.join(OUTPUT_DIR, output_settings["filename"])

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

        # Create log panel early so we can use self.log
        self._create_log_panel()

        # Set up component managers - now log method is available
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

        # Initialize token count tracking
        self.token_count = 0
        self.token_encoding = "cl100k_base"  # Default encoding (GPT-4/ChatGPT)
        
        # Start the application
        self.log("Application started. Use 'Load Directory' to select a folder.")

        # Set initial token count
        self.update_token_count()

        # Restore last session if available
        self.after(100, self.restore_last_session)  # Short delay to ensure UI is ready

        # Add context state tracking
        self.loaded_context_state = None
        self.is_context_synced = True  # Assume synced initially or when no context loaded

    def log(self, message):
        """
        Add a timestamped message to the log panel.
        
        Args:
            message (str): The message to log
        """
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        self.log_text.insert("end", timestamp + message + "\n")
        self.log_text.see("end")

    def _create_log_panel(self):
        """Create the log panel."""
        frame_log = ttk.LabelFrame(self.frame_main, text="Log")
        frame_log.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text = scrolledtext.ScrolledText(frame_log, wrap="word", height=10)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_window_configure(self, event):
        """Save window position when it changes."""
        # Only save if it's the main window changing, not a child window
        if event.widget == self:
            # Delay updating to avoid excessive writes
            self.after_cancel(self._save_position_timer) if hasattr(self, '_save_position_timer') else None
            self._save_position_timer = self.after(500, self._save_window_position)
            
    def _save_window_position(self):
        """Save the window position to settings."""
        width = self.winfo_width()
        height = self.winfo_height()
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        settings.set_window_settings(width, height, x, y)

    def _on_app_focus(self, event):
        """
        Check for externally modified files when the application regains focus.
        
        Args:
            event: The focus event
        """
        # Only process if the main window receives focus
        if event.widget != self:
            return
            
        # Check if we have an editor with a file open
        if hasattr(self, 'editor_manager') and self.editor_manager.current_file:
            # See if the file has been modified externally
            try:
                current_mtime = os.path.getmtime(self.editor_manager.current_file)
                if hasattr(self.editor_manager, 'last_mtime') and self.editor_manager.last_mtime is not None:
                    if current_mtime != self.editor_manager.last_mtime and not self.editor_manager.modified:
                        # File has been modified externally and we have no local changes
                        response = messagebox.askyesno(
                            "File Changed Externally",
                            f"The file '{os.path.basename(self.editor_manager.current_file)}' has been modified outside the editor.\n\n"
                            "Do you want to reload it?",
                            icon="info"
                        )
                        if response:
                            self.editor_manager.sync_file()
            except Exception as e:
                self.log(f"Error checking for external file changes: {e}")

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
        """Display a context menu for a file or folder."""
        menu = tk.Menu(self, tearoff=0)
        is_file = os.path.isfile(path)
        is_dir = os.path.isdir(path)

        if is_file:
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
        elif is_dir:
            menu.add_command(
                label="Add All Files (Recursive)",
                command=lambda p=path: self.add_all_files_from_folder(p)
            )
            
        menu.tk_popup(x, y)

    def add_all_files_from_folder(self, folder_path):
        """Recursively add all files from a folder to the list."""
        count = 0
        current_files = self.listbox_files.get(0, END)
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file).replace('\\', '/') # Normalize path
                if full_path not in current_files:
                    self.listbox_files.insert(END, full_path)
                    self.file_tree_manager.mark_file_selected(full_path, True)
                    count += 1
        self.log(f"Added {count} file(s) from folder: {folder_path}")
        self.update_status(f"{count} file(s) added from folder. Total: {self.listbox_files.size()} files")
        self.update_token_count()
        self._check_context_sync() # Check sync status

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
            on_context_menu=self.show_context_menu,
            status_update=self.update_status  # Pass status update callback
        )
        
        # Initialize search handler - use tree area as parent
        self.search_handler = SearchHandler(
            self.frame_tree_area,
            self.file_tree_manager,
            self.log
        )
        
        # Initialize editor manager - use editor area as parent
        self.editor_manager = EditorManager(
            self.frame_editor_area, 
            self.log,
            status_update=self.update_status  # Pass status update callback
        )

    def update_status(self, message):
        """Update the status bar label with a message.
        
        Args:
            message (str): The message to display in the status bar
        """
        self.status_label.config(text=message)
        self.update_idletasks()  # Force immediate update

    def _create_explorer_panel(self):
        """Configure the file explorer panel."""
        # Search handler already creates its own widgets
        
        # Tree manager creates its widgets in its parent
        
        # Editor manager creates its widgets in its parent

    def _create_main_panel(self):
        """Configure the main panel with file list and log."""
        # Create selected files list first
        self._create_file_list()
        
        # Create context management widgets
        self._create_context_widgets()
        
        # Create quick notes area
        self._create_quick_notes()
        
        # Create action buttons
        self._create_action_buttons()
        
        # Set up context change tracking (after all widgets are created)
        self._setup_context_change_tracking()

    def _create_context_widgets(self):
        """Create widgets for managing different file contexts."""
        # Create a context management section
        self.context_frame = ttk.LabelFrame(self.frame_main, text="💼 Task Snapshot")
        self.context_frame.pack(fill="x", padx=10, pady=5)
        
        # Add help/info button
        info_btn = ttk.Button(self.context_frame, text="ℹ️", width=3,
                            command=self.show_context_help)
        info_btn.pack(side="right", padx=5)
        ToolTip(info_btn, "Learn more about Task Snapshots (formerly Working Contexts)")
        
        # Context naming and saving
        name_frame = ttk.Frame(self.context_frame)
        name_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(name_frame, text="Snapshot Name:").pack(side="left")
        self.context_name = ttk.Entry(name_frame)
        self.context_name.pack(side="left", fill="x", expand=True, padx=5)
        
        # Context actions with improved icons
        btn_frame = ttk.Frame(self.context_frame)
        btn_frame.pack(fill="x", padx=5, pady=2)
        
        # Keep a reference to the save button
        self.save_btn = ttk.Button(btn_frame, text="💾 Save Snapshot",
                       command=self.save_current_context, compound='left')
        self.save_btn.pack(side="left", padx=2)
        ToolTip(self.save_btn, "Save current files and notes as a named snapshot")
        
        export_btn = ttk.Button(btn_frame, text="📤 Export",
                            command=self.export_context, compound='left')
        export_btn.pack(side="left", padx=2)
        ToolTip(export_btn, "Export snapshot to a JSON or Markdown file")
        
        import_btn = ttk.Button(btn_frame, text="📥 Import",
                            command=self.import_context, compound='left')
        import_btn.pack(side="left", padx=2)
        ToolTip(import_btn, "Import snapshot from a JSON file")
        
        # Context selector
        select_frame = ttk.Frame(self.context_frame)
        select_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(select_frame, text="Load Snapshot:").pack(side="left")
        self.context_combo = ttk.Combobox(select_frame, state="readonly")
        self.context_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.context_combo.bind("<<ComboboxSelected>>", self.load_context)
        ToolTip(self.context_combo, "Select a saved snapshot to load")
        
        # Track context state
        self._context_state_synced = True

    def _setup_context_change_tracking(self):
        """Set up tracking for changes to the context state."""
        # Setup tracking for changes in files or notes
        if hasattr(self, 'listbox_files'):
            self.listbox_files.bind('<<ListboxSelect>>', self._check_context_sync)
        
        if hasattr(self, 'notes_text'):
            self.notes_text.bind('<KeyRelease>', self._check_context_sync)

    def _reset_status_bar_color(self):
        """Reset the status bar color after a visual feedback."""
        self.status_bar.config(background=self.style.lookup("StatusBar.TFrame", "background"))

    def _create_quick_notes(self):
        """Create a notes panel for context description and task notes."""
        notes_frame = ttk.LabelFrame(self.frame_main, text="📝 Context Notes / Task Description")
        notes_frame.pack(fill="x", padx=10, pady=5)
        
        self.notes_text = scrolledtext.ScrolledText(notes_frame, height=3,
                                                  font=Font(family="Segoe UI", size=10))
        self.notes_text.pack(fill="x", padx=5, pady=5)
        
        # Add tooltip to the notes text area
        ToolTip(self.notes_text, "Add notes related to the selected files or the current task/context.")
        
        # Add placeholder text
        if not hasattr(self, 'notes_placeholder_shown') or not self.notes_placeholder_shown:
            self.notes_text.insert("1.0", "Describe what these files are for or add instructions for an LLM...")
            self.notes_text.config(foreground="gray")
            self.notes_placeholder_shown = True
            
            # Bind events to clear placeholder
            self.notes_text.bind("<FocusIn>", self._clear_notes_placeholder)
            self.notes_text.bind("<FocusOut>", self._restore_notes_placeholder)
        
        # Add binding for notes modifications
        self.notes_text.bind("<<Modified>>", self._on_notes_modified)

    def _clear_notes_placeholder(self, event=None):
        """Clear the placeholder text when the notes field gets focus."""
        if self.notes_placeholder_shown:
            self.notes_text.delete("1.0", "end")
            self.notes_text.config(foreground="black")
            self.notes_placeholder_shown = False

    def _restore_notes_placeholder(self, event=None):
        """Restore the placeholder text if the notes field is empty."""
        if not self.notes_text.get("1.0", "end-1c"):
            self.notes_text.insert("1.0", "Describe what these files are for or add instructions for an LLM...")
            self.notes_text.config(foreground="gray")
            self.notes_placeholder_shown = True

    def _track_context_changes(self, event=None):
        """Track changes in the context (files or notes) to show save indicator."""
        # If we already know it's not synced, don't recalculate
        if not self._context_state_synced:
            return
        
        # Check if current context is loaded
        current_context = self.context_manager.get_current_context()
        if not current_context:
            return  # Nothing to compare against
        
        # Compare files
        current_files = list(self.listbox_files.get(0, "end"))
        saved_files = current_context.get('files', [])
        
        files_match = (len(current_files) == len(saved_files) and 
                      all(a == b for a, b in zip(current_files, saved_files)))
        
        # Compare notes (ignore placeholder text)
        current_notes = self.notes_text.get("1.0", "end-1c")
        if self.notes_placeholder_shown:
            current_notes = ""
        saved_notes = current_context.get('notes', '').strip()
        
        # Update state and visual indicator
        if not files_match or current_notes.strip() != saved_notes:
            self._context_state_synced = False
            self._update_save_context_button_style(is_synced=False)

    def _update_save_context_button_style(self, is_synced=True):
        """Update the save context button style to indicate changes."""
        if is_synced:
            self.save_btn.configure(text="💾 Save Snapshot")
        else:
            self.save_btn.configure(text="💾 Save Snapshot*")
            
        # Could also change button style, color, etc. for more visual impact
        # self.save_btn.configure(style="Attention.TButton" if not is_synced else "TButton")

    def _create_file_list(self):
        """Create the selected files list panel with reordering and token count."""
        # Frame for Selected Files List
        self.frame_files = ttk.LabelFrame(self.frame_main, text="Selected Files")
        self.frame_files.pack(fill="both", expand=True, padx=10, pady=10)

        # Add token counter at the top
        token_frame = ttk.Frame(self.frame_files)
        token_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        ttk.Label(token_frame, text="Token Count:").pack(side="left")
        self.token_label = ttk.Label(token_frame, text="0 tokens")
        self.token_label.pack(side="left", padx=5)
        
        # Token count progress bar
        self.token_progress = ttk.Progressbar(token_frame, mode='determinate', length=100)
        self.token_progress.pack(side="left", fill="x", expand=True, padx=5)
        
        # Model selector
        models = list(token_utils.get_model_context_limits().keys())
        self.model_var = tk.StringVar(value=models[1] if len(models) > 1 else models[0])  # Default to GPT-4
        model_menu = ttk.Combobox(token_frame, textvariable=self.model_var, 
                                values=models, state="readonly", width=12)
        model_menu.pack(side="right", padx=5)
        model_menu.bind("<<ComboboxSelected>>", self.update_token_count)
        ttk.Label(token_frame, text="Model:").pack(side="right")
        
        # File list container
        list_frame = ttk.Frame(self.frame_files)
        list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

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

        # Create a frame for left-aligned buttons
        left_buttons = ttk.Frame(frame_buttons)
        left_buttons.pack(side="left", fill="x", expand=True)

        btn_add = ttk.Button(left_buttons, text="➕ Add Files", 
                          command=self.add_files, compound='left')
        btn_add.pack(side="left", padx=5)
        ToolTip(btn_add, "Add files to the list")

        btn_remove = ttk.Button(left_buttons, text="➖ Remove", 
                             command=self.remove_selected, compound='left')
        btn_remove.pack(side="left", padx=5)
        ToolTip(btn_remove, "Remove selected files from the list")

        btn_clear = ttk.Button(left_buttons, text="🗑️ Clear", 
                            command=self.clear_list, compound='left')
        btn_clear.pack(side="left", padx=5)
        ToolTip(btn_clear, "Clear the entire file list")

        # Add Copy Output button
        btn_copy = ttk.Button(left_buttons, text="📋 Copy Output", 
                           command=self.copy_output_to_clipboard, compound='left')
        btn_copy.pack(side="left", padx=5)
        ToolTip(btn_copy, "Copy the current master.txt content to clipboard")
        
        # Add Settings button
        btn_settings = ttk.Button(left_buttons, text="⚙️ Settings", 
                               command=self.show_settings_dialog, compound='left')
        btn_settings.pack(side="left", padx=5)
        ToolTip(btn_settings, "Configure output format and application settings")

        # Create a frame for right-aligned buttons
        right_buttons = ttk.Frame(frame_buttons)
        right_buttons.pack(side="right")

        btn_concat = ttk.Button(right_buttons, text="⚙️ Concatenate", 
                             command=self.concatenate_files, compound='left')
        btn_concat.pack(side="left", padx=5)
        ToolTip(btn_concat, "Concatenate all files in the list")
        
        btn_exit = ttk.Button(right_buttons, text="🚪 Exit", 
                           command=self.quit, compound='left')
        btn_exit.pack(side="left", padx=5)
        ToolTip(btn_exit, "Exit the application")

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
            
            # Update token count
            self.update_token_count()
            
            # Check context sync state
            self._check_context_sync()

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
        
        # Update token count
        self.update_token_count()
        
        # Check context sync state
        self._check_context_sync()

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
        
        # Update token count
        self.update_token_count()
        
        # Clear loaded context state
        self.loaded_context_state = None
        self.is_context_synced = True
        self._update_save_context_button_style(is_synced=True)
        self.context_frame.config(text="💼 Task Snapshot")

    def update_token_count(self, event=None):
        """Update the token count display based on current file selection."""
        # Get list of files
        files = self.listbox_files.get(0, END)
        if not files:
            self.token_count = 0
            self.token_label.config(text="0 tokens")
            self.token_progress["value"] = 0
            return
            
        # Get model context limit
        model = self.model_var.get()
        limits = token_utils.get_model_context_limits()
        limit = limits.get(model, 100000)  # Default to a high number if model not found
        
        # Get encoding from settings
        self.token_encoding = settings.get_encoding()
        
        # Start a background thread to calculate tokens
        threading.Thread(
            target=self._calculate_tokens_in_background,
            args=(files, limit),
            daemon=True
        ).start()

    def _calculate_tokens_in_background(self, files, limit):
        """Calculate token count in the background to avoid freezing the UI."""
        combined_text = ""
        
        # First collect content from all files
        for file in files:
            content = file_io_utils.load_file(file, self.log)
            if content:
                combined_text += f"\n\n{content}"
        
        # Estimate tokens
        token_count = token_utils.estimate_tokens(combined_text, self.token_encoding)
        
        # Update UI in the main thread
        self.after(0, lambda: self._update_token_display(token_count, limit))
    
    def _update_token_display(self, token_count, limit):
        """Update the token count display in the UI."""
        self.token_count = token_count if token_count is not None else 0
        
        # Format token count
        formatted_count = token_utils.format_token_count(token_count)
        
        # Update token count label
        if token_count is None:
            self.token_label.config(text="Unknown (tiktoken not installed)")
            self.token_progress["value"] = 0
        else:
            percentage = min(100, int((token_count / limit) * 100))
            self.token_label.config(
                text=f"{formatted_count} ({percentage}% of {limit:,})",
                foreground="red" if token_count > limit else "black"
            )
            self.token_progress["value"] = percentage
            
            # Set color based on usage
            if percentage < 75:
                self.token_progress["style"] = "green.Horizontal.TProgressbar"
            elif percentage < 90:
                self.token_progress["style"] = "yellow.Horizontal.TProgressbar"
            else:
                self.token_progress["style"] = "red.Horizontal.TProgressbar"

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
        
        # Check context sync state
        self._check_context_sync()

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
        
        # Check context sync state
        self._check_context_sync()

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
        
        # Copy the generated file content to clipboard
        try:
            content = file_io_utils.load_file(self.master_filename, self.log)
            if content:
                self.clipboard_clear()
                self.clipboard_append(content)
                self.log("Copied concatenated content to clipboard.")
                
                # Flash visual feedback in status bar
                self.status_label.config(text="✅ Concatenation complete - Copied to clipboard!")
                self.status_bar.config(background="#90EE90")  # Light green background
                
                # Reset status bar color after 2 seconds
                self.after(2000, self._reset_status_bar_color)
        except Exception as e:
            self.log(f"Error copying to clipboard: {e}")
            self.status_label.config(text="Concatenation complete, but clipboard copy failed")
            
        self.log("Concatenation process completed.")
        messagebox.showinfo("Completed", f"Files have been concatenated into {self.master_filename} and copied to clipboard.")
        
        # Reset progress bar
        self.progress_bar["value"] = 0

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
        messagebox.showinfo("About Task Snapshots", help_text.strip())

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
        
        # Auto-suggest name if empty
        if not name:
            # Generate a name based on files if any are selected
            files = list(self.listbox_files.get(0, END))
            if files:
                # Use first file's basename without extension as part of the suggested name
                first_file = os.path.basename(files[0])
                base_name = os.path.splitext(first_file)[0]
                suggested_name = f"{base_name}-snapshot-{datetime.now().strftime('%m%d')}"
            else:
                # Generic name if no files are selected
                suggested_name = f"snapshot-{datetime.now().strftime('%Y%m%d-%H%M')}"
            
            # Set the suggested name
            self.context_name.delete(0, END)
            self.context_name.insert(0, suggested_name)
            name = suggested_name
            self.log(f"Suggested name: {name}")
        
        # Check if name is set (should always be true now with auto-suggest)
        if not name:
            self.status_label.config(text="Please enter a name for the snapshot")
            return False
        
        # Get files and notes
        files = list(self.listbox_files.get(0, END))
        
        # Get notes, handling placeholder text
        notes = self.notes_text.get("1.0", END)
        if self.notes_placeholder_shown:
            notes = ""
        
        # Save the context
        if self.context_manager.save_context(name, files, notes):
            self.update_context_combo()
            
            # Update loaded context state to match saved state
            self.loaded_context_state = {
                'name': name,
                'files': sorted(files),
                'notes': notes.strip()
            }
            self.is_context_synced = True
            self._update_save_context_button_style(is_synced=True)
            
            # Update frame title with context name
            self.context_frame.config(text=f"💼 Task Snapshot: {name}")
            
            self.status_label.config(text=f"Snapshot '{name}' saved")
            return True
        
        return False

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
        
        # Clear notes and remove placeholder
        self.notes_text.delete("1.0", END)
        self.notes_placeholder_shown = False
        self.notes_text.config(foreground="black")
        
        # Load context state
        for file in context['files']:
            self.listbox_files.insert(END, file)
            # Update visual indication in tree if file is visible
            self.file_tree_manager.mark_file_selected(file, True)
            
            # Expand folders to show each selected file
            self.file_tree_manager.expand_to_path(file)
        
        # Add notes back if there are any
        if context.get('notes', '').strip():
            self.notes_text.insert("1.0", context.get('notes', ''))
        else:
            # If no notes, show the placeholder
            self._restore_notes_placeholder()
        
        # Update UI
        self.context_name.delete(0, END)
        self.context_name.insert(0, name)
        
        # Update loaded context state
        self.loaded_context_state = {
            'name': name,
            'files': sorted(list(context['files'])),  # Sort for consistent comparison
            'notes': context.get('notes', '').strip()
        }
        self.is_context_synced = True
        self._update_save_context_button_style(is_synced=True)
        self.context_frame.config(text=f"💼 Task Snapshot: {name}")
        
        self.status_label.config(text=f"Snapshot '{name}' loaded with {len(context['files'])} files")
        
        # Update token count based on loaded files
        self.update_token_count()

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
    
    def restore_last_session(self):
        """Restore the last session data if available."""
        session_data = settings.get_last_session()
        if not session_data:
            return
            
        selected_files = session_data.get("selected_files", [])
        quick_notes = session_data.get("quick_notes", "")
        editor_file = session_data.get("editor_file")
        
        if selected_files:
            # Load the last directory first to ensure files can be found in tree
            if selected_files and os.path.exists(selected_files[0]):
                parent_dir = os.path.dirname(selected_files[0])
                if os.path.isdir(parent_dir):
                    self.file_tree_manager.load_directory(parent_dir)
                    
            # Short delay to ensure directory is loaded
            self.after(200, lambda: self._continue_session_restore(selected_files, quick_notes, editor_file))
        elif quick_notes or editor_file:
            # If only notes or editor file but no selected files
            self._restore_notes_and_editor(quick_notes, editor_file)
            
        # Reset context state tracking
        self.loaded_context_state = None
        self.is_context_synced = True
        self.context_frame.config(text="💼 Current Session")
            
    def _continue_session_restore(self, selected_files, quick_notes, editor_file):
        """Continue restoring session after directory load."""
        valid_files = []
        for file in selected_files:
            if os.path.exists(file):
                self.listbox_files.insert(tk.END, file)
                self.file_tree_manager.mark_file_selected(file, True)
                self.file_tree_manager.expand_to_path(file)
                valid_files.append(file)
            else:
                self.log(f"Warning: File from previous session not found: {file}")
                
        if valid_files:
            self.log(f"Restored {len(valid_files)} file(s) from previous session")
            
        self._restore_notes_and_editor(quick_notes, editor_file)
        
        # Update token count based on restored files
        self.update_token_count()
        
    def _restore_notes_and_editor(self, quick_notes, editor_file):
        """Restore quick notes and editor file."""
        # Restore notes
        if quick_notes and quick_notes.strip():
            self.notes_text.delete("1.0", tk.END)
            self.notes_text.insert("1.0", quick_notes)
            self.notes_text.config(foreground="black")
            self.notes_placeholder_shown = False
        else:
            # Make sure placeholder is shown
            self._restore_notes_placeholder()
            
        # Restore editor file
        if editor_file and os.path.exists(editor_file):
            self.editor_manager.load_file(editor_file)
            self.log(f"Restored editor file: {editor_file}")

    def quit(self):
        """Override quit to check for unsaved changes and save settings."""
        if self.editor_manager.has_unsaved_changes():
            if not self.editor_manager.prompt_save_changes():
                return  # Cancel quit if user cancels save
                
        # Save session data
        selected_files = list(self.listbox_files.get(0, tk.END))
        quick_notes = self.notes_text.get("1.0", tk.END)
        editor_file = self.editor_manager.current_file
        settings.set_last_session(selected_files, quick_notes, editor_file)
                
        # Save settings before exiting
        self._save_window_position()
        settings.save_settings()
        
        super().quit()

    def copy_output_to_clipboard(self):
        """Copy the current content of the master file to clipboard."""
        if not os.path.exists(self.master_filename):
            self.log(f"Output file does not exist: {self.master_filename}")
            self.status_label.config(text="No output file exists yet. Run concatenation first.")
            return
            
        try:
            # Load the content from the master file
            content = file_io_utils.load_file(self.master_filename, self.log)
            if content:
                # Copy to clipboard
                self.clipboard_clear()
                self.clipboard_append(content)
                self.log(f"Copied output content to clipboard from: {self.master_filename}")
                
                # Visual feedback in status bar
                self.status_label.config(text="✅ Output content copied to clipboard!")
                self.status_bar.config(background="#90EE90")  # Light green background
                
                # Reset status bar color after 2 seconds
                self.after(2000, self._reset_status_bar_color)
            else:
                self.status_label.config(text="Output file is empty")
        except Exception as e:
            self.log(f"Error copying output to clipboard: {e}")
            self.status_label.config(text=f"Error copying to clipboard: {e}")

    def load_directory(self):
        """Open dialog to select and load a directory."""
        initial_dir = settings.get_last_directory() or os.path.expanduser("~")
        dir_selected = filedialog.askdirectory(title="Select Directory", initialdir=initial_dir)
        if not dir_selected:
            return None

        # Save the selected directory in settings
        settings.set_last_directory(dir_selected)
        settings.save_settings()
        
        # Use the modified load_directory method from file_tree_manager
        self.file_tree_manager.load_directory(dir_selected)

    def show_settings_dialog(self):
        """Show the settings dialog."""
        SettingsDialog(self)
        
        # After dialog closes, update the output file if it changed
        output_settings = settings.get_output_settings()
        self.master_filename = os.path.join(OUTPUT_DIR, output_settings["filename"])
        
        # Apply editor theme if it changed
        if hasattr(self, 'editor_manager'):
            theme = settings.get_editor_theme()
            self.editor_manager.set_theme(theme)

    def _check_context_sync(self, event=None):
        """Check if the current state matches the loaded context."""
        if not self.loaded_context_state:  # No context loaded or just saved
            self.is_context_synced = True
            self._update_save_context_button_style(is_synced=True)
            return

        current_files = sorted(list(self.listbox_files.get(0, END)))
        
        # Handle placeholder text in notes comparison
        current_notes = self.notes_text.get("1.0", END).strip()
        if self.notes_placeholder_shown:
            current_notes = ""

        files_match = current_files == self.loaded_context_state['files']
        notes_match = current_notes == self.loaded_context_state['notes']

        self.is_context_synced = files_match and notes_match
        self._update_save_context_button_style(is_synced=self.is_context_synced)

    def _update_save_context_button_style(self, is_synced):
        """Update the visual style of the Save Context button."""
        if is_synced:
            self.save_btn.config(text="💾 Save Snapshot")
            # Reset any special style if you added one
        else:
            self.save_btn.config(text="💾* Save Snapshot")  # Add asterisk
            # Optionally apply a style: self.save_btn.config(style="Unsaved.TButton")

    def _on_notes_modified(self, event=None):
        """Handle modifications to the notes text area."""
        # Debounce check to avoid excessive calls
        self.after_cancel(self._notes_modified_timer) if hasattr(self, '_notes_modified_timer') else None
        self._notes_modified_timer = self.after(500, self._check_context_sync)
        # Reset the Text widget's internal modified flag
        self.notes_text.edit_modified(False)
