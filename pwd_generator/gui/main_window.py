"""
Main window for Horizon Cypher.

The primary application window with navigation and all features.
"""

import logging
from pathlib import Path

from pwd_generator import SecurePasswordGenerator
from pwd_generator.config import load_config
from pwd_generator.encryption import clear_memory
from pwd_generator.exceptions import EncryptionError, ValidationError
from pwd_generator.gui import (
    QAction,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequence,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    Qt,
    QTimer,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from pwd_generator.gui import icons as gui_icons
from pwd_generator.gui.cli_terminal import CliTerminalPanel
from pwd_generator.gui.constants import (
    APP_DISPLAY_NAME,
    CLI_PANEL_MIN_HEIGHT_PX,
    CLI_SPLITTER_CLI_ABSOLUTE_MIN_PX,
    CLI_SPLITTER_CLI_FRACTION,
    CLI_SPLITTER_INITIAL_BOTTOM_PX,
    CLI_SPLITTER_INITIAL_TOP_PX,
    CLI_SPLITTER_MIN_CLI_PX,
    CLI_SPLITTER_MIN_MAIN_PX,
    CLI_SPLITTER_REBALANCE_IF_HEIGHT_BELOW_PX,
)
from pwd_generator.gui.generator_window import GeneratorWindow
from pwd_generator.gui.history_window import HistoryWindow
from pwd_generator.gui.settings_window import SettingsWindow
from pwd_generator.gui.widgets import theme_manager

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
        import hmac
        
        password = self.password_edit.text()

        if len(password) < 12:
            QMessageBox.warning(self, "Error", "Master password must be at least 12 characters.")
            return

        if self._is_new:
            confirm = self.confirm_edit.text()
            # Use constant-time comparison to prevent timing attacks
            if not hmac.compare_digest(password.encode('utf-8'), confirm.encode('utf-8')):
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return

        self._master_password = bytearray(password.encode("utf-8"))
        self.accept()

    def get_master_password(self) -> bytearray:
        """Get the entered master password."""
        return self._master_password


class MainWindow(QMainWindow):
    """
    Main application window: menu bar (primary actions), optional sidebar,
    stacked views, status bar.
    """

    def __init__(self):
        super().__init__()

        self._generator = None
        self._master_password = None

        self._setup_ui()
        self.setWindowIcon(gui_icons.create_application_icon())
        self._setup_menus()
        self._setup_statusbar()

        # Show master password dialog
        if not self._show_master_password_dialog():
            # User cancelled, close the app
            self.close()
            return

    def _setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle(APP_DISPLAY_NAME)
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

        self._top_content = QWidget()
        top_layout = QVBoxLayout(self._top_content)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)

        self._sidebar_toggle_btn = QToolButton()
        self._sidebar_toggle_btn.setObjectName("sidebarToggleButton")
        self._sidebar_toggle_btn.setFixedWidth(26)
        self._sidebar_toggle_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        self._sidebar_toggle_btn.setAutoRaise(True)
        self._sidebar_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sidebar_toggle_btn.clicked.connect(self._toggle_sidebar_strip)
        content_row.addWidget(self._sidebar_toggle_btn)

        content_row.addWidget(self._main_splitter, 1)
        top_layout.addLayout(content_row)

        self._cli_strip_toggle = QToolButton()
        self._cli_strip_toggle.setObjectName("cliStripToggle")
        self._cli_strip_toggle.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._cli_strip_toggle.setFixedHeight(24)
        self._cli_strip_toggle.setAutoRaise(True)
        self._cli_strip_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cli_strip_toggle.clicked.connect(self._toggle_cli_strip)
        top_layout.addWidget(self._cli_strip_toggle)

        self._cli_panel = CliTerminalPanel(self)
        self._cli_panel.setMinimumHeight(CLI_PANEL_MIN_HEIGHT_PX)

        self._vert_splitter = QSplitter(Qt.Orientation.Vertical)
        self._vert_splitter.setChildrenCollapsible(False)
        self._vert_splitter.setHandleWidth(5)
        self._vert_splitter.addWidget(self._top_content)
        self._vert_splitter.addWidget(self._cli_panel)
        self._cli_panel.setVisible(False)
        self._vert_splitter.setStretchFactor(0, 1)
        self._vert_splitter.setStretchFactor(1, 1)
        self._vert_splitter.setSizes(
            [CLI_SPLITTER_INITIAL_TOP_PX, CLI_SPLITTER_INITIAL_BOTTOM_PX]
        )

        outer.addWidget(self._vert_splitter)

        theme_manager.register_theme_listener(self._on_theme_applied)
        self._sync_sidebar_toggle_state(True)
        self._sync_cli_toggle_state(False)

    def _create_sidebar(self) -> QWidget:
        """Create the navigation sidebar."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(200)
        sidebar.setMaximumWidth(340)
        self._sidebar = sidebar

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(10)

        self._sidebar_title = QLabel(APP_DISPLAY_NAME)
        self._sidebar_title.setWordWrap(False)
        self._sidebar_title.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self._sidebar_title.setStyleSheet(
            f"""
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.2px;
            line-height: 1.2;
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
            ("Saved Passwords", "history"),
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

        self.exit_btn = QPushButton("Quit")
        self.exit_btn.setObjectName("navButton")
        self.exit_btn.setCheckable(False)
        self.exit_btn.setMinimumHeight(40)
        self.exit_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.exit_btn.setToolTip("Quit the application (Ctrl+Q)")
        self.exit_btn.clicked.connect(self.close)
        layout.addWidget(self.exit_btn)

        self._sidebar_version_label = QLabel("v1.0.0")
        self._sidebar_version_label.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;"
        )
        self._sidebar_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._sidebar_version_label)

        self._apply_sidebar_chrome()
        return sidebar

    def _setup_menus(self):
        """Set up the menu bar (primary navigation and actions)."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        export_action = QAction("Export Saved Passwords...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._export_history)
        file_menu.addAction(export_action)

        import_action = QAction("Import Passwords...", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._import_passwords)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # View menu (sidebar + navigation + appearance)
        view_menu = menubar.addMenu("View")

        self._show_sidebar_action = QAction("Show Sidebar", self)
        self._show_sidebar_action.setCheckable(True)
        self._show_sidebar_action.setChecked(True)
        self._show_sidebar_action.setShortcut(QKeySequence("Ctrl+B"))
        self._show_sidebar_action.toggled.connect(self._set_sidebar_visible)
        view_menu.addAction(self._show_sidebar_action)

        self._show_cli_panel_action = QAction("Show CLI Panel", self)
        self._show_cli_panel_action.setCheckable(True)
        self._show_cli_panel_action.setChecked(False)
        self._show_cli_panel_action.setShortcut(QKeySequence("Ctrl+J"))
        self._show_cli_panel_action.toggled.connect(self._set_cli_panel_visible)
        view_menu.addAction(self._show_cli_panel_action)

        focus_cli = QAction("Focus CLI Input", self)
        focus_cli.setShortcut(QKeySequence("Ctrl+Shift+T"))
        focus_cli.triggered.connect(self._focus_cli_input)
        view_menu.addAction(focus_cli)

        view_menu.addSeparator()

        go_gen = QAction("Generate", self)
        go_gen.setShortcut(QKeySequence("Ctrl+1"))
        go_gen.triggered.connect(lambda: self._navigate_to("generator"))
        view_menu.addAction(go_gen)

        go_saved = QAction("Saved Passwords", self)
        go_saved.setShortcut(QKeySequence("Ctrl+2"))
        go_saved.triggered.connect(lambda: self._navigate_to("history"))
        view_menu.addAction(go_saved)

        go_settings = QAction("Settings", self)
        go_settings.setShortcut(QKeySequence("Ctrl+3"))
        go_settings.triggered.connect(lambda: self._navigate_to("settings"))
        view_menu.addAction(go_settings)

        view_menu.addSeparator()

        self._theme_menu_action = QAction(self)
        self._theme_menu_action.triggered.connect(self._toggle_theme)
        self._sync_theme_menu_label()
        view_menu.addAction(self._theme_menu_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        audit_action = QAction("Password Audit...", self)
        audit_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        audit_action.triggered.connect(self._show_audit)
        tools_menu.addAction(audit_action)

        qr_action = QAction("QR Code for Current Password...", self)
        qr_action.setShortcut(QKeySequence("Ctrl+Shift+Q"))
        qr_action.triggered.connect(self._show_qr_generator)
        tools_menu.addAction(qr_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        cli_cheat_action = QAction("CLI Command Cheatsheet", self)
        cli_cheat_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
        cli_cheat_action.triggered.connect(self._show_cli_cheatsheet)
        help_menu.addAction(cli_cheat_action)

        help_menu.addSeparator()

        about_action = QAction("About Horizon Cypher", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        self._sync_sidebar_toggle_state(self._sidebar.isVisible())
        self._sync_cli_toggle_state(self._cli_panel.isVisible())

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

        self._cli_panel.set_generator(self._generator)
        self._cli_panel.ensure_welcome_shown()
        self._cli_panel.command_finished.connect(self._on_cli_command_finished)

    def _on_cli_command_finished(self, code: int) -> None:
        if code == 0 and hasattr(self, "history_view"):
            self.history_view.refresh()

    def _focus_cli_input(self) -> None:
        if hasattr(self, "_cli_panel"):
            if not self._cli_panel.isVisible():
                self._set_cli_panel_visible(True)
            self._cli_panel.focus_cli_input()

    def _show_cli_cheatsheet(self) -> None:
        if hasattr(self, "_cli_panel"):
            self._cli_panel.show_cheatsheet_dialog()

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

    def _set_sidebar_visible(self, visible: bool) -> None:
        """Show or hide the navigation sidebar splitter child.

        When hidden, the main area uses the full width.
        """
        if hasattr(self, "_sidebar"):
            self._sidebar.setVisible(visible)
        self._sync_sidebar_toggle_state(visible)

    def _toggle_sidebar_strip(self) -> None:
        """Toggle sidebar from the strip button (keeps View menu in sync)."""
        if not hasattr(self, "_sidebar"):
            return
        self._set_sidebar_visible(not self._sidebar.isVisible())

    def _sync_sidebar_toggle_state(self, visible: bool) -> None:
        """Update strip button label/tooltip and View ▸ Show Sidebar check state."""
        if hasattr(self, "_sidebar_toggle_btn"):
            self._sidebar_toggle_btn.setText("◀" if visible else "▶")
            self._sidebar_toggle_btn.setToolTip(
                "Hide sidebar" if visible else "Show sidebar"
            )
        if hasattr(self, "_show_sidebar_action"):
            self._show_sidebar_action.blockSignals(True)
            self._show_sidebar_action.setChecked(visible)
            self._show_sidebar_action.blockSignals(False)
        self._apply_sidebar_toggle_chrome()

    def _set_cli_panel_visible(self, visible: bool) -> None:
        if hasattr(self, "_cli_panel"):
            self._cli_panel.setVisible(visible)
            if visible:
                QTimer.singleShot(0, self._balance_cli_splitter)
        self._sync_cli_toggle_state(visible)

    def _balance_cli_splitter(self) -> None:
        """Give the CLI / shell panel a usable share of vertical space when shown."""
        if not hasattr(self, "_vert_splitter") or not hasattr(self, "_cli_panel"):
            return
        if not self._cli_panel.isVisible():
            return
        splitter = self._vert_splitter
        total = splitter.height()
        if total < CLI_SPLITTER_REBALANCE_IF_HEIGHT_BELOW_PX:
            QTimer.singleShot(0, self._balance_cli_splitter)
            return
        handle = splitter.handleWidth()
        avail = max(1, total - handle)
        target = int(avail * CLI_SPLITTER_CLI_FRACTION)
        bottom = max(CLI_SPLITTER_MIN_CLI_PX, target)
        bottom = min(bottom, avail - CLI_SPLITTER_MIN_MAIN_PX)
        bottom = max(CLI_SPLITTER_CLI_ABSOLUTE_MIN_PX, bottom)
        top = avail - bottom
        splitter.setSizes([max(1, top), max(1, bottom)])

    def _toggle_cli_strip(self) -> None:
        if not hasattr(self, "_cli_panel"):
            return
        self._set_cli_panel_visible(not self._cli_panel.isVisible())

    def _sync_cli_toggle_state(self, visible: bool) -> None:
        if hasattr(self, "_cli_strip_toggle"):
            self._cli_strip_toggle.setText(
                "▲ Hide CLI panel" if visible else "▼ Show CLI panel"
            )
            self._cli_strip_toggle.setToolTip(
                "Hide the CLI panel (Ctrl+J)" if visible else "Show the CLI panel (Ctrl+J)"
            )
        if hasattr(self, "_show_cli_panel_action"):
            self._show_cli_panel_action.blockSignals(True)
            self._show_cli_panel_action.setChecked(visible)
            self._show_cli_panel_action.blockSignals(False)
        self._apply_cli_strip_chrome()

    def _apply_cli_strip_chrome(self) -> None:
        if not hasattr(self, "_cli_strip_toggle"):
            return
        c = theme_manager.get_color
        self._cli_strip_toggle.setStyleSheet(
            f"""
            QToolButton#cliStripToggle {{
                border: none;
                border-top: 1px solid {c('border_primary')};
                background-color: {c('background_secondary')};
                color: {c('text_secondary')};
                font-size: 12px;
                padding: 4px 8px;
            }}
            QToolButton#cliStripToggle:hover {{
                background-color: {c('background_tertiary')};
                color: {c('text_primary')};
            }}
        """
        )

    def _apply_sidebar_toggle_chrome(self) -> None:
        if not hasattr(self, "_sidebar_toggle_btn"):
            return
        c = theme_manager.get_color
        self._sidebar_toggle_btn.setStyleSheet(
            f"""
            QToolButton#sidebarToggleButton {{
                border: none;
                border-right: 1px solid {c('border_primary')};
                background-color: {c('background_secondary')};
                color: {c('text_primary')};
                font-size: 15px;
                font-weight: 600;
                padding: 0;
            }}
            QToolButton#sidebarToggleButton:hover {{
                background-color: {c('background_tertiary')};
            }}
            QToolButton#sidebarToggleButton:pressed {{
                background-color: {c('border_primary')};
            }}
        """
        )

    def _sync_theme_menu_label(self) -> None:
        if not hasattr(self, "_theme_menu_action"):
            return
        if theme_manager.current_theme == "dark":
            self._theme_menu_action.setText("Switch to Light Theme")
        else:
            self._theme_menu_action.setText("Switch to Dark Theme")

    def _on_theme_applied(self) -> None:
        self._apply_sidebar_chrome()
        self._apply_sidebar_toggle_chrome()
        self._apply_cli_strip_chrome()
        self._sync_theme_menu_label()
        if getattr(self, "_generator", None) and hasattr(self, "generator_view"):
            self.generator_view.refresh_theme_styles()
            self.history_view.refresh_theme_styles()
            self.settings_view.refresh_theme_styles()
        version = getattr(self, "_sidebar_version_label", None)
        if version is not None:
            version.setStyleSheet(
                f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;"
            )
        if hasattr(self, "_cli_panel"):
            self._cli_panel.refresh_theme_styles()

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
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.2px;
            line-height: 1.2;
            padding: 4px 4px 12px 4px;
            color: {theme_manager.get_color('text_primary')};
        """
            )

    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        theme_manager.toggle_theme()
        theme_manager.apply_theme(QApplication.instance())

    def _export_history(self):
        """Export password history."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Saved Passwords",
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
                QMessageBox.information(
                    self, "Export Complete", f"Saved passwords exported to {file_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Export Failed", "Failed to export saved passwords."
                )
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

        auditor = PasswordAuditor(self._generator)
        report = auditor.generate_audit_report()

        score = report["security_score"]
        det = score["details"]
        sim_line = f"Similar Pairs: {det.get('similar_pairs', 0)}"
        if det.get("similar_audit_skipped"):
            sim_line += " (scan skipped for large vault)"

        QMessageBox.information(
            self,
            "Password Audit",
            f"Security Score: {score['score']:.1f}/100\n\n"
            f"Total Passwords: {det['total_passwords']}\n"
            f"Weak Passwords: {det['weak_passwords']}\n"
            f"Duplicate Passwords: {det['duplicate_passwords']}\n"
            f"{sim_line}\n"
            f"Expired Passwords: {det['expired_passwords']}"
        )

    def _show_qr_generator(self):
        """Open Generate view and show QR for the current generated or analyzed password."""
        if not getattr(self, "generator_view", None):
            return
        self._navigate_to("generator")
        self.generator_view.open_qr_code_dialog(self)

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"About {APP_DISPLAY_NAME}",
            f"<h3>{APP_DISPLAY_NAME}</h3>"
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

    try:
        from PyQt6.QtWidgets import QStyleFactory
    except ImportError:
        from PySide6.QtWidgets import QStyleFactory

    app = QApplication(sys.argv)
    aa = getattr(Qt, "ApplicationAttribute", None)
    if aa is not None:
        no_native = getattr(aa, "AA_DontUseNativeMenuBar", None)
        if no_native is not None:
            app.setAttribute(no_native, True)
    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName(APP_DISPLAY_NAME)
    app.setWindowIcon(gui_icons.create_application_icon())

    cfg = load_config()
    theme = cfg.get("theme")
    if isinstance(theme, str) and theme.lower() in ("dark", "light"):
        theme_manager.set_theme(theme.lower())

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
