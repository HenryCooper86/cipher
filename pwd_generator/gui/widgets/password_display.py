"""
Password Display Widget

A widget for displaying passwords with copy/show functionality.
"""

from pwd_generator.gui import (
    QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    Qt, QClipboard, QApplication, QTimer, QSizePolicy,
)
from pwd_generator.gui.widgets.theme import theme_manager


class PasswordDisplay(QWidget):
    """
    Password display widget with copy and show/hide buttons.
    
    Features:
    - Password field with optional masking
    - Copy to clipboard button
    - Show/hide password toggle
    - Visual feedback on copy
    """
    
    def __init__(self, placeholder: str = "Generated password will appear here", parent=None):
        super().__init__(parent)
        self._password = ""
        self._show_password = False
        self._placeholder = placeholder
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Password field row
        field_layout = QHBoxLayout()
        field_layout.setSpacing(8)
        
        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText(self._placeholder)
        self.password_field.setReadOnly(True)
        self.password_field.setObjectName("passwordField")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        field_layout.addWidget(self.password_field, 1)
        
        # Show/hide button
        self.show_button = QPushButton("Show")
        self.show_button.setMinimumWidth(72)
        self.show_button.setMinimumHeight(36)
        self.show_button.setToolTip("Show or hide password")
        self.show_button.clicked.connect(self._toggle_visibility)
        field_layout.addWidget(self.show_button)
        
        self.copy_button = QPushButton("Copy")
        self.copy_button.setMinimumWidth(72)
        self.copy_button.setMinimumHeight(36)
        self.copy_button.setToolTip("Copy password to clipboard")
        self.copy_button.clicked.connect(self._copy_to_clipboard)
        field_layout.addWidget(self.copy_button)
        
        layout.addLayout(field_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {theme_manager.get_color('accent_success')}; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.status_label)
    
    def set_password(self, password: str):
        """Set the password to display."""
        self._password = password
        self.password_field.setText(password)
        self.password_field.setEchoMode(
            QLineEdit.EchoMode.Normal if self._show_password else QLineEdit.EchoMode.Password
        )
    
    def get_password(self) -> str:
        """Get the current password."""
        return self._password
    
    def clear(self):
        """Clear the password field."""
        self._password = ""
        self.password_field.clear()
        self.status_label.clear()
    
    def _toggle_visibility(self):
        """Toggle password visibility."""
        self._show_password = not self._show_password
        if self._show_password:
            self.password_field.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_button.setText("Hide")
        else:
            self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_button.setText("Show")
    
    def _copy_to_clipboard(self):
        """Copy password to clipboard."""
        if not self._password:
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self._password)
        
        # Visual feedback
        self.status_label.setText("Copied to clipboard.")
        self.copy_button.setText("Copied")
        self.copy_button.setStyleSheet(f"background-color: {theme_manager.get_color('accent_success')}; color: white;")
        
        # Reset after delay
        QTimer.singleShot(2000, self._reset_copy_button)
    
    def _reset_copy_button(self):
        """Reset the copy button to default state."""
        self.copy_button.setText("Copy")
        self.copy_button.setStyleSheet("")
        self.status_label.clear()


class PasswordEditor(QWidget):
    """
    Password editor widget for manual password input.
    
    Features:
    - Editable password field
    - Strength indicator integration
    - Character set options
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._password = ""
        self._show_password = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Password field row
        field_layout = QHBoxLayout()
        field_layout.setSpacing(8)
        
        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText("Enter password...")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setObjectName("passwordField")
        self.password_field.textChanged.connect(self._on_password_changed)
        field_layout.addWidget(self.password_field, 1)
        
        # Show/hide button
        self.show_button = QPushButton("Show")
        self.show_button.setMinimumWidth(72)
        self.show_button.setMinimumHeight(36)
        self.show_button.setToolTip("Show or hide password")
        self.show_button.clicked.connect(self._toggle_visibility)
        field_layout.addWidget(self.show_button)
        
        self.generate_button = QPushButton("Random")
        self.generate_button.setMinimumWidth(72)
        self.generate_button.setMinimumHeight(36)
        self.generate_button.setToolTip("Generate random password (connect in parent if needed)")
        field_layout.addWidget(self.generate_button)
        
        layout.addLayout(field_layout)
    
    def set_password(self, password: str):
        """Set the password."""
        self._password = password
        self.password_field.setText(password)
    
    def get_password(self) -> str:
        """Get the current password."""
        return self.password_field.text()
    
    def clear(self):
        """Clear the password field."""
        self._password = ""
        self.password_field.clear()
    
    def _toggle_visibility(self):
        """Toggle password visibility."""
        self._show_password = not self._show_password
        if self._show_password:
            self.password_field.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_button.setText("Hide")
        else:
            self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_button.setText("Show")
    
    def _on_password_changed(self, text: str):
        """Handle password text change."""
        self._password = text