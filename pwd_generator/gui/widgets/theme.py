"""
Theme Manager for Horizon Password Manager GUI

Supports dark and light themes with calibrated sRGB-friendly palettes.
"""

from pwd_generator.gui import (
    QColor, QPalette, QFont, QBrush, QPen,
    Qt, QApplication,
)
from typing import Callable, Dict, List
import logging

logger = logging.getLogger(__name__)


class ThemeColors:
    """Color definitions for themes."""
    
    DARK = {
        # Surfaces (slightly lifted contrast vs prior flat navy)
        "background_primary": "#12131c",
        "background_secondary": "#1b1d2a",
        "background_tertiary": "#252838",
        "background_input": "#1e2233",
        # Text
        "text_primary": "#c8d3f5",
        "text_secondary": "#a9b4d6",
        "text_disabled": "#565f89",
        "text_link": "#7aa2f7",
        # Accents
        "accent_primary": "#7aa2f7",
        "accent_secondary": "#9ece6a",
        "accent_warning": "#e0af68",
        "accent_danger": "#f7768e",
        "accent_success": "#9ece6a",
        # Strength meter
        "strength_weak": "#f7768e",
        "strength_fair": "#e0af68",
        "strength_good": "#7dcfff",
        "strength_strong": "#9ece6a",
        "strength_very_strong": "#73daca",
        "strength_badge_text": "#ffffff",
        # Borders
        "border_primary": "#434a66",
        "border_focus": "#7aa2f7",
        "border_hover": "#5a6288",
        # Selection (menus / native)
        "selection_bg": "#7aa2f7",
        "selection_text": "#16161e",
        # Scrollbar
        "scrollbar_bg": "#1b1d2a",
        "scrollbar_handle": "#4a5270",
        # Buttons
        "button_bg": "#2a2f45",
        "button_hover": "#363c58",
        "button_pressed": "#424a6a",
        "button_text": "#c8d3f5",
        # Tables / lists
        "table_header_bg": "#1b1d2a",
        "table_header_text": "#c8d3f5",
        "table_row_alt": "#222536",
        "table_row_selected": "#304069",
        "table_row_selected_text": "#e8eeff",
        # Checkbox frame (unchecked must read on table + input surfaces)
        "checkbox_unchecked_bg": "#2c334d",
        "checkbox_unchecked_border": "#8b97c4",
        "checkbox_unchecked_hover_bg": "#383f5c",
        # Checkbox checked PNG (high contrast on dark)
        "checkbox_checked_bg": "#3e4f7d",
        "checkbox_checked_border": "#b8ceff",
        "checkbox_tick": "#ffffff",
    }
    
    LIGHT = {
        "background_primary": "#f5f6f8",
        "background_secondary": "#ffffff",
        "background_tertiary": "#eceef2",
        "background_input": "#ffffff",
        "text_primary": "#1a1d26",
        "text_secondary": "#5c6370",
        "text_disabled": "#9aa0a8",
        "text_link": "#2d5a8c",
        "accent_primary": "#3b6ea8",
        "accent_secondary": "#3d8b40",
        "accent_warning": "#d97706",
        "accent_danger": "#d32f2f",
        "accent_success": "#2e7d32",
        "strength_weak": "#c62828",
        "strength_fair": "#e65100",
        "strength_good": "#1565c0",
        "strength_strong": "#2e7d32",
        "strength_very_strong": "#00838f",
        "strength_badge_text": "#ffffff",
        "border_primary": "#d1d5db",
        "border_focus": "#3b6ea8",
        "border_hover": "#b8bec8",
        "selection_bg": "#3b6ea8",
        "selection_text": "#ffffff",
        "scrollbar_bg": "#eceef2",
        "scrollbar_handle": "#c5cad3",
        "button_bg": "#eceef2",
        "button_hover": "#e2e5ea",
        "button_pressed": "#d6dae0",
        "button_text": "#1a1d26",
        "table_header_bg": "#eceef2",
        "table_header_text": "#1a1d26",
        "table_row_alt": "#f9fafb",
        "table_row_selected": "#c5daf5",
        "table_row_selected_text": "#142033",
        "checkbox_unchecked_bg": "#ffffff",
        "checkbox_unchecked_border": "#9aa3b2",
        "checkbox_unchecked_hover_bg": "#f0f2f5",
        "checkbox_checked_bg": "#ffffff",
        "checkbox_checked_border": "#3b6ea8",
        "checkbox_tick": "#1a3d6e",
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
            self._theme_listeners: List[Callable[[], None]] = []
    
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

    def register_theme_listener(self, callback: Callable[[], None]) -> None:
        """Register a callable invoked after each successful apply_theme (e.g. refresh inline styles)."""
        if callback not in self._theme_listeners:
            self._theme_listeners.append(callback)
    
    def get_style_sheet(self) -> str:
        """Generate the complete application stylesheet."""
        c = self._colors
        from pwd_generator.gui import icons

        cb_checked = icons.checkbox_indicator_checked_qss_image(
            self._current_theme, c
        )
        rb_checked = icons.radio_indicator_checked_url(self._current_theme, c)
        combo_arrow = icons.combobox_down_arrow_qss_image(c)

        return f"""
            /* Global Styles */
            QWidget {{
                font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
            }}
            
            QWidget#historyCheckboxHost {{
                background-color: {c['background_tertiary']};
                border-radius: 6px;
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
                width: 28px;
            }}
            
            QComboBox::down-arrow {{
                width: 12px;
                height: 8px;
                border: none;
                image: {combo_arrow if combo_arrow else "none"};
                subcontrol-origin: padding;
                subcontrol-position: center right;
                margin-right: 8px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {c['background_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border_primary']};
                selection-background-color: {c['table_row_selected']};
                selection-color: {c['table_row_selected_text']};
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
                subcontrol-origin: padding;
                subcontrol-position: center center;
            }}
            
            QCheckBox::indicator:unchecked {{
                border: 2px solid {c['checkbox_unchecked_border']};
                border-radius: 4px;
                background-color: {c['checkbox_unchecked_bg']};
            }}
            
            QCheckBox::indicator:unchecked:hover {{
                border-color: {c['border_hover']};
                background-color: {c['checkbox_unchecked_hover_bg']};
            }}
            
            QCheckBox::indicator:unchecked:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['checkbox_unchecked_bg']};
            }}
            
            QCheckBox::indicator:unchecked:pressed {{
                border-color: {c['border_focus']};
                background-color: {c['background_tertiary']};
            }}
            
            QCheckBox::indicator:checked {{
                width: 18px;
                height: 18px;
                border: 2px solid transparent;
                border-radius: 4px;
                background-color: {c['checkbox_checked_bg']};
                image: {cb_checked};
            }}
            
            QCheckBox::indicator:checked:hover {{
                border: 2px solid {c['border_hover']};
                border-radius: 4px;
                background-color: {c['checkbox_checked_bg']};
                image: {cb_checked};
            }}
            
            QCheckBox::indicator:checked:focus {{
                border: 2px solid {c['border_focus']};
                border-radius: 4px;
                background-color: {c['checkbox_checked_bg']};
                image: {cb_checked};
            }}
            
            QCheckBox::indicator:checked:pressed {{
                border: 2px solid {c['border_focus']};
                border-radius: 4px;
                background-color: {c['checkbox_checked_bg']};
                image: {cb_checked};
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
                width: 18px;
                height: 18px;
                border: none;
                image: url("{rb_checked}");
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
            
            QTableCornerButton::section {{
                background-color: {c['table_header_bg']};
                border: none;
                border-bottom: 1px solid {c['border_primary']};
                border-right: 1px solid {c['border_primary']};
                padding: 8px;
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
                color: {c['selection_text']};
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
                color: {c['selection_text']};
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
                background-color: {c['table_row_selected']};
                color: {c['table_row_selected_text']};
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
        palette.setColor(QPalette.ColorRole.Highlight, QColor(c['table_row_selected']))
        palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(c['table_row_selected_text'])
        )
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(c['text_disabled']))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(c['text_disabled']))
        
        app.setPalette(palette)

        for cb in self._theme_listeners:
            try:
                cb()
            except Exception:
                logger.exception("Theme listener callback failed")


# Singleton instance
theme_manager = ThemeManager()