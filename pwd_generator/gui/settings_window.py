"""
Settings Window

Window for configuring application settings and profiles.
"""

from pwd_generator.gui import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QGroupBox, QFrame,
    QSpinBox, QCheckBox, QComboBox, QTabWidget,
    QMessageBox, QFileDialog, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QScrollArea, Qt, QSizePolicy,
)
from pwd_generator.gui.widgets import theme_manager
from pwd_generator import SecurePasswordGenerator
from pwd_generator.config import load_config, save_config, create_default_config
from pwd_generator.profiles import ProfileManager, PasswordProfile
from pwd_generator.constants import DEFAULT_POLICY


class SettingsWindow(QWidget):
    """
    Settings and configuration window.
    
    Features:
    - Theme toggle (Dark/Light)
    - Password policy settings
    - Profile management
    - Import/Export settings
    """
    
    def __init__(self, generator: SecurePasswordGenerator, parent=None):
        super().__init__(parent)
        self._generator = generator
        self._config = load_config()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        for factory, title in (
            (self._create_appearance_tab, "Appearance"),
            (self._create_policy_tab, "Policy"),
            (self._create_profiles_tab, "Profiles"),
        ):
            body = factory()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            body.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
            scroll.setWidget(body)
            self.tabs.addTab(scroll, title)

        layout.addWidget(self.tabs, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        self.save_btn = QPushButton("Save settings")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setMinimumWidth(200)
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
    
    def _create_appearance_tab(self) -> QWidget:
        """Create the appearance settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Color Theme:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(theme_manager.current_theme.capitalize())
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo)
        
        theme_row.addStretch()
        theme_layout.addLayout(theme_row)
        
        self._theme_preview_label = QLabel("Changes will apply immediately")
        self._theme_preview_label.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')}; font-style: italic;"
        )
        theme_layout.addWidget(self._theme_preview_label)
        
        layout.addWidget(theme_group)
        
        # Window group
        window_group = QGroupBox("Window")
        window_layout = QVBoxLayout(window_group)
        
        self.remember_geometry_cb = QCheckBox("Remember window size and position")
        self.remember_geometry_cb.setChecked(True)
        window_layout.addWidget(self.remember_geometry_cb)
        
        self.show_tray_cb = QCheckBox("Show system tray icon (if supported)")
        self.show_tray_cb.setChecked(False)
        window_layout.addWidget(self.show_tray_cb)
        
        layout.addWidget(window_group)
        
        layout.addStretch()
        return widget
    
    def _create_policy_tab(self) -> QWidget:
        """Create the password policy settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Length group
        length_group = QGroupBox("Password Length")
        length_layout = QGridLayout(length_group)
        
        length_layout.addWidget(QLabel("Minimum Length:"), 0, 0)
        self.min_length_spin = QSpinBox()
        self.min_length_spin.setRange(8, 32)
        self.min_length_spin.setValue(self._config.get("policy", {}).get("min_length", DEFAULT_POLICY.get("min_length", 12)))
        length_layout.addWidget(self.min_length_spin, 0, 1)
        
        length_layout.addWidget(QLabel("Maximum Length:"), 0, 2)
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(32, 256)
        self.max_length_spin.setValue(self._config.get("policy", {}).get("max_length", DEFAULT_POLICY.get("max_length", 128)))
        length_layout.addWidget(self.max_length_spin, 0, 3)
        
        length_layout.addWidget(QLabel("Default Length:"), 1, 0)
        self.default_length_spin = QSpinBox()
        self.default_length_spin.setRange(8, 64)
        self.default_length_spin.setValue(16)
        length_layout.addWidget(self.default_length_spin, 1, 1)
        
        layout.addWidget(length_group)
        
        # Character requirements group
        char_group = QGroupBox("Character Requirements")
        char_layout = QVBoxLayout(char_group)
        
        self.require_uppercase_cb = QCheckBox("Require uppercase letters (A-Z)")
        self.require_uppercase_cb.setChecked(self._config.get("policy", {}).get("require_uppercase", True))
        char_layout.addWidget(self.require_uppercase_cb)
        
        self.require_lowercase_cb = QCheckBox("Require lowercase letters (a-z)")
        self.require_lowercase_cb.setChecked(self._config.get("policy", {}).get("require_lowercase", True))
        char_layout.addWidget(self.require_lowercase_cb)
        
        self.require_digits_cb = QCheckBox("Require digits (0-9)")
        self.require_digits_cb.setChecked(self._config.get("policy", {}).get("require_digits", True))
        char_layout.addWidget(self.require_digits_cb)
        
        self.require_special_cb = QCheckBox("Require special characters (!@#$...)")
        self.require_special_cb.setChecked(self._config.get("policy", {}).get("require_special", True))
        char_layout.addWidget(self.require_special_cb)
        
        layout.addWidget(char_group)
        
        # Entropy group
        entropy_group = QGroupBox("Entropy Requirements")
        entropy_layout = QGridLayout(entropy_group)
        
        entropy_layout.addWidget(QLabel("Minimum Entropy (bits):"), 0, 0)
        self.min_entropy_spin = QSpinBox()
        self.min_entropy_spin.setRange(40, 150)
        self.min_entropy_spin.setValue(self._config.get("policy", {}).get("min_entropy", DEFAULT_POLICY.get("min_entropy", 60)))
        entropy_layout.addWidget(self.min_entropy_spin, 0, 1)
        
        layout.addWidget(entropy_group)
        
        # History group
        history_group = QGroupBox("History Settings")
        history_layout = QGridLayout(history_group)
        
        history_layout.addWidget(QLabel("Maximum History Size:"), 0, 0)
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(100, 10000)
        self.max_history_spin.setValue(self._config.get("policy", {}).get("max_history_size", 1000))
        history_layout.addWidget(self.max_history_spin, 0, 1)
        
        history_layout.addWidget(QLabel("Password Expiration (days):"), 1, 0)
        self.expiration_spin = QSpinBox()
        self.expiration_spin.setRange(30, 365)
        self.expiration_spin.setValue(self._config.get("policy", {}).get("expiration_days", DEFAULT_POLICY.get("expiration_days", 90)))
        history_layout.addWidget(self.expiration_spin, 1, 1)
        
        layout.addWidget(history_group)
        
        layout.addStretch()
        return widget
    
    def _create_profiles_tab(self) -> QWidget:
        """Create the profiles management tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(16)
        
        # Profile list
        list_group = QGroupBox("Profiles")
        list_layout = QVBoxLayout(list_group)
        
        self.profile_list = QListWidget()
        self.profile_list.itemSelectionChanged.connect(self._on_profile_selected)
        list_layout.addWidget(self.profile_list)
        
        # Profile buttons
        profile_btn_layout = QHBoxLayout()
        
        self.add_profile_btn = QPushButton("Add profile")
        self.add_profile_btn.setMinimumHeight(38)
        self.add_profile_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.add_profile_btn.clicked.connect(self._add_profile)
        profile_btn_layout.addWidget(self.add_profile_btn, 1)

        self.delete_profile_btn = QPushButton("Delete profile")
        self.delete_profile_btn.setObjectName("dangerButton")
        self.delete_profile_btn.setMinimumHeight(38)
        self.delete_profile_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.delete_profile_btn.clicked.connect(self._delete_profile)
        profile_btn_layout.addWidget(self.delete_profile_btn, 1)
        
        list_layout.addLayout(profile_btn_layout)
        
        layout.addWidget(list_group, 1)
        
        # Profile editor
        editor_group = QGroupBox("Edit Profile")
        editor_layout = QVBoxLayout(editor_group)
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.profile_name_edit = QLineEdit()
        name_layout.addWidget(self.profile_name_edit)
        editor_layout.addLayout(name_layout)
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QGridLayout(settings_group)
        
        settings_layout.addWidget(QLabel("Min Length:"), 0, 0)
        self.profile_min_length_spin = QSpinBox()
        self.profile_min_length_spin.setRange(8, 64)
        settings_layout.addWidget(self.profile_min_length_spin, 0, 1)
        
        settings_layout.addWidget(QLabel("Min Entropy:"), 0, 2)
        self.profile_min_entropy_spin = QSpinBox()
        self.profile_min_entropy_spin.setRange(40, 150)
        settings_layout.addWidget(self.profile_min_entropy_spin, 0, 3)
        
        settings_layout.addWidget(QLabel("Template:"), 1, 0)
        self.profile_template_combo = QComboBox()
        self.profile_template_combo.addItems(["None", "alphanumeric", "numeric_only", "letters_only", "no_special", "url_safe", "readable"])
        settings_layout.addWidget(self.profile_template_combo, 1, 1)
        
        editor_layout.addWidget(settings_group)
        
        # Save profile button
        self.save_profile_btn = QPushButton("Save profile")
        self.save_profile_btn.setObjectName("primaryButton")
        self.save_profile_btn.setMinimumHeight(40)
        self.save_profile_btn.clicked.connect(self._save_profile)
        editor_layout.addWidget(self.save_profile_btn)
        
        editor_layout.addStretch()
        
        layout.addWidget(editor_group, 2)
        
        # Load profiles
        self._load_profiles()
        
        return widget
    
    def _load_profiles(self):
        """Load profiles into the list."""
        self.profile_list.clear()
        
        manager = ProfileManager()
        profiles = manager.list_profiles()
        
        for profile_name in profiles:
            self.profile_list.addItem(profile_name)
    
    def _on_profile_selected(self):
        """Handle profile selection."""
        selected = self.profile_list.currentItem()
        if not selected:
            return
        
        profile_name = selected.text()
        manager = ProfileManager()
        profile = manager.get_profile(profile_name)
        
        if profile:
            self.profile_name_edit.setText(profile.name)
            self.profile_min_length_spin.setValue(profile.policy.get("min_length", 12))
            self.profile_min_entropy_spin.setValue(profile.policy.get("min_entropy", 60))
            self.profile_template_combo.setCurrentText(profile.template or "None")
    
    def _add_profile(self):
        """Add a new profile."""
        self.profile_name_edit.clear()
        self.profile_min_length_spin.setValue(12)
        self.profile_min_entropy_spin.setValue(60)
        self.profile_template_combo.setCurrentIndex(0)
        self.profile_name_edit.setFocus()
    
    def _delete_profile(self):
        """Delete the selected profile."""
        selected = self.profile_list.currentItem()
        if not selected:
            return
        
        profile_name = selected.text()
        
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Delete profile '{profile_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            manager = ProfileManager()
            if manager.delete_profile(profile_name):
                self._load_profiles()
                QMessageBox.information(self, "Deleted", "Profile deleted successfully.")
    
    def _save_profile(self):
        """Save the current profile."""
        name = self.profile_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Profile name is required.")
            return
        
        policy = {
            "min_length": self.profile_min_length_spin.value(),
            "min_entropy": self.profile_min_entropy_spin.value(),
        }
        
        template = self.profile_template_combo.currentText()
        if template == "None":
            template = None
        
        profile = PasswordProfile(name, policy, template)
        
        manager = ProfileManager()
        if manager.add_profile(profile):
            self._load_profiles()
            QMessageBox.information(self, "Saved", "Profile saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to save profile.")
    
    def refresh_theme_styles(self) -> None:
        """Reapply theme-dependent inline styles after global theme change."""
        self._theme_preview_label.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')}; font-style: italic;"
        )
        self.theme_combo.blockSignals(True)
        try:
            self.theme_combo.setCurrentIndex(
                0 if theme_manager.current_theme == "dark" else 1
            )
        finally:
            self.theme_combo.blockSignals(False)

    def _on_theme_changed(self, index: int):
        """Handle theme change."""
        theme_name = "dark" if index == 0 else "light"
        theme_manager.set_theme(theme_name)
        theme_manager.apply_theme(self._get_app())
    
    def _get_app(self):
        """Get the QApplication instance."""
        from pwd_generator.gui import QApplication
        return QApplication.instance()
    
    def _save_settings(self):
        """Save all settings."""
        # Update config
        self._config.setdefault("policy", {})
        
        # Policy settings
        self._config["policy"]["min_length"] = self.min_length_spin.value()
        self._config["policy"]["max_length"] = self.max_length_spin.value()
        self._config["policy"]["default_length"] = self.default_length_spin.value()
        self._config["policy"]["require_uppercase"] = self.require_uppercase_cb.isChecked()
        self._config["policy"]["require_lowercase"] = self.require_lowercase_cb.isChecked()
        self._config["policy"]["require_digits"] = self.require_digits_cb.isChecked()
        self._config["policy"]["require_special"] = self.require_special_cb.isChecked()
        self._config["policy"]["min_entropy"] = self.min_entropy_spin.value()
        self._config["policy"]["max_history_size"] = self.max_history_spin.value()
        self._config["policy"]["expiration_days"] = self.expiration_spin.value()
        
        # Appearance settings
        self._config["theme"] = self.theme_combo.currentText().lower()
        self._config["remember_geometry"] = self.remember_geometry_cb.isChecked()
        
        # Save config
        if save_config(self._config):
            # Update generator policy
            self._generator.policy.update(self._config["policy"])
            
            QMessageBox.information(self, "Saved", "Settings saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings.")