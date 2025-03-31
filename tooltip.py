"""
Simple tooltip implementation for tkinter widgets.
"""

import tkinter as tk

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
