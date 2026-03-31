"""
Theme Manager for Horizon Password Generator GUI

Supports Dark and Light themes with modern styling.
"""

from pwd_generator.gui import (
    QColor, QPalette, QFont, QBrush, QPen, 
    Qt, QApplication
)
from typing import Dict, Any
import json
from pathlib import Path


class ThemeColors:
    """Color definitions for themes."""
    
    DARK = {
        # Background colors
        "background_primary": "#1e1e2e",
        "background_secondary": "#2d2d3d",
        "background_tertiary": "#3d3d4d",
        "background_input": "#2d2d3d",
        
        # Text colors
        "text_primary": "#e0e0e0",
        "text_secondary": "#a0a0a0",
        "text_disabled": "#606060",
        "text_link": "#7aa2f7",
        
        # Accent colors
        "accent_primary": "#7aa2f7",
        "accent_secondary": "#9ece6a",
        "accent_warning": "#e0af68",
        "accent_danger": "#f7768e",
        "accent_success": "#9ece6a",
        
        # Strength meter colors
        "strength_weak": "#f7768e",
        "strength_fair": "#e0af68",
        "strength_good": "#7dcfff",
        "strength_strong": "#9ece6a",
        "strength_very_strong": "#73daca",
        
        # Border colors
        "border_primary": "#3d3d4d",
        "border_focus": "#7aa2f7",
        "border_hover": "#5d5d6d",
        
        # Selection
        "selection_bg": "#7aa2f7",
        "selection_text": "#1e1e2e",
        
        # Scrollbar
        "scrollbar_bg": "#2d2d3d",
        "scrollbar_handle": "#4d4d5d",
        
        # Button
        "button_bg": "#3d3d4d",
        "button_hover": "#4d4d5d",
        "button_pressed": "#5d5d6d",
        "button_text": "#e0e0e0",
        
        # Table/List
        "table_header_bg": "#2d2d3d",
        "table_header_text": "#e0e0e0",
        "table_row_alt": "#252535",
        # Row highlight when selected (distinct from neutral greys)
        "table_row_selected": "#2a4a7a",
        "table_row_selected_text": "#e8eef8",
    }
    
    LIGHT = {
        # Background colors
        "background_primary": "#fafafa",
        "background_secondary": "#ffffff",
        "background_tertiary": "#f0f0f0",
        "background_input": "#ffffff",
        
        # Text colors
        "text_primary": "#1a1a2e",
        "text_secondary": "#4a4a5a",
        "text_disabled": "#a0a0a0",
        "text_link": "#3a6ea5",
        
        # Accent colors
        "accent_primary": "#3a6ea5",
        "accent_secondary": "#4caf50",
        "accent_warning": "#ff9800",
        "accent_danger": "#f44336",
        "accent_success": "#4caf50",
        
        # Strength meter colors
        "strength_weak": "#f44336",
        "strength_fair": "#ff9800",
        "strength_good": "#2196f3",
        "strength_strong": "#4caf50",
        "strength_very_strong": "#00bcd4",
        
        # Border colors
        "border_primary": "#e0e0e0",
        "border_focus": "#3a6ea5",
        "border_hover": "#c0c0c0",
        
        # Selection
        "selection_bg": "#3a6ea5",
        "selection_text": "#ffffff",
        
        # Scrollbar
        "scrollbar_bg": "#f0f0f0",
        "scrollbar_handle": "#c0c0c0",
        
        # Button
        "button_bg": "#e0e0e0",
        "button_hover": "#d0d0d0",
        "button_pressed": "#c0c0c0",
        "button_text": "#1a1a2e",
        
        # Table/List
        "table_header_bg": "#f0f0f0",
        "table_header_text": "#1a1a2e",
        "table_row_alt": "#fafafa",
        "table_row_selected": "#b6d4f2",
        "table_row_selected_text": "#14233d",
    }


class ThemeManager:
    """Manages application theme."""
    
    _instance = None
    _current_theme = "dark"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._colors = ThemeColors.DARK if self._current_theme == "dark" else ThemeColors.LIGHT
    
    @classmethod
    def get_instance(cls):
        return cls()
    
    @property
    def current_theme(self) -> str:
        return self._current_theme
    
    @property
    def colors(self) -> Dict[str, str]:
        return self._colors
    
    def set_theme(self, theme_name: str) -> None:
        """Set the application theme."""
        theme_name = theme_name.lower()
        if theme_name not in ("dark", "light"):
            raise ValueError(f"Unknown theme: {theme_name}")
        
        self._current_theme = theme_name
        self._colors = ThemeColors.DARK if theme_name == "dark" else ThemeColors.LIGHT
    
    def toggle_theme(self) -> str:
        """Toggle between dark and light theme."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme
    
    def get_color(self, name: str) -> str:
        """Get a color value by name."""
        return self._colors.get(name, "#000000")
    
    def get_style_sheet(self) -> str:
        """Generate the complete application stylesheet."""
        c = self._colors
        
        return f"""
            /* Global Styles */
            QWidget {{
                font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
            }}
            
            QMainWindow, QDialog {{
                background-color: {c['background_primary']};
                color: {c['text_primary']};
            }}
            
            /* Labels */
            QLabel {{
                color: {c['text_primary']};
                background-color: transparent;
            }}
            
            QLabel:disabled {{
                color: {c['text_disabled']};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {c['button_bg']};
                color: {c['button_text']};
                border: 1px solid {c['border_primary']};
                border-radius: 8px;
                padding: 10px 16px;
                min-height: 36px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {c['button_hover']};
                border-color: {c['border_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {c['button_pressed']};
            }}
            
            QPushButton:disabled {{
                background-color: {c['background_tertiary']};
                color: {c['text_disabled']};
            }}
            
            QPushButton#primaryButton {{
                background-color: {c['accent_primary']};
                color: #ffffff;
                border: none;
                font-weight: 600;
            }}
            
            QPushButton#primaryButton:hover {{
                background-color: {c['text_link']};
                color: #ffffff;
            }}
            
            QPushButton#dangerButton {{
                background-color: {c['accent_danger']};
                color: #ffffff;
                border: none;
                font-weight: 600;
            }}
            
            QPushButton#dangerButton:hover {{
                color: #ffffff;
                border: 1px solid {c['border_focus']};
                background-color: {c['accent_danger']};
            }}
            
            QPushButton#successButton {{
                background-color: {c['accent_success']};
                color: #ffffff;
                border: none;
                font-weight: 600;
            }}
            
            QPushButton#navButton {{
                text-align: center;
                min-height: 40px;
                padding: 10px 12px;
                font-weight: 500;
                background-color: transparent;
                color: {c['text_primary']};
                border: 1px solid transparent;
                border-radius: 8px;
            }}
            
            QPushButton#navButton:hover {{
                background-color: {c['background_tertiary']};
                border-color: {c['border_primary']};
            }}
            
            QPushButton#navButton:checked {{
                background-color: {c['accent_primary']};
                color: #ffffff;
                border-color: {c['accent_primary']};
                font-weight: 600;
            }}
            
            QPushButton#navButton:checked:hover {{
                background-color: {c['text_link']};
                border-color: {c['text_link']};
                color: #ffffff;
            }}
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {c['background_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {c['selection_bg']};
                selection-color: {c['selection_text']};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {c['border_focus']};
            }}
            
            QLineEdit:disabled, QTextEdit:disabled {{
                background-color: {c['background_tertiary']};
                color: {c['text_disabled']};
            }}
            
            QLineEdit#passwordField {{
                font-family: 'Courier New', monospace;
                font-size: 14px;
            }}
            
            /* ComboBox */
            QComboBox {{
                background-color: {c['background_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                border-radius: 6px;
                padding: 8px;
                min-height: 20px;
            }}
            
            QComboBox:hover {{
                border-color: {c['border_hover']};
            }}
            
            QComboBox:focus {{
                border-color: {c['border_focus']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {c['text_primary']};
                margin-right: 10px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {c['background_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                selection-background-color: {c['accent_primary']};
                selection-color: white;
            }}
            
            /* SpinBox */
            QSpinBox, QDoubleSpinBox {{
                background-color: {c['background_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                border-radius: 6px;
                padding: 8px;
            }}
            
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {c['border_focus']};
            }}
            
            /* CheckBox */
            QCheckBox {{
                color: {c['text_primary']};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {c['border_primary']};
                border-radius: 4px;
                background-color: {c['background_input']};
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {c['border_hover']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {c['accent_primary']};
                border-color: {c['accent_primary']};
            }}
            
            /* RadioButton */
            QRadioButton {{
                color: {c['text_primary']};
                spacing: 8px;
            }}
            
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {c['border_primary']};
                border-radius: 9px;
                background-color: {c['background_input']};
            }}
            
            QRadioButton::indicator:hover {{
                border-color: {c['border_hover']};
            }}
            
            QRadioButton::indicator:checked {{
                background-color: {c['accent_primary']};
                border-color: {c['accent_primary']};
            }}
            
            /* GroupBox */
            QGroupBox {{
                color: {c['text_primary']};
                font-weight: bold;
                border: 1px solid {c['border_primary']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            
            /* TabWidget */
            QTabWidget::pane {{
                border: 1px solid {c['border_primary']};
                border-radius: 8px;
                background-color: {c['background_secondary']};
            }}
            
            QTabBar::tab {{
                background-color: {c['background_tertiary']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {c['background_secondary']};
                border-bottom: 1px solid {c['background_secondary']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {c['background_primary']};
            }}
            
            /* ScrollBar */
            QScrollBar:vertical {{
                background-color: {c['scrollbar_bg']};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {c['scrollbar_handle']};
                border-radius: 6px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {c['border_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {c['scrollbar_bg']};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {c['scrollbar_handle']};
                border-radius: 6px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {c['border_hover']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            /* TableWidget */
            QTableWidget {{
                background-color: {c['background_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                border-radius: 8px;
                gridline-color: {c['border_primary']};
            }}
            
            QTableWidget::item {{
                padding: 8px;
            }}
            
            QTableWidget::item:selected {{
                background-color: {c['table_row_selected']};
                color: {c['table_row_selected_text']};
            }}
            
            QTableWidget::item:selected:active {{
                background-color: {c['table_row_selected']};
                color: {c['table_row_selected_text']};
            }}
            
            QHeaderView::section {{
                background-color: {c['table_header_bg']};
                color: {c['table_header_text']};
                border: none;
                border-bottom: 1px solid {c['border_primary']};
                padding: 8px;
                font-weight: bold;
            }}
            
            /* ProgressBar */
            QProgressBar {{
                background-color: {c['background_tertiary']};
                border: none;
                border-radius: 4px;
                text-align: center;
                color: {c['text_primary']};
            }}
            
            QProgressBar::chunk {{
                border-radius: 4px;
            }}
            
            /* Slider */
            QSlider::groove:horizontal {{
                background-color: {c['background_tertiary']};
                height: 6px;
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background-color: {c['accent_primary']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background-color: {c['accent_primary']};
            }}
            
            /* ScrollArea */
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
            
            /* Frame */
            QFrame {{
                background-color: transparent;
            }}
            
            QFrame#cardFrame {{
                background-color: {c['background_secondary']};
                border: 1px solid {c['border_primary']};
                border-radius: 8px;
            }}
            
            /* Menu */
            QMenuBar {{
                background-color: {c['background_secondary']};
                color: {c['text_primary']};
                border-bottom: 1px solid {c['border_primary']};
            }}
            
            QMenuBar::item {{
                padding: 8px 12px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {c['accent_primary']};
            }}
            
            QMenu {{
                background-color: {c['background_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
            }}
            
            QMenu::item {{
                padding: 8px 24px;
            }}
            
            QMenu::item:selected {{
                background-color: {c['accent_primary']};
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: {c['border_primary']};
                margin: 4px 8px;
            }}
            
            /* StatusBar */
            QStatusBar {{
                background-color: {c['background_secondary']};
                color: {c['text_secondary']};
                border-top: 1px solid {c['border_primary']};
            }}
            
            /* ToolTip */
            QToolTip {{
                background-color: {c['background_tertiary']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                border-radius: 4px;
                padding: 4px;
            }}
            
            /* Splitter */
            QSplitter::handle {{
                background-color: {c['border_primary']};
            }}
            
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            
            QSplitter::handle:vertical {{
                height: 1px;
            }}
            
            /* ListWidget */
            QListWidget {{
                background-color: {c['background_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                border-radius: 8px;
            }}
            
            QListWidget::item {{
                padding: 8px;
            }}
            
            QListWidget::item:selected {{
                background-color: {c['accent_primary']};
                color: white;
            }}
            
            QListWidget::item:hover:!selected {{
                background-color: {c['background_tertiary']};
            }}
        """
    
    def apply_theme(self, app: QApplication) -> None:
        """Apply the current theme to the application."""
        app.setStyleSheet(self.get_style_sheet())
        
        # Set palette for native widgets
        palette = QPalette()
        c = self._colors
        
        palette.setColor(QPalette.ColorRole.Window, QColor(c['background_primary']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(c['text_primary']))
        palette.setColor(QPalette.ColorRole.Base, QColor(c['background_secondary']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(c['background_tertiary']))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(c['background_tertiary']))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(c['text_primary']))
        palette.setColor(QPalette.ColorRole.Text, QColor(c['text_primary']))
        palette.setColor(QPalette.ColorRole.Button, QColor(c['button_bg']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(c['button_text']))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(c['accent_primary']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(c['text_disabled']))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(c['text_disabled']))
        
        app.setPalette(palette)


# Singleton instance
theme_manager = ThemeManager()