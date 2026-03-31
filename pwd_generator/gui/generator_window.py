"""
Generator view: password generation and analysis (Horizon Cypher).
"""

from pathlib import Path

from pwd_generator.gui import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QLineEdit, QGroupBox, QFrame, QTabWidget, QTextEdit,
    QMessageBox, QFileDialog, QProgressBar, Qt, Signal, QTimer,
    QScrollArea, QSizePolicy, QDialog, QApplication, QImage, QPixmap,
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


class QrCodeDialog(QDialog):
    """Preview, copy, and save a QR code for arbitrary text (e.g. a password)."""

    _MAX_DISPLAY = 320

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QR code")
        self._png_bytes: Optional[bytes] = None
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(200, 200)
        layout.addWidget(self._image_label)
        btn_row = QHBoxLayout()
        self._copy_btn = QPushButton("Copy image")
        self._copy_btn.setToolTip("Copy the QR image to the clipboard")
        self._copy_btn.clicked.connect(self._copy_image)
        self._save_btn = QPushButton("Save as PNG…")
        self._save_btn.setToolTip("Save the QR code as a PNG file")
        self._save_btn.clicked.connect(self._save_png)
        btn_row.addWidget(self._copy_btn)
        btn_row.addWidget(self._save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def set_payload(self, text: str) -> bool:
        from pwd_generator.qr_code import generate_qr_png_bytes

        data = generate_qr_png_bytes(text.strip())
        if not data:
            return False
        self._png_bytes = data
        image = QImage.fromData(data, "PNG")
        if image.isNull():
            return False
        pix = QPixmap.fromImage(image)
        scaled = pix.scaled(
            self._MAX_DISPLAY,
            self._MAX_DISPLAY,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        return True

    def _copy_image(self) -> None:
        if not self._png_bytes:
            return
        image = QImage.fromData(self._png_bytes, "PNG")
        if image.isNull():
            return
        QApplication.clipboard().setPixmap(QPixmap.fromImage(image))

    def _save_png(self) -> None:
        if not self._png_bytes:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save QR code", "", "PNG Images (*.png)"
        )
        if not path:
            return
        out = Path(path)
        if out.suffix.lower() != ".png":
            out = out.with_suffix(".png")
        try:
            out.write_bytes(self._png_bytes)
        except OSError as e:
            QMessageBox.warning(self, "Save failed", str(e))


def show_qr_code_dialog(parent: QWidget, text: str) -> None:
    """Show a QR preview for text, or a message if empty / generation failed."""
    stripped = (text or "").strip()
    if not stripped:
        QMessageBox.information(
            parent,
            "QR code",
            "Generate or enter a password first.",
        )
        return
    dlg = QrCodeDialog(parent)
    if not dlg.set_payload(stripped):
        QMessageBox.warning(
            parent,
            "QR code",
            "Could not create a QR code. Install the qrcode package and try again.",
        )
        return
    dlg.exec()


def save_qr_png_to_file(parent: QWidget, text: str) -> None:
    """Save QR as PNG via file dialog without opening the preview."""
    from pwd_generator.qr_code import generate_qr_png_bytes

    stripped = (text or "").strip()
    if not stripped:
        QMessageBox.information(
            parent,
            "QR code",
            "Generate or enter a password first.",
        )
        return
    data = generate_qr_png_bytes(stripped)
    if not data:
        QMessageBox.warning(
            parent,
            "QR code",
            "Could not create a QR code. Install the qrcode package and try again.",
        )
        return
    path, _ = QFileDialog.getSaveFileName(
        parent, "Save QR code", "", "PNG Images (*.png)"
    )
    if not path:
        return
    out = Path(path)
    if out.suffix.lower() != ".png":
        out = out.with_suffix(".png")
    try:
        out.write_bytes(data)
    except OSError as e:
        QMessageBox.warning(parent, "Save failed", str(e))


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
        
        # Options group (length on row 0; include/charset on row 1; passphrase on row 2)
        options_group = QGroupBox("Options")
        options_layout = QGridLayout(options_group)
        options_layout.setSpacing(12)
        options_layout.setHorizontalSpacing(14)
        options_layout.setVerticalSpacing(10)
        
        options_layout.addWidget(QLabel("Length:"), 0, 0)
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(16)
        options_layout.addWidget(self.length_spin, 0, 1)
        options_layout.setColumnStretch(2, 1)
        
        self.char_options_label = QLabel("Include:")
        char_layout = QHBoxLayout()
        char_layout.setSpacing(16)
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
        char_layout.addStretch(1)

        _charset_cb_min_w = 80
        for cb in (
            self.uppercase_cb,
            self.lowercase_cb,
            self.digits_cb,
            self.special_cb,
        ):
            cb.setSizePolicy(
                QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
            )
            cb.setMinimumWidth(_charset_cb_min_w)

        self._char_options_container = QWidget()
        char_row = QHBoxLayout(self._char_options_container)
        char_row.setContentsMargins(0, 0, 0, 0)
        char_row.setSpacing(12)
        char_row.addWidget(self.char_options_label)
        char_row.addLayout(char_layout, 1)
        self._char_options_container.setMinimumWidth(280)
        options_layout.addWidget(self._char_options_container, 1, 0, 1, 3)
        
        self.words_label = QLabel("Words:")
        self.words_spin = QSpinBox()
        self.words_spin.setRange(4, 10)
        self.words_spin.setValue(5)
        self.separator_label = QLabel("Separator:")
        self.separator_edit = QLineEdit("-")
        self.separator_edit.setMaxLength(3)
        self.separator_edit.setFixedWidth(50)

        self._passphrase_container = QWidget()
        ph_layout = QHBoxLayout(self._passphrase_container)
        ph_layout.setContentsMargins(0, 0, 0, 0)
        ph_layout.setSpacing(12)
        ph_layout.addWidget(self.words_label)
        ph_layout.addWidget(self.words_spin)
        ph_layout.addWidget(self.separator_label)
        ph_layout.addWidget(self.separator_edit)
        ph_layout.addStretch(1)
        options_layout.addWidget(self._passphrase_container, 2, 0, 1, 3)

        self.words_label.hide()
        self.words_spin.hide()
        self.separator_label.hide()
        self.separator_edit.hide()
        self._passphrase_container.hide()
        
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

        qr_row = QHBoxLayout()
        qr_row.setSpacing(8)
        self.show_qr_btn = QPushButton("Show QR code")
        self.show_qr_btn.setToolTip("Encode this password as a scannable QR image")
        self.show_qr_btn.clicked.connect(self._show_qr_code)
        self.save_qr_btn = QPushButton("Save QR as PNG…")
        self.save_qr_btn.setToolTip("Save the QR code to a PNG file")
        self.save_qr_btn.clicked.connect(self._save_qr_code)
        qr_row.addWidget(self.show_qr_btn)
        qr_row.addWidget(self.save_qr_btn)
        qr_row.addStretch()
        display_layout.addLayout(qr_row)
        
        layout.addWidget(display_group)
        
        # Strength meter
        strength_group = QGroupBox("Password Analysis")
        strength_layout = QVBoxLayout(strength_group)
        
        self.strength_meter = StrengthMeter()
        strength_layout.addWidget(self.strength_meter)
        
        layout.addWidget(strength_group)
        
        # Save to history (stacked so label is never clipped on narrow widths)
        save_layout = QVBoxLayout()
        save_layout.setSpacing(10)
        self.save_cb = QCheckBox("Add to Saved Passwords")
        self.save_cb.setChecked(True)
        self.save_cb.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        save_layout.addWidget(self.save_cb)
        service_row = QHBoxLayout()
        service_row.setSpacing(10)
        self.service_label = QLabel("Service:")
        self.service_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        service_row.addWidget(self.service_label)
        self.service_edit = QLineEdit()
        self.service_edit.setPlaceholderText("e.g., gmail, bank, work")
        self.service_edit.setMinimumWidth(200)
        self.service_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        service_row.addWidget(self.service_edit, 1)
        save_layout.addLayout(service_row)
        
        layout.addLayout(save_layout)
        
        # Add stretch to push everything up
        layout.addStretch()
    
    def _on_type_changed(self, index: int):
        """Handle password type change."""
        is_random = index == 0
        is_passphrase = index == 1
        is_pin = index == 2
        
        self._char_options_container.setVisible(is_random)
        self._passphrase_container.setVisible(is_passphrase)
        
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

    def _show_qr_code(self) -> None:
        show_qr_code_dialog(self, self.get_password())

    def _save_qr_code(self) -> None:
        save_qr_png_to_file(self, self.get_password())

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

        qr_row = QHBoxLayout()
        qr_row.setSpacing(8)
        self.show_qr_btn = QPushButton("Show QR code")
        self.show_qr_btn.setToolTip("Encode this password as a scannable QR image")
        self.show_qr_btn.clicked.connect(self._show_qr_code)
        self.save_qr_btn = QPushButton("Save QR as PNG…")
        self.save_qr_btn.setToolTip("Save the QR code to a PNG file")
        self.save_qr_btn.clicked.connect(self._save_qr_code)
        qr_row.addWidget(self.show_qr_btn)
        qr_row.addWidget(self.save_qr_btn)
        qr_row.addStretch()
        layout.addLayout(qr_row)
        
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

    def _show_qr_code(self) -> None:
        show_qr_code_dialog(self, self.password_editor.get_password())

    def _save_qr_code(self) -> None:
        save_qr_png_to_file(self, self.password_editor.get_password())

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

    def open_qr_code_dialog(self, parent: Optional[QWidget] = None) -> None:
        """Show QR for the current Generate or Analyze password (menu / shortcut)."""
        owner = parent or self
        pw = self.generator_panel.get_password().strip()
        if not pw:
            pw = self.analyzer_panel.password_editor.get_password().strip()
        show_qr_code_dialog(owner, pw)