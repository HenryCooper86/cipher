"""
Password Generator Window

Main window for generating passwords with various options.
"""

from pwd_generator.gui import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QLineEdit, QGroupBox, QFrame, QTabWidget, QTextEdit,
    QMessageBox, QFileDialog, QProgressBar, Qt, Signal, QTimer,
    QScrollArea, QSizePolicy,
)
from pwd_generator.gui.widgets import (
    StrengthMeter, PasswordDisplay, theme_manager
)
from pwd_generator import SecurePasswordGenerator
from pwd_generator.exceptions import ValidationError, PasswordGeneratorError
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class GeneratorPanel(QWidget):
    """
    Password generator panel with all generation options.
    
    Features:
    - Random password generation
    - Passphrase generation
    - PIN generation
    - Strength visualization
    - Copy to clipboard
    """
    
    def __init__(self, generator: SecurePasswordGenerator, parent=None):
        super().__init__(parent)
        self._generator = generator
        self._current_password = ""
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Password type selection
        type_group = QGroupBox("Password Type")
        type_layout = QHBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Random Password", "Passphrase", "PIN"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(QLabel("Type:"))
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        
        layout.addWidget(type_group)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QGridLayout(options_group)
        options_layout.setSpacing(12)
        
        # Length option
        options_layout.addWidget(QLabel("Length:"), 0, 0)
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(16)
        options_layout.addWidget(self.length_spin, 0, 1)
        
        # Character options (for random)
        self.char_options_label = QLabel("Include:")
        options_layout.addWidget(self.char_options_label, 0, 2, 1, 1)
        
        char_layout = QHBoxLayout()
        self.uppercase_cb = QCheckBox("A-Z")
        self.uppercase_cb.setChecked(True)
        char_layout.addWidget(self.uppercase_cb)
        
        self.lowercase_cb = QCheckBox("a-z")
        self.lowercase_cb.setChecked(True)
        char_layout.addWidget(self.lowercase_cb)
        
        self.digits_cb = QCheckBox("0-9")
        self.digits_cb.setChecked(True)
        char_layout.addWidget(self.digits_cb)
        
        self.special_cb = QCheckBox("!@#$")
        self.special_cb.setChecked(True)
        char_layout.addWidget(self.special_cb)
        
        options_layout.addLayout(char_layout, 0, 3, 1, 4)
        
        # Words option (for passphrase)
        self.words_label = QLabel("Words:")
        self.words_label.hide()
        options_layout.addWidget(self.words_label, 1, 0)
        
        self.words_spin = QSpinBox()
        self.words_spin.setRange(4, 10)
        self.words_spin.setValue(5)
        self.words_spin.hide()
        options_layout.addWidget(self.words_spin, 1, 1)
        
        # Separator option (for passphrase)
        self.separator_label = QLabel("Separator:")
        self.separator_label.hide()
        options_layout.addWidget(self.separator_label, 1, 2)
        
        self.separator_edit = QLineEdit("-")
        self.separator_edit.setMaxLength(3)
        self.separator_edit.setFixedWidth(50)
        self.separator_edit.hide()
        options_layout.addWidget(self.separator_edit, 1, 3)
        
        options_layout.setColumnStretch(4, 1)
        
        layout.addWidget(options_group)
        
        # Generate button
        btn_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate password")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.clicked.connect(self._generate_password)
        btn_layout.addWidget(self.generate_btn, 1)
        
        layout.addLayout(btn_layout)
        
        # Password display
        display_group = QGroupBox("Generated Password")
        display_layout = QVBoxLayout(display_group)
        
        self.password_display = PasswordDisplay()
        display_layout.addWidget(self.password_display)
        
        layout.addWidget(display_group)
        
        # Strength meter
        strength_group = QGroupBox("Password Analysis")
        strength_layout = QVBoxLayout(strength_group)
        
        self.strength_meter = StrengthMeter()
        strength_layout.addWidget(self.strength_meter)
        
        layout.addWidget(strength_group)
        
        # Save to history
        save_layout = QHBoxLayout()
        
        self.save_cb = QCheckBox("Save to history")
        self.save_cb.setChecked(True)
        save_layout.addWidget(self.save_cb)
        
        save_layout.addStretch()
        
        self.service_label = QLabel("Service:")
        save_layout.addWidget(self.service_label)
        
        self.service_edit = QLineEdit()
        self.service_edit.setPlaceholderText("e.g., gmail, bank, work")
        self.service_edit.setMinimumWidth(200)
        self.service_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        save_layout.addWidget(self.service_edit)
        
        layout.addLayout(save_layout)
        
        # Add stretch to push everything up
        layout.addStretch()
    
    def _on_type_changed(self, index: int):
        """Handle password type change."""
        is_random = index == 0
        is_passphrase = index == 1
        is_pin = index == 2
        
        # Show/hide character options for random
        self.char_options_label.setVisible(is_random)
        self.uppercase_cb.setVisible(is_random)
        self.lowercase_cb.setVisible(is_random)
        self.digits_cb.setVisible(is_random)
        self.special_cb.setVisible(is_random)
        
        # Show/hide passphrase options
        self.words_label.setVisible(is_passphrase)
        self.words_spin.setVisible(is_passphrase)
        self.separator_label.setVisible(is_passphrase)
        self.separator_edit.setVisible(is_passphrase)
        
        # Adjust length spin defaults
        if is_pin:
            self.length_spin.setRange(4, 12)
            self.length_spin.setValue(6)
        else:
            self.length_spin.setRange(8, 64)
            self.length_spin.setValue(16)
    
    def _generate_password(self):
        """Generate a new password."""
        if not self._generator:
            QMessageBox.critical(self, "Error", "Password generator not initialized.")
            return
        
        try:
            password_type = self.type_combo.currentIndex()
            
            if password_type == 0:  # Random
                password = self._generator.generate_random_string(
                    length=self.length_spin.value()
                )
            elif password_type == 1:  # Passphrase
                password = self._generator.generate_passphrase(
                    num_words=self.words_spin.value(),
                    separator=self.separator_edit.text() or "-"
                )
            else:  # PIN
                password = self._generator.generate_pin(
                    length=self.length_spin.value()
                )
            
            self._current_password = password
            self.password_display.set_password(password)
            
            # Update strength meter
            stats = self._generator.get_password_stats(password)
            self.strength_meter.set_strength(
                stats['strength'],
                stats['entropy'],
                stats
            )
            
            # Save to history if checked
            if self.save_cb.isChecked():
                try:
                    if self._generator.encryption_manager and self._generator.encryption_manager.cipher:
                        service = self.service_edit.text().strip() or "Unspecified"
                        self._generator.add_to_history(password, service)
                except Exception as e:
                    logger.warning(f"Failed to save to history: {e}")
                    # Don't show error to user - password was still generated
                
        except ValidationError as e:
            QMessageBox.warning(self, "Generation Error", str(e))
        except PasswordGeneratorError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            logger.exception("Unexpected error during password generation")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
    
    def get_password(self) -> str:
        """Get the current password."""
        return self._current_password

    def refresh_theme_styles(self) -> None:
        """Reapply theme-dependent inline styles after global theme change."""
        self.strength_meter.refresh_from_theme()
        self.password_display.refresh_theme_styles()


class AnalyzerPanel(QWidget):
    """
    Password analyzer panel.
    
    Features:
    - Manual password input
    - Strength analysis
    - Breach checking
    """
    
    # Signal for thread-safe breach result updates
    breach_result_signal = Signal(bool, dict)
    
    def __init__(self, generator: SecurePasswordGenerator, parent=None):
        super().__init__(parent)
        self._generator = generator
        self._breach_ui_state: Optional[str] = None
        self._setup_ui()
        
        # Connect signal for thread-safe updates
        self.breach_result_signal.connect(self._update_breach_result)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Password input
        input_group = QGroupBox("Password to Analyze")
        input_layout = QVBoxLayout(input_group)
        
        from pwd_generator.gui.widgets.password_display import PasswordEditor
        self.password_editor = PasswordEditor()
        self.password_editor.password_field.textChanged.connect(self._analyze_password)
        input_layout.addWidget(self.password_editor)
        
        layout.addWidget(input_group)
        
        # Strength meter
        strength_group = QGroupBox("Analysis Results")
        strength_layout = QVBoxLayout(strength_group)
        
        self.strength_meter = StrengthMeter()
        strength_layout.addWidget(self.strength_meter)
        
        layout.addWidget(strength_group)
        
        # Breach check
        breach_group = QGroupBox("Breach Check")
        breach_layout = QVBoxLayout(breach_group)
        
        self.breach_info = QLabel(
            "Check if your password has appeared in known data breaches.\n"
            "Uses HaveIBeenPwned API with k-anonymity (your password never leaves this device)."
        )
        self.breach_info.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')};"
        )
        breach_layout.addWidget(self.breach_info)
        
        self.breach_btn = QPushButton("Check for breaches")
        self.breach_btn.clicked.connect(self._check_breach)
        breach_layout.addWidget(self.breach_btn)
        
        self.breach_result = QLabel("")
        self.breach_result.setWordWrap(True)
        breach_layout.addWidget(self.breach_result)
        
        layout.addWidget(breach_group)
        
        layout.addStretch()
    
    def _analyze_password(self, password: str):
        """Analyze the entered password."""
        if not password:
            self.strength_meter.clear()
            return
        
        if not self._generator:
            return
        
        try:
            stats = self._generator.get_password_stats(password)
            self.strength_meter.set_strength(
                stats['strength'],
                stats['entropy'],
                stats
            )
        except Exception as e:
            logger.warning(f"Failed to analyze password: {e}")
    
    def _check_breach(self):
        """Check password against breach database."""
        password = self.password_editor.get_password()
        if not password:
            QMessageBox.warning(self, "No Password", "Please enter a password to check.")
            return
        
        self.breach_btn.setEnabled(False)
        self.breach_btn.setText("Checking...")
        self._breach_ui_state = "checking"
        self.breach_result.setText("Checking breach database...")
        self.breach_result.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')};"
        )
        
        # Run breach check in background thread
        def do_check():
            try:
                is_breached, details = self._generator.check_password_breach(password)
                # Use signal for thread-safe UI update
                self.breach_result_signal.emit(is_breached, details)
            except Exception as e:
                logger.exception("Breach check failed")
                self.breach_result_signal.emit(False, {"error": str(e)})
        
        thread = threading.Thread(target=do_check, daemon=True)
        thread.start()
    
    def _update_breach_result(self, is_breached: bool, details: dict):
        """Update breach check result (called from main thread)."""
        self.breach_btn.setEnabled(True)
        self.breach_btn.setText("Check for breaches")
        
        # Check for error
        if details.get('error'):
            self._breach_ui_state = "error"
            self.breach_result.setText(
                f"Error checking breach status: {details['error']}\n"
                "Please check your internet connection and try again."
            )
            self.breach_result.setStyleSheet(f"color: {theme_manager.get_color('accent_warning')};")
            return
        
        if is_breached:
            self._breach_ui_state = "breached"
            count = details.get('count', 'Unknown')
            self.breach_result.setText(
                f"BREACHED: This password appeared {count:,} times in data breaches.\n"
                "Change it immediately on every account where it is used."
            )
            self.breach_result.setStyleSheet(f"color: {theme_manager.get_color('accent_danger')}; font-weight: bold;")
        else:
            self._breach_ui_state = "safe"
            self.breach_result.setText(
                "Not found in known breach data (Have I Been Pwned).\n"
                "That does not guarantee the password is strong or unique."
            )
            self.breach_result.setStyleSheet(f"color: {theme_manager.get_color('accent_success')};")

    def refresh_theme_styles(self) -> None:
        """Reapply theme-dependent inline styles after global theme change."""
        self.breach_info.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')};"
        )
        state = self._breach_ui_state
        if state == "checking":
            self.breach_result.setStyleSheet(
                f"color: {theme_manager.get_color('text_secondary')};"
            )
        elif state == "error":
            self.breach_result.setStyleSheet(
                f"color: {theme_manager.get_color('accent_warning')};"
            )
        elif state == "breached":
            self.breach_result.setStyleSheet(
                f"color: {theme_manager.get_color('accent_danger')}; font-weight: bold;"
            )
        elif state == "safe":
            self.breach_result.setStyleSheet(
                f"color: {theme_manager.get_color('accent_success')};"
            )
        else:
            self.breach_result.setStyleSheet("")
        self.strength_meter.refresh_from_theme()


class GeneratorWindow(QWidget):
    """
    Main password generator window with tabs.
    """
    
    def __init__(self, generator: SecurePasswordGenerator, parent=None):
        super().__init__(parent)
        self._generator = generator
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.generator_panel = GeneratorPanel(self._generator)
        self.analyzer_panel = AnalyzerPanel(self._generator)

        for panel, title in (
            (self.generator_panel, "Generate"),
            (self.analyzer_panel, "Analyze"),
        ):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            panel.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
            scroll.setWidget(panel)
            self.tabs.addTab(scroll, title)

        layout.addWidget(self.tabs)

    def refresh_theme_styles(self) -> None:
        """Reapply theme-dependent inline styles after global theme change."""
        self.generator_panel.refresh_theme_styles()
        self.analyzer_panel.refresh_theme_styles()
    
    def generate_password(self):
        """Generate a password in the generator panel."""
        self.generator_panel._generate_password()