"""
ThemeConfig: Modern theme configuration for the File Concatenator GUI.

This module defines a consistent visual style for the application using ttk styles.
It creates a custom theme based on 'clam' with modern colors and fonts.

The theme includes:
- Custom fonts for regular text and headings
- Modern color scheme with accent colors
- Styled widgets (buttons, labels, treeview)
- Status bar styling
"""

import tkinter as tk
from tkinter import ttk
from tkinter.font import Font

class ThemeConfig:
    """
    Static configuration class for application theming.
    
    Provides a single point of control for the application's visual appearance,
    ensuring consistency across all widgets and windows.
    """
    
    @staticmethod
    def setup_theme():
        """
        Configure and apply the application's custom theme.
        
        Returns:
            tuple: (ttk.Style, dict) The configured style object and color scheme
            
        The color scheme includes:
        - bg: Background color
        - fg: Foreground (text) color
        - selected: Selection highlight color
        - hover: Hover state color
        - accent: Accent color for emphasis
        - border: Border and separator color
        """
        style = ttk.Style()
        
        # Configure main theme
        style.theme_create("modern", parent="clam")
        style.theme_use("modern")

        # Fonts
        default_font = Font(family="Segoe UI", size=10)
        heading_font = Font(family="Segoe UI", size=11, weight="bold")
        
        # Colors - refined for better visual appeal
        colors = {
            'bg': '#f8f8f8',           # Slightly off-white for less eye strain
            'fg': '#333333',           # Dark gray text
            'selected': '#0078d7',     # Bright blue selection
            'hover': '#e5f3ff',        # Light blue hover state
            'accent': '#0078d7',       # Accent color matching selection
            'border': '#dddddd'        # Lighter gray for borders
        }

        # Common widget styles with improved padding
        style.configure(".",
            font=default_font,
            background=colors['bg'],
            foreground=colors['fg'])

        # Configure button with padding and hover effects
        style.configure("TButton",
            padding=5)
        style.map("TButton",
            background=[('active', colors['hover']), ('pressed', colors['selected'])],
            foreground=[('pressed', '#ffffff')])
            
        # Configure label with better padding
        style.configure("TLabel", 
            padding=(3, 5))

        style.configure("Treeview",
            background=colors['bg'],
            fieldbackground=colors['bg'],
            borderwidth=1,
            relief="solid")
        
        style.configure("Treeview.Heading",
            font=heading_font,
            background=colors['bg'],
            relief="solid",
            borderwidth=1,
            padding=3)

        style.map("Treeview",
            background=[("selected", colors['selected'])],
            foreground=[("selected", '#ffffff')])

        # Custom styles
        style.configure("Header.TLabel",
            font=heading_font,
            padding=5)

        # Frame styles
        style.configure("TFrame",
            background=colors['bg'])
        style.configure("TLabelframe",
            background=colors['bg'])
        style.configure("TLabelframe.Label",
            background=colors['bg'],
            foreground=colors['fg'],
            padding=(5, 2))

        # StatusBar styles
        style.configure("StatusBar.TFrame",
            background=colors['border'],
            relief="sunken")

        style.configure("StatusBar.TLabel",
            background=colors['border'],
            padding=3)

        # PanedWindow styles
        style.configure("TPanedwindow",
            background=colors['border'])

        return style, colors
