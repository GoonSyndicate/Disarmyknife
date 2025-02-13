import tkinter as tk
from tkinter import ttk
from tkinter.font import Font

class ThemeConfig:
    @staticmethod
    def setup_theme():
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
