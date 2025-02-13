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
        
        # Colors
        colors = {
            'bg': '#ffffff',
            'fg': '#333333',
            'selected': '#0078d7',
            'hover': '#e5f3ff',
            'accent': '#0078d7',
            'border': '#cccccc'
        }

        # Common widget styles
        style.configure(".",
            font=default_font,
            background=colors['bg'],
            foreground=colors['fg'])

        style.configure("Treeview",
            background=colors['bg'],
            fieldbackground=colors['bg'],
            borderwidth=1,
            relief="solid")
        
        style.configure("Treeview.Heading",
            font=heading_font,
            background=colors['bg'],
            relief="solid",
            borderwidth=1)

        style.map("Treeview",
            background=[("selected", colors['selected'])],
            foreground=[("selected", colors['bg'])])

        # Custom styles
        style.configure("Header.TLabel",
            font=heading_font,
            padding=5)

        style.configure("StatusBar.TFrame",
            background=colors['border'],
            relief="sunken")

        style.configure("StatusBar.TLabel",
            background=colors['border'],
            padding=3)

        return style, colors
