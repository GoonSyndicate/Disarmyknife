# Disarmyknife: File Concatenation Utility

**Disarmyknife** is an IDE‑like tool that bundles several utilities into a single application. One of its core features is a **file concatenation utility** with a modern, responsive Tkinter‑based GUI. This utility enables users to select files from their file system, preview and manage those selections, and then merge them into a single master document (`master.txt`).

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

4. **File Concatenation Process:**
   - Concatenate the selected files into `master.txt`.
   - Before concatenation, create a timestamped backup of any existing `master.txt`.
   - Write a header into `master.txt` that lists the directory structure (i.e., the selected file paths).
   - Append each file's content to the master file with a header indicating its source.

5. **User Feedback and Logging:**
   - Display log messages (with timestamps) for all operations and errors in a dedicated log panel.
   - Provide a status bar and progress bar to inform the user of the current operation status and progress during long‑running tasks.

---

## Directory Structure

```
Disarmyknife/
├── theme_config.py
├── gui_components.py
├── main.py
├── file_io_utils.py
└── concat_files.py
```

### **theme_config.py**
- **Purpose:** Sets up a modern Tkinter theme.
- **Features:**
  - Creates a custom “modern” theme using the `clam` base.
  - Configures fonts (default and headings) and colors for backgrounds, foregrounds, selection, and borders.
  - Defines common widget styles (buttons, labels, treeviews, status bars) for a consistent UI look.

### **gui_components.py**
- **Purpose:** Contains the primary GUI application class for the file concatenation utility.
- **Features:**
  - **File Explorer Panel:**  
    - Displays directories and files using a `ttk.Treeview`.
    - Includes a legend for file type indicators.
    - Supports double‑click and right‑click (context menu) to toggle file inclusion.
  - **Preview Panel:**  
    - Uses a `tk.Text` widget (with scrollbars) to display file previews.
    - Integrates optional syntax highlighting using Pygments.
  - **Selected Files List:**  
    - Manages selected files in a `tk.Listbox`.
  - **Buttons Panel:**  
    - Offers buttons to add files, remove selected files, clear the list, exit, and start concatenation.
  - **Log Panel:**  
    - Displays timestamped log messages in a scrolled text widget.
  - **Status Bar and Progress Bar:**  
    - Shows current status messages and progress of operations.

### **main.py**
- **Purpose:** Serves as the entry point for the application.
- **Functionality:**  
  - Imports `FileConcatenatorApp` from `gui_components.py`.
  - Instantiates the application and starts the Tkinter main loop.

### **file_io_utils.py**
- **Purpose:** Provides file input/output utility functions.
- **Features:**
  - **create_backup:** Creates a timestamped backup of an existing `master.txt`.
  - **load_file:** Reads and returns the content of a given file.
  - **append_to_master:** Appends file content to `master.txt`, prefixed with a header.
  - **write_directory_structure:** Writes the list of selected file paths as a header in `master.txt`.
  - Handles and logs errors for all file operations.

### **concat_files.py**
- **Purpose:** Offers a standalone script version of the file concatenation utility.
- **Features:**
  - Similar functionality and GUI as in `gui_components.py`.
  - Can be executed directly to run the file concatenation process.
  - Provides the same modern styling, file explorer, preview, file management, logging, and concatenation process.

---

## Workflow Overview

1. **Loading a Directory:**
   - The user selects a directory via a file dialog.
   - The application populates the treeview with the directory’s contents, allowing the user to explore subdirectories.

2. **Selecting and Previewing Files:**
   - Files can be added to the selection list by double‑clicking or using the context menu on the treeview.
   - The preview panel shows the first ten lines of the selected file, with syntax highlighting applied if applicable.

3. **Managing Selected Files:**
   - The listbox holds the files chosen for concatenation.
   - Users can remove files or clear the entire selection as needed.

4. **Concatenation Process:**
   - Upon confirming concatenation, a backup of `master.txt` is created (if it exists).
   - The master file is cleared and then rebuilt by:
     - Writing a header containing the selected file paths.
     - Appending each file’s content with a header indicating its source.
   - The process runs on a separate thread to keep the GUI responsive.
   - Progress and status updates are shown in the status bar and progress bar, and all operations are logged.

---

## Documentation Strategy

The codebase follows literate programming principles to maintain clarity and maintainability:

### Documentation Levels

1. **Module Level**
   - Comprehensive module docstrings explaining purpose and features
   - Import organization and rationale
   - Module-level constants and configurations

2. **Class Level**
   - Detailed class docstrings with:
     - Purpose and responsibilities
     - Key features
     - Attribute descriptions
     - Usage patterns

3. **Method Level**
   - Function/method docstrings including:
     - Purpose and behavior
     - Arguments and return values
     - Error conditions
     - Usage examples where needed

4. **Inline Documentation**
   - Strategic comments explaining complex logic
   - State management annotations
   - Performance considerations
   - Error handling rationale

### Documentation Principles

1. **Clarity First**
   - Clear, concise language
   - Consistent terminology
   - Logical organization

2. **Context Preservation**
   - Links between related components
   - Workflow descriptions
   - State management explanations

3. **Maintainability Focus**
   - Update instructions
   - Dependency documentation
   - Configuration guidelines

4. **User-Centric Approach**
   - Feature descriptions from user perspective
   - Error message explanations
   - Troubleshooting guides

## Development Workflow

### Adding New Features

1. **Documentation First**
   - Add feature description to devdoc.md
   - Define API and interfaces
   - Document expected behavior

2. **Implementation**
   - Follow documented design
   - Add inline documentation
   - Update module/class docs

3. **Testing**
   - Document test cases
   - Add usage examples
   - Update troubleshooting guides

### Maintaining Code

1. **Documentation Review**
   - Keep docs in sync with code
   - Update examples
   - Refresh screenshots/diagrams

2. **Code Updates**
   - Follow documented patterns
   - Maintain consistent style
   - Update docs with changes

3. **Quality Assurance**
   - Validate documentation accuracy
   - Test documented features
   - Update known issues

---

## Conclusion

Disarmyknife’s file concatenation utility is a powerful, modular tool designed to help users efficiently merge multiple files into a single document. With its modern, responsive interface and robust logging and status feedback, the application is well‑suited for both casual and professional use. The code is organized into separate modules for theme configuration, GUI components, file I/O operations, and main execution, ensuring maintainability and scalability for future enhancements.
