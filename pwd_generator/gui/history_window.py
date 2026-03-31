"""
Password History Window

Window for managing encrypted password history.
"""

from pwd_generator.gui import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QGroupBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QFileDialog, QDialog, QTextEdit, QComboBox,
    QDialogButtonBox, QDateEdit, Qt, QApplication, QClipboard,
    QSizePolicy,
)
from pwd_generator.gui.widgets import theme_manager
from pwd_generator import SecurePasswordGenerator
from pwd_generator.exceptions import HistoryError, EncryptionError
from pwd_generator.gui.widgets.strength_meter import StrengthIndicator
from datetime import datetime
from pathlib import Path


class HistoryWindow(QWidget):
    """
    Password history browser and manager.
    
    Features:
    - View all password entries
    - Search and filter
    - Copy passwords
    - Delete entries
    - Export history
    """
    
    def __init__(self, generator: SecurePasswordGenerator, parent=None):
        super().__init__(parent)
        self._generator = generator
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Search and filter bar
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by service name or notes...")
        self.search_edit.textChanged.connect(self._filter_history)
        search_layout.addWidget(self.search_edit, 1)
        
        # Filter by strength
        filter_label = QLabel("Strength:")
        search_layout.addWidget(filter_label)
        
        self.strength_filter = QComboBox()
        self.strength_filter.addItems(["All", "Weak", "Fair", "Good", "Strong", "Very Strong"])
        self.strength_filter.currentIndexChanged.connect(self._filter_history)
        search_layout.addWidget(self.strength_filter)
        
        layout.addLayout(search_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setMinimumHeight(200)
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Service", "Password", "Strength", "Entropy", "Created"])
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.doubleClicked.connect(self._show_entry_details)
        
        # Set column widths
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.history_table.setColumnWidth(2, 100)
        self.history_table.setColumnWidth(3, 80)
        self.history_table.setColumnWidth(4, 110)
        
        layout.addWidget(self.history_table, 1)
        
        # Action buttons (equal width)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.copy_btn = QPushButton("Copy password")
        self.copy_btn.setMinimumHeight(40)
        self.copy_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.copy_btn.clicked.connect(self._copy_selected_password)
        btn_layout.addWidget(self.copy_btn, 1)

        self.view_btn = QPushButton("View details")
        self.view_btn.setMinimumHeight(40)
        self.view_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.view_btn.clicked.connect(self._show_entry_details)
        btn_layout.addWidget(self.view_btn, 1)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn, 1)

        layout.addLayout(btn_layout)

        export_layout = QHBoxLayout()
        export_layout.setSpacing(10)

        export_label = QLabel("Export:")
        export_layout.addWidget(export_label)

        self.export_json_btn = QPushButton("Export JSON")
        self.export_json_btn.setMinimumHeight(36)
        self.export_json_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.export_json_btn.clicked.connect(lambda: self._export_history("json"))
        export_layout.addWidget(self.export_json_btn, 1)

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.setMinimumHeight(36)
        self.export_csv_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.export_csv_btn.clicked.connect(lambda: self._export_history("csv"))
        export_layout.addWidget(self.export_csv_btn, 1)
        export_layout.addStretch(1)
        
        # Stats label
        self.stats_label = QLabel("Total: 0 entries")
        self.stats_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
        export_layout.addWidget(self.stats_label)
        
        layout.addLayout(export_layout)
    
    def _load_history(self):
        """Load history from the generator."""
        self._populate_table(self._generator.history)
    
    def _populate_table(self, entries: list):
        """Populate the table with history entries."""
        self.history_table.setRowCount(len(entries))
        
        for row, entry in enumerate(entries):
            meta = entry.get("metadata", {})
            
            # Service
            service_item = QTableWidgetItem(meta.get("service", "Unknown"))
            self.history_table.setItem(row, 0, service_item)
            
            # Password (masked)
            password = entry.get("password", "")
            masked = "•" * min(len(password), 16)
            password_item = QTableWidgetItem(masked)
            password_item.setData(Qt.ItemDataRole.UserRole, password)  # Store actual password
            self.history_table.setItem(row, 1, password_item)
            
            # Strength
            strength = meta.get("strength", "-")
            strength_item = QTableWidgetItem(strength)
            strength_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Color code by strength
            strength_colors = {
                "Weak": theme_manager.get_color("strength_weak"),
                "Fair": theme_manager.get_color("strength_fair"),
                "Good": theme_manager.get_color("strength_good"),
                "Strong": theme_manager.get_color("strength_strong"),
                "Very Strong": theme_manager.get_color("strength_very_strong"),
            }
            if strength in strength_colors:
                strength_item.setForeground(Qt.GlobalColor.white)
                strength_item.setBackground(Qt.GlobalColor.darkGray)
            
            self.history_table.setItem(row, 2, strength_item)
            
            # Entropy
            entropy = meta.get("entropy", 0)
            entropy_item = QTableWidgetItem(f"{entropy:.1f} bits")
            entropy_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(row, 3, entropy_item)
            
            # Created
            created = meta.get("created_at", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    created = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            created_item = QTableWidgetItem(created)
            self.history_table.setItem(row, 4, created_item)
        
        self._update_stats(len(entries))
    
    def _filter_history(self):
        """Filter history based on search and strength filter."""
        search = self.search_edit.text().lower()
        strength_filter = self.strength_filter.currentText()
        
        filtered = []
        for entry in self._generator.history:
            meta = entry.get("metadata", {})
            
            # Search filter
            if search:
                service = meta.get("service", "").lower()
                notes = meta.get("notes", "").lower()
                if search not in service and search not in notes:
                    continue
            
            # Strength filter
            if strength_filter != "All":
                if meta.get("strength") != strength_filter:
                    continue
            
            filtered.append(entry)
        
        self._populate_table(filtered)
    
    def _update_stats(self, count: int):
        """Update the stats label."""
        total = len(self._generator.history)
        if count == total:
            self.stats_label.setText(f"Total: {total} entries")
        else:
            self.stats_label.setText(f"Showing: {count} of {total} entries")
    
    def _get_selected_index(self) -> int:
        """Get the index of the selected row."""
        selected = self.history_table.selectedItems()
        if not selected:
            return -1
        return selected[0].row()
    
    def _copy_selected_password(self):
        """Copy the selected password to clipboard."""
        row = self._get_selected_index()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a password entry.")
            return
        
        password_item = self.history_table.item(row, 1)
        password = password_item.data(Qt.ItemDataRole.UserRole)
        
        from pwd_generator.gui import QApplication, QClipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(password)
        
        QMessageBox.information(self, "Copied", "Password copied to clipboard.")
    
    def _show_entry_details(self):
        """Show detailed view of selected entry."""
        row = self._get_selected_index()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a password entry.")
            return
        
        # Get the entry from filtered results
        search = self.search_edit.text().lower()
        strength_filter = self.strength_filter.currentText()
        
        filtered = []
        for entry in self._generator.history:
            meta = entry.get("metadata", {})
            if search:
                service = meta.get("service", "").lower()
                notes = meta.get("notes", "").lower()
                if search not in service and search not in notes:
                    continue
            if strength_filter != "All":
                if meta.get("strength") != strength_filter:
                    continue
            filtered.append(entry)
        
        if row >= len(filtered):
            return
        
        entry = filtered[row]
        dialog = EntryDetailDialog(entry, self)
        dialog.exec()
    
    def _delete_selected(self):
        """Delete the selected entry."""
        row = self._get_selected_index()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a password entry.")
            return
        
        service_item = self.history_table.item(row, 0)
        service = service_item.text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete password for '{service}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Find the actual index in the full history
            search = self.search_edit.text().lower()
            strength_filter = self.strength_filter.currentText()
            
            filtered_indices = []
            for i, entry in enumerate(self._generator.history):
                meta = entry.get("metadata", {})
                if search:
                    service = meta.get("service", "").lower()
                    notes = meta.get("notes", "").lower()
                    if search not in service and search not in notes:
                        continue
                if strength_filter != "All":
                    if meta.get("strength") != strength_filter:
                        continue
                filtered_indices.append(i)
            
            if row < len(filtered_indices):
                actual_index = filtered_indices[row]
                if self._generator.delete_from_history(actual_index):
                    self._load_history()
                    QMessageBox.information(self, "Deleted", "Entry deleted successfully.")
    
    def _export_history(self, format: str):
        """Export history to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export History ({format.upper()})",
            f"password_history.{format}",
            f"{format.upper()} Files (*.{format})"
        )
        
        if not file_path:
            return
        
        try:
            if format == "json":
                from pwd_generator.export import export_history_json
                success = export_history_json(self._generator.history, file_path, include_passwords=True)
            else:
                from pwd_generator.export import export_history_csv
                success = export_history_csv(self._generator.history, file_path, include_passwords=True)
            
            if success:
                QMessageBox.information(self, "Export Complete", f"History exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export history.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
    
    def refresh(self):
        """Refresh the history display."""
        self._load_history()


class EntryDetailDialog(QDialog):
    """Dialog showing detailed entry information."""
    
    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._setup_ui()
    
    def _setup_ui(self):
        meta = self._entry.get("metadata", {})
        
        self.setWindowTitle(f"Password Details - {meta.get('service', 'Unknown')}")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Service
        service_layout = QHBoxLayout()
        service_layout.addWidget(QLabel("Service:"))
        self.service_label = QLabel(meta.get("service", "Unknown"))
        self.service_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        service_layout.addWidget(self.service_label)
        service_layout.addStretch()
        layout.addLayout(service_layout)
        
        # Password
        password_group = QGroupBox("Password")
        password_layout = QVBoxLayout(password_group)
        
        from pwd_generator.gui.widgets.password_display import PasswordDisplay
        self.password_display = PasswordDisplay()
        self.password_display.set_password(self._entry.get("password", ""))
        password_layout.addWidget(self.password_display)
        
        layout.addWidget(password_group)
        
        # Details grid
        details_group = QGroupBox("Details")
        details_layout = QGridLayout(details_group)
        details_layout.setSpacing(8)
        
        row = 0
        details_layout.addWidget(QLabel("Strength:"), row, 0)
        strength_label = QLabel(meta.get("strength", "-"))
        strength_label.setStyleSheet(f"font-weight: bold;")
        details_layout.addWidget(strength_label, row, 1)
        
        row += 1
        details_layout.addWidget(QLabel("Entropy:"), row, 0)
        entropy_label = QLabel(f"{meta.get('entropy', 0):.1f} bits")
        details_layout.addWidget(entropy_label, row, 1)
        
        row += 1
        details_layout.addWidget(QLabel("Created:"), row, 0)
        created = meta.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created)
                created = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        created_label = QLabel(created)
        details_layout.addWidget(created_label, row, 1)
        
        row += 1
        details_layout.addWidget(QLabel("Notes:"), row, 0)
        notes = meta.get("notes", "")
        notes_label = QLabel(notes or "No notes")
        notes_label.setWordWrap(True)
        details_layout.addWidget(notes_label, row, 1)
        
        details_layout.setColumnStretch(1, 1)
        
        layout.addWidget(details_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)