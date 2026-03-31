"""
Main Window for Horizon Password Generator

The primary application window with navigation and all features.
"""

from pwd_generator.gui import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QMenuBar,
    QMenu, QToolBar, QStatusBar, QMessageBox, QFileDialog,
    QApplication, QAction, QDialog, QLineEdit, QDialogButtonBox,
    QGridLayout, QGroupBox, Qt, QSplitter, QSizePolicy,
)
from pwd_generator.gui.widgets import theme_manager
from pwd_generator.gui.generator_window import GeneratorWindow
from pwd_generator.gui.history_window import HistoryWindow
from pwd_generator.gui.settings_window import SettingsWindow
from pwd_generator import SecurePasswordGenerator
from pwd_generator.exceptions import ValidationError, EncryptionError
from pwd_generator.encryption import clear_memory
from pwd_generator.config import load_config
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MasterPasswordDialog(QDialog):
    """Dialog for entering the master password."""
    
    def __init__(self, is_new: bool = False, parent=None):
        super().__init__(parent)
        self._is_new = is_new
        self._master_password = None
        self._setup_ui()
    
    def _setup_ui(self):
        title = "Create Master Password" if self._is_new else "Enter Master Password"
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Info label
        if self._is_new:
            info = QLabel(
                "Create a master password to encrypt your password history.\n"
                "This password must be at least 12 characters with good entropy."
            )
        else:
            info = QLabel("Enter your master password to unlock your password history.")
        info.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
        layout.addWidget(info)
        
        # Password fields
        password_group = QGroupBox("Master Password")
        password_layout = QGridLayout(password_group)
        
        password_layout.addWidget(QLabel("Password:"), 0, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter master password...")
        password_layout.addWidget(self.password_edit, 0, 1)
        
        if self._is_new:
            password_layout.addWidget(QLabel("Confirm:"), 1, 0)
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_edit.setPlaceholderText("Confirm master password...")
            password_layout.addWidget(self.confirm_edit, 1, 1)
        
        layout.addWidget(password_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _accept(self):
        """Handle accept button."""
        password = self.password_edit.text()
        
        if len(password) < 12:
            QMessageBox.warning(self, "Error", "Master password must be at least 12 characters.")
            return
        
        if self._is_new:
            confirm = self.confirm_edit.text()
            if password != confirm:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return
        
        self._master_password = bytearray(password.encode("utf-8"))
        self.accept()
    
    def get_master_password(self) -> bytearray:
        """Get the entered master password."""
        return self._master_password


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Features:
    - Navigation sidebar
    - Stacked widget for different views
    - Menu bar and toolbar
    - Status bar
    """
    
    def __init__(self):
        super().__init__()
        
        self._generator = None
        self._master_password = None
        
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # Show master password dialog
        if not self._show_master_password_dialog():
            # User cancelled, close the app
            self.close()
            return
    
    def _setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle("Horizon Password Generator")
        self.setMinimumSize(880, 560)
        self.resize(1100, 720)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.setChildrenCollapsible(False)
        self._main_splitter.setHandleWidth(4)

        sidebar = self._create_sidebar()
        self._main_splitter.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.stack.setMinimumWidth(360)
        self.stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        placeholder = QWidget()
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.addWidget(QLabel("Loading…"))
        self.stack.addWidget(placeholder)

        self._main_splitter.addWidget(self.stack)
        self._main_splitter.setStretchFactor(0, 0)
        self._main_splitter.setStretchFactor(1, 1)
        self._main_splitter.setSizes([224, 876])

        outer.addWidget(self._main_splitter)
    
    def _create_sidebar(self) -> QWidget:
        """Create the navigation sidebar."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(168)
        sidebar.setMaximumWidth(340)
        self._sidebar = sidebar

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(10)

        self._sidebar_title = QLabel("Horizon")
        self._sidebar_title.setStyleSheet(
            f"""
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 0.5px;
            padding: 4px 4px 12px 4px;
            color: {theme_manager.get_color('text_primary')};
        """
        )
        layout.addWidget(self._sidebar_title)

        self._sidebar_line = QFrame()
        self._sidebar_line.setFrameShape(QFrame.Shape.HLine)
        self._sidebar_line.setFixedHeight(1)
        layout.addWidget(self._sidebar_line)

        self.nav_buttons = []

        nav_items = [
            ("Generate", "generator"),
            ("History", "history"),
            ("Settings", "settings"),
        ]

        for label, page_id in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setChecked(page_id == "generator")
            btn.setMinimumHeight(40)
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            btn.clicked.connect(lambda checked, p=page_id: self._navigate_to(p))
            layout.addWidget(btn)
            self.nav_buttons.append((btn, page_id))

        layout.addStretch(1)

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("navButton")
        self.theme_btn.setCheckable(False)
        self.theme_btn.setMinimumHeight(40)
        self.theme_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._sync_theme_button_label()
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        version = QLabel("v1.0.0")
        version.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;"
        )
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        self._apply_sidebar_chrome()
        return sidebar
    
    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export History...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_history)
        file_menu.addAction(export_action)
        
        import_action = QAction("Import Passwords...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._import_passwords)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        audit_action = QAction("Password Audit...", self)
        audit_action.setShortcut("Ctrl+A")
        audit_action.triggered.connect(self._show_audit)
        tools_menu.addAction(audit_action)
        
        qr_action = QAction("QR Code Generator...", self)
        qr_action.triggered.connect(self._show_qr_generator)
        tools_menu.addAction(qr_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Generate action
        gen_action = QAction("Generate", self)
        gen_action.triggered.connect(lambda: self._navigate_to("generator"))
        toolbar.addAction(gen_action)
        
        # History action
        hist_action = QAction("History", self)
        hist_action.triggered.connect(lambda: self._navigate_to("history"))
        toolbar.addAction(hist_action)
    
    def _setup_statusbar(self):
        """Set up the status bar."""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        self._statusbar = statusbar
        statusbar.showMessage("Ready")
    
    def _show_master_password_dialog(self) -> bool:
        """Show master password dialog and initialize generator."""
        config = load_config()
        history_file = config.get("history_file", "password_history.enc")
        history_exists = Path(history_file).exists()
        
        dialog = MasterPasswordDialog(is_new=not history_exists, parent=self)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        
        self._master_password = dialog.get_master_password()
        
        try:
            self._generator = SecurePasswordGenerator(
                history_file=history_file,
                master_password=self._master_password,
                policy=config.get("policy", {})
            )
            
            # Initialize views
            self._init_views()
            
            return True
            
        except ValidationError as e:
            QMessageBox.critical(self, "Validation Error", str(e))
            return False
        except EncryptionError as e:
            QMessageBox.critical(
                self, 
                "Decryption Error",
                f"{e}\n\nThis usually means the master password is incorrect."
            )
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize: {e}")
            logger.exception("Failed to initialize generator")
            return False
    
    def _init_views(self):
        """Initialize all views."""
        # Clear placeholder
        while self.stack.count():
            self.stack.removeWidget(self.stack.widget(0))
        
        # Create views
        self.generator_view = GeneratorWindow(self._generator)
        self.history_view = HistoryWindow(self._generator)
        self.settings_view = SettingsWindow(self._generator)
        
        # Add to stack
        self.stack.addWidget(self.generator_view)
        self.stack.addWidget(self.history_view)
        self.stack.addWidget(self.settings_view)
        
        # Navigate to generator
        self._navigate_to("generator")
    
    def _navigate_to(self, page_id: str):
        """Navigate to a page."""
        page_map = {
            "generator": 0,
            "history": 1,
            "settings": 2,
        }
        
        if page_id in page_map:
            self.stack.setCurrentIndex(page_map[page_id])
            
            # Update nav buttons
            for btn, pid in self.nav_buttons:
                btn.setChecked(pid == page_id)
            
            # Refresh history view when navigating to it
            if page_id == "history":
                self.history_view.refresh()
    
    def _sync_theme_button_label(self) -> None:
        if theme_manager.current_theme == "dark":
            self.theme_btn.setText("Switch to light theme")
        else:
            self.theme_btn.setText("Switch to dark theme")

    def _apply_sidebar_chrome(self) -> None:
        if not hasattr(self, "_sidebar"):
            return
        self._sidebar.setStyleSheet(
            f"""
            QFrame#sidebar {{
                background-color: {theme_manager.get_color('background_secondary')};
                border-right: 1px solid {theme_manager.get_color('border_primary')};
            }}
        """
        )
        if hasattr(self, "_sidebar_line"):
            self._sidebar_line.setStyleSheet(
                f"background-color: {theme_manager.get_color('border_primary')};"
            )
        if hasattr(self, "_sidebar_title"):
            self._sidebar_title.setStyleSheet(
                f"""
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 0.5px;
            padding: 4px 4px 12px 4px;
            color: {theme_manager.get_color('text_primary')};
        """
            )

    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        theme_manager.toggle_theme()
        self._sync_theme_button_label()
        theme_manager.apply_theme(QApplication.instance())
        self._apply_sidebar_chrome()
    
    def _export_history(self):
        """Export password history."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export History",
            "password_history.json",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith(".json"):
                from pwd_generator.export import export_history_json
                success = export_history_json(self._generator.history, file_path)
            else:
                from pwd_generator.export import export_history_csv
                success = export_history_csv(self._generator.history, file_path)
            
            if success:
                QMessageBox.information(self, "Export Complete", f"History exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export history.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
    
    def _import_passwords(self):
        """Import passwords from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Passwords",
            "",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith(".json"):
                from pwd_generator.import_export import import_from_json
                entries = import_from_json(file_path)
            else:
                from pwd_generator.import_export import import_from_csv
                entries = import_from_csv(file_path)
            
            imported = 0
            for entry in entries:
                self._generator.add_to_history(
                    entry["password"],
                    entry["metadata"].get("service", ""),
                    entry["metadata"].get("notes", "")
                )
                imported += 1
            
            QMessageBox.information(self, "Import Complete", f"Imported {imported} passwords.")
            self.history_view.refresh()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")
    
    def _show_audit(self):
        """Show password audit dialog."""
        from pwd_generator.audit import PasswordAuditor
        import json
        
        auditor = PasswordAuditor(self._generator)
        report = auditor.generate_audit_report()
        
        score = report["security_score"]
        
        QMessageBox.information(
            self,
            "Password Audit",
            f"Security Score: {score['score']:.1f}/100\n\n"
            f"Total Passwords: {score['details']['total_passwords']}\n"
            f"Weak Passwords: {score['details']['weak_passwords']}\n"
            f"Duplicate Passwords: {score['details']['duplicate_passwords']}\n"
            f"Expired Passwords: {score['details']['expired_passwords']}"
        )
    
    def _show_qr_generator(self):
        """Show QR code generator."""
        QMessageBox.information(self, "QR Generator", "QR Code generation is available via the CLI.")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Horizon Password Generator",
            "<h3>Horizon Password Generator</h3>"
            "<p>A secure password generator with encrypted history, "
            "breach checking, and password analysis.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Random password generation</li>"
            "<li>Passphrase generation</li>"
            "<li>PIN generation</li>"
            "<li>Password strength analysis</li>"
            "<li>Breach checking via HaveIBeenPwned</li>"
            "<li>Encrypted password history</li>"
            "<li>QR code generation</li>"
            "</ul>"
            "<p>Version: 1.0.0</p>"
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Clear sensitive data
        if self._master_password:
            clear_memory(self._master_password)
        
        if self._generator:
            self._generator.clear_sensitive_data()
        
        event.accept()


def run_gui():
    """Run the GUI application."""
    import sys
    
    app = QApplication(sys.argv)
    app.setApplicationName("Horizon Password Generator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Horizon")
    
    # Apply theme
    theme_manager.apply_theme(app)
    
    # Create and show main window
    window = MainWindow()
    
    # Only show if initialization succeeded
    if window._generator:
        window.show()
        return app.exec()
    else:
        return 0


if __name__ == "__main__":
    run_gui()