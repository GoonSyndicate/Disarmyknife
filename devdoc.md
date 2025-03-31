# Disarmyknife: File Concatenation Utility

**Disarmyknife** is an IDE‑like tool that bundles several utilities into a single application. One of its core features is a **file concatenation utility** with a modern, responsive Tkinter‑based GUI. This utility enables users to select files from their file system, preview and manage those selections, and then merge them into a single configurable output file.

---

## Primary Objectives

1. **Directory Loading and File Exploration:**
   - Allow users to load a directory and display its contents in a tree‑view file explorer.
   - Categorize files using icons and provide a legend for quick identification (e.g., Python files, JavaScript files, etc.).

2. **File Selection and Preview:**
   - Enable selection of multiple files either via the treeview or a file dialog.
   - Provide a preview panel that shows the first few lines of a selected file, with support for syntax highlighting.

3. **File Management:**
   - Manage a list of selected files using a listbox, with options to add, remove, or clear files.
   - Use context menus (via right‑click) to quickly toggle file inclusion, preview files, open files in the default editor, or display file properties.
   - Reorder files with drag-and-drop support and up/down buttons.

4. **File Concatenation Process:**
   - Concatenate the selected files into a master file.
   - Before concatenation, create a timestamped backup of any existing master file.
   - Write a header into the master file that lists the directory structure (i.e., the selected file paths).
   - Append each file's content to the master file with a header indicating its source.
   - Configurable header formats and optional line numbering.

5. **User Feedback and Logging:**
   - Display log messages (with timestamps) for all operations and errors in a dedicated log panel.
   - Provide a status bar and progress bar to inform the user of the current operation status and progress during long‑running tasks.

6. **Context Management:**
   - Save collections of files with notes as named contexts
   - Switch between different working contexts
   - Export contexts to JSON or Markdown formats
   - Import contexts from JSON files

7. **Advanced Editing:**
   - Built-in syntax-highlighting editor
   - Multiple theming options
   - Find and replace functionality
   - Line numbering

8. **Search and Filter:**
   - Search by filename, content, or extension
   - Highlight matching results
   - Real-time filtering

9. **Settings Management:**
   - Configure output formatting
   - Set application preferences
   - Persistent window positioning and sizing

---

## Directory Structure

```
Disarmyknife/
├── app_config.py
├── config.json
├── context_manager.py
├── editor_manager.py
├── file_io_utils.py
├── file_tree_manager.py
├── gui_components.py
├── main.py
├── search_handler.py
├── settings_dialog.py
├── settings_manager.py
├── theme_config.py
└── token_utils.py
```

### **app_config.py**
- **Purpose:** Defines application paths and loads initial configuration.
- **Features:**
  - Sets up base directories for application data
  - Configures output and backup directories
  - Loads settings for output filename from settings_manager

### **config.json**
- **Purpose:** Stores user-specific application settings persisted across sessions.
- **Features:**
  - Window size and position
  - Last used directory
  - Output formatting preferences
  - Editor theme settings
  - Token encoding selection

### **context_manager.py**
- **Purpose:** Manages working contexts for the application.
- **Features:**
  - Save and load named contexts (groups of files with notes)
  - Export contexts to JSON or Markdown format
  - Import contexts from JSON
  - Track context metadata

### **editor_manager.py**
- **Purpose:** Provides rich text editing functionality.
- **Features:**
  - Syntax highlighting for various languages
  - Line numbering
  - Find and replace with regex support
  - Multiple theme options
  - File loading and saving

### **file_io_utils.py**
- **Purpose:** Provides file input/output utility functions.
- **Features:**
  - Create backups of master files
  - Load file contents with error handling
  - Append content to the master file with formatted headers
  - Write directory structure information

### **file_tree_manager.py**
- **Purpose:** Manages the file explorer tree view component.
- **Features:**
  - Directory browsing with lazy loading
  - File type visualization with icons
  - Selection handling and marking
  - Triple-click to select all files in a directory

### **gui_components.py**
- **Purpose:** Contains the primary GUI application class.
- **Features:**
  - Main application window and layout
  - Integration of all component managers
  - Drag and drop support
  - Token counting for LLM context limits
  - Focus mode for distraction-free work

### **main.py**
- **Purpose:** Serves as the entry point for the application.
- **Functionality:**  
  - Instantiates the FileConcatenatorApp
  - Starts the Tkinter main loop

### **search_handler.py**
- **Purpose:** Provides file search functionality.
- **Features:**
  - Filename search
  - Content search (first 1KB)
  - Extension filtering
  - Real-time result highlighting

### **settings_dialog.py**
- **Purpose:** Provides a dialog for configuring application settings.
- **Features:**
  - Output formatting options
  - Editor preferences
  - Window settings
  - Directory management

### **settings_manager.py**
- **Purpose:** Manages application settings persistence.
- **Features:**
  - Load settings from JSON file
  - Save settings to JSON file
  - Provide defaults for missing settings
  - Access settings throughout application

### **theme_config.py**
- **Purpose:** Configures the visual theme for the application.
- **Features:**
  - Custom fonts for text and headings
  - Modern color scheme with accent colors
  - Consistent widget styling
  - Status bar and progress bar theming

### **token_utils.py**
- **Purpose:** Provides token counting for LLM context limits.
- **Features:**
  - Estimate token counts using tiktoken
  - Format token counts for display
  - Track model context limits
  - Multiple encoding support

---

## Component Interactions

The application follows a modular design with dedicated manager classes:

1. **FileConcatenatorApp** (in gui_components.py) serves as the main orchestrator:
   - Creates and arranges the UI layout
   - Initializes component managers
   - Handles high-level application flow

2. **Component Managers** provide encapsulated functionality:
   - **FileTreeManager**: Handles file system exploration
   - **EditorManager**: Provides code editing capabilities
   - **ContextManager**: Manages working contexts
   - **SearchHandler**: Handles file searching and filtering
   - **SettingsManager**: Manages application preferences

3. **Utility Modules** provide shared functionality:
   - **file_io_utils.py**: Core file operations
   - **token_utils.py**: Token counting for LLM integration
   - **theme_config.py**: Consistent visual styling

4. **Configuration**:
   - **app_config.py**: Application constants
   - **config.json**: User preferences
   - **settings_manager.py**: Settings access layer

---

## Workflow Overview

1. **Application Startup**:
   - Load saved settings
   - Initialize component managers
   - Set up the GUI layout
   - Apply the visual theme

2. **Loading Files**:
   - Navigate file system via tree view
   - Select files through:
     - Double-clicking files in the tree
     - Using the Add Files button
     - Dragging and dropping files
     - Triple-clicking folders to select all files
     - Loading a saved context

3. **Working with Files**:
   - Preview selected files in the editor
   - Reorder files in the selection list
   - Edit files in the built-in editor
   - Track token counts for LLM context limits

4. **Context Management**:
   - Save selected files and notes as a named context
   - Switch between different contexts
   - Export contexts for sharing
   - Import contexts from other users

5. **Concatenation Process**:
   - Create backup of existing master file
   - Write directory structure header
   - Append each file with configurable headers
   - Copy result to clipboard
   - Display progress in status bar

6. **Settings Configuration**:
   - Adjust output formatting options
   - Set editor preferences
   - Configure window behavior
   - Manage directory defaults

---

## Features in Detail

### 1. File Selection and Management

The application provides multiple ways to select files:
- File explorer tree with directory navigation
- Add Files button to select files via dialog
- Drag and drop from external file manager
- Triple-click folders to select all contained files

Selected files can be:
- Reordered using up/down buttons
- Removed individually or cleared all at once
- Saved as part of a context
- Previewed in the editor

### 2. Context Management

Contexts allow users to save and restore working environments:

- **Save Context**: Store current file selection with notes
- **Load Context**: Restore previously saved file selections
- **Export Context**: Share contexts via JSON or Markdown
- **Import Context**: Use contexts created by others

Contexts help users:
- Organize related files for different projects
- Save notes about the purpose of file groupings
- Share file groupings with teammates or LLMs

### 3. Advanced Editor

The built-in editor provides:

- **Syntax Highlighting**: For multiple languages
- **Theme Selection**: Multiple color schemes available
- **Find and Replace**: With regex support
- **Line Numbers**: For easy reference

Editor state is tracked to:
- Prompt to save changes
- Show modified status
- Revert to saved versions

### 4. Search Capabilities

The search functionality includes:
- **Filename Search**: Find files by name
- **Content Search**: Search within file content
- **Extension Search**: Filter by file type
- **Real-time Results**: Highlight matches as you type

### 5. Token Counting

For integration with LLMs, the application:
- Counts tokens in selected files
- Shows percentage of context window used
- Supports multiple model context sizes
- Provides visual feedback on token usage
- Allows configuring the token encoding via Settings dialog

### 6. Output Customization

The concatenated output can be customized:
- **Header Format**: Choose from several header styles
- **Line Numbering**: Optionally add line numbers
- **Output File**: Configure output filename
- **Automatic Backup**: Create timestamped backups

---

## GUI Components Architecture

The `FileConcatenatorApp` class in `gui_components.py` follows a composite pattern, where the main application window integrates various specialized manager components:

1. **Initialization Flow**:
   - Initialize core application state and window
   - Create and initialize component managers
   - Build GUI layout using specialized panels
   - Configure event handlers and bindings
   - Set up the theme and styling

2. **Panel Organization**:
   - **Left Panel**: File exploration and preview
     - Tree view with file system navigation
     - Preview/editor area for file content
     - Search controls for filtering files
   - **Right Panel**: Selected files and operations
     - Selected files list with reordering controls
     - Action buttons for core operations
     - Quick notes input area
     - Context management controls
     - Log panel for operation feedback

3. **Cross-Component Communication**:
   - Event-driven updates between components
   - Callback functions for status updates
   - Cross-component state synchronization (e.g., selected files)

---

## Error Handling Strategy

The application implements a consistent error handling approach:

1. **Try/Except Blocks**:
   - All file operations are wrapped in `try/except` blocks
   - Settings loading and saving are wrapped in `try/except` blocks
   - UI updates that might fail are wrapped in `try/except` blocks

2. **Informative Error Messages**:
   - Specific exceptions are caught and produce informative error messages
   - Error messages are displayed via messagebox dialogs for critical errors
   - Errors are logged to the log panel for all errors

3. **Resilience**:
   - The application attempts to default to default settings when configuration is invalid
   - The application handles missing dependencies gracefully, especially when optional components (like tiktoken) are missing
   - The application remains stable even when encountering unexpected conditions while providing appropriate feedback to the user.

---

## Search System Integration

The `SearchHandler` component provides a flexible search system that tightly integrates with the file tree view:

1. **Search Input**:
   - Search text input for entering search terms
   - Search type selection (name, content, extension)

2. **Real-time Filtering**:
   - Real-time filtering triggers on text changes
   - Matching items are highlighted with a 'match' tag

3. **Search Logic**:
   - **Name search**: Filters by filename using simple string matching
   - **Content search**: Reads the first 1KB of each file to find matches
   - **Extension search**: Filters by file extension

---

## Focus Mode Feature

The application includes a "Focus Mode" feature that hides the file explorer panel to provide a distraction-free environment for working with selected files. This can be toggled via a checkbox in the status bar.

1. **UI Simplification**:
   - The file explorer panel is hidden
   - The main window adapts to a more compact view

2. **Workflow**:
   - Focus mode allows users to concentrate on the file list and editor
   - Users can quickly toggle focus mode when working with the editor or reviewing the selected files without needing to browse for additional files.

---

## Automated Testing

For future development, the following automated testing approaches could be implemented:

1. **Unit Tests**:
   - Testing utility functions in isolation
   - Mocking file system operations
   - Testing settings management

2. **Integration Tests**:
   - Testing manager components with dependencies
   - Verifying cross-component communication

3. **UI Testing**:
   - Testing UI element behavior
   - Verifying cross-component state synchronization (e.g., selected files)
   - Testing user workflows

---

## Model-View-Controller (MVC)

The application architecture loosely follows the Model-View-Controller (MVC) design pattern:

1. **Components**:
   - **Model**: Settings, contexts, and file data
   - **View**: GUI components and themed widgets
   - **Controller**: Manager classes that mediate between models and views

2. **Responsibilities**:
   - **Model**: Manages data and business logic
   - **View**: Displays data and handles user input
   - **Controller**: Updates the model based on user input and updates the view when the model changes

This architecture provides good separation of concerns while maintaining necessary interaction between components.

---

## Known Issues and Future Enhancements

### Known Issues
- Large files may cause performance issues in the editor
- Token counting may be slow for very large file selections
- Limited undo/redo support in certain operations

### Future Enhancements
- **Virtual Environment Support**: Detect and use project virtual environments
- **Git Integration**: Show file status and commit history
- **Split View Editing**: Compare files side by side
- **Custom Plugins**: Allow user-defined extensions
- **Improved Search**: Add fuzzy search and replace-all functionality
- **File Grouping**: Group files by type or directory
- **Export Formats**: Add more export formats (PDF, HTML)
- **Settings Dialog**: Add the ability to change encodings in the settings dialog.

---

## Conclusion

Disarmyknife's file concatenation utility is a powerful, modular tool designed to help users efficiently manage and merge multiple files. With its modern interface, advanced editing capabilities, context management, and customization options, it provides a comprehensive solution for working with collections of files.

The application's modular design allows for easy maintenance and extension, while the comprehensive documentation ensures that developers can quickly understand and modify the codebase as needed.
