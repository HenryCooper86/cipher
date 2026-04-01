"""
Password History Window

Window for managing encrypted password history.
"""

from datetime import datetime

from pwd_generator import SecurePasswordGenerator
from pwd_generator.gui import (
    QAbstractItemView,
    QApplication,
    QBrush,
    QCheckBox,
    QColor,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from pwd_generator.gui.widgets import theme_manager

# Column indices (0 = checkbox)
COL_SELECT = 0
COL_SERVICE = 1
COL_PASSWORD = 2
COL_STRENGTH = 3
COL_ENTROPY = 4
COL_CREATED = 5

# Service cell stores vault index in full history (for filtered views)
HISTORY_INDEX_ROLE = Qt.ItemDataRole.UserRole + 1


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

        # History table (column 0 = checkbox)
        self.history_table = QTableWidget()
        self.history_table.setMinimumHeight(200)
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["", "Service", "Password", "Strength", "Entropy", "Created"]
        )
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.doubleClicked.connect(self._on_table_double_clicked)
        self.history_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(COL_SELECT, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COL_SERVICE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_PASSWORD, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_STRENGTH, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COL_ENTROPY, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COL_CREATED, QHeaderView.ResizeMode.Fixed)

        self.history_table.setColumnWidth(COL_SELECT, 76)
        self.history_table.setColumnWidth(COL_STRENGTH, 100)
        self.history_table.setColumnWidth(COL_ENTROPY, 88)
        self.history_table.setColumnWidth(COL_CREATED, 130)

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
        pairs = list(enumerate(self._generator.history))
        self._populate_table(pairs)

    def _filtered_pairs(self) -> list:
        """Return [(history_index, entry), ...] matching current filters."""
        search = self.search_edit.text().lower()
        strength_filter = self.strength_filter.currentText()
        pairs = []
        for hist_idx, entry in enumerate(self._generator.history):
            meta = entry.get("metadata", {})
            if search:
                service = meta.get("service", "").lower()
                notes = meta.get("notes", "").lower()
                if search not in service and search not in notes:
                    continue
            if strength_filter != "All":
                if meta.get("strength") != strength_filter:
                    continue
            pairs.append((hist_idx, entry))
        return pairs

    def _populate_table(self, pairs: list) -> None:
        """Populate rows from (history_index, entry) pairs."""
        self.history_table.setRowCount(0)
        self.history_table.setRowCount(len(pairs))

        for row, (hist_idx, entry) in enumerate(pairs):
            meta = entry.get("metadata", {})

            box_host = QWidget()
            box_host.setObjectName("historyCheckboxHost")
            box_host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            hl = QHBoxLayout(box_host)
            hl.setContentsMargins(4, 2, 4, 2)
            hl.addStretch()
            cb = QCheckBox()
            cb.setText("")
            cb.setToolTip("Select this entry")
            hl.addWidget(cb, 0, Qt.AlignmentFlag.AlignCenter)
            hl.addStretch()
            self.history_table.setCellWidget(row, COL_SELECT, box_host)

            service_item = QTableWidgetItem(meta.get("service", "Unknown"))
            service_item.setData(HISTORY_INDEX_ROLE, hist_idx)
            self.history_table.setItem(row, COL_SERVICE, service_item)

            password = entry.get("password", "")
            masked = "•" * min(len(password), 16)
            password_item = QTableWidgetItem(masked)
            password_item.setData(Qt.ItemDataRole.UserRole, password)
            self.history_table.setItem(row, COL_PASSWORD, password_item)

            strength = meta.get("strength", "-")
            strength_item = QTableWidgetItem(strength)
            strength_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            strength_colors = {
                "Weak": theme_manager.get_color("strength_weak"),
                "Fair": theme_manager.get_color("strength_fair"),
                "Good": theme_manager.get_color("strength_good"),
                "Strong": theme_manager.get_color("strength_strong"),
                "Very Strong": theme_manager.get_color("strength_very_strong"),
            }
            if strength in strength_colors:
                hex_bg = strength_colors[strength]
                strength_item.setBackground(QBrush(QColor(hex_bg)))
                strength_item.setForeground(
                    QBrush(QColor(theme_manager.get_color("strength_badge_text")))
                )
            self.history_table.setItem(row, COL_STRENGTH, strength_item)

            entropy = meta.get("entropy", 0)
            entropy_item = QTableWidgetItem(f"{entropy:.1f} bits")
            entropy_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(row, COL_ENTROPY, entropy_item)

            created = meta.get("created_at", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    created = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
            created_item = QTableWidgetItem(created)
            self.history_table.setItem(row, COL_CREATED, created_item)

        self._update_stats(len(pairs))
        self.history_table.resizeColumnToContents(COL_SERVICE)

    def _filter_history(self):
        """Filter history based on search and strength filter."""
        self._populate_table(self._filtered_pairs())

    def _get_checkbox_at_row(self, row: int):
        host = self.history_table.cellWidget(row, COL_SELECT)
        if host is None:
            return None
        return host.findChild(QCheckBox)

    def _checked_rows(self) -> list:
        rows = []
        for r in range(self.history_table.rowCount()):
            cb = self._get_checkbox_at_row(r)
            if cb is not None and cb.isChecked():
                rows.append(r)
        return rows

    def _history_index_for_row(self, row: int):
        it = self.history_table.item(row, COL_SERVICE)
        if it is None:
            return None
        v = it.data(HISTORY_INDEX_ROLE)
        return int(v) if v is not None else None

    def _resolve_single_action_row(self) -> int:
        """One table row: single checked box, or exactly one selected row."""
        checked = self._checked_rows()
        if len(checked) == 1:
            return checked[0]
        if len(checked) > 1:
            QMessageBox.warning(
                self,
                "Multiple selected",
                "Use one checked row, or uncheck all and select a single row.",
            )
            return -1
        selected = self.history_table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self,
                "No selection",
                "Select a row or check exactly one entry.",
            )
            return -1
        rows = {it.row() for it in selected}
        if len(rows) != 1:
            QMessageBox.warning(
                self,
                "No selection",
                "Select a single row.",
            )
            return -1
        return next(iter(rows))

    def _on_table_double_clicked(self, index):
        if index.column() == COL_SELECT:
            return
        self._show_entry_details_for_row(index.row())

    def _show_entry_details_for_row(self, row: int):
        hist_idx = self._history_index_for_row(row)
        if hist_idx is None:
            return
        if hist_idx < 0 or hist_idx >= len(self._generator.history):
            return
        entry = self._generator.history[hist_idx]
        dialog = EntryDetailDialog(entry, self)
        dialog.exec()

    def _update_stats(self, count: int):
        """Update the stats label."""
        total = len(self._generator.history)
        if count == total:
            self.stats_label.setText(f"Total: {total} entries")
        else:
            self.stats_label.setText(f"Showing: {count} of {total} entries")

    def _copy_selected_password(self):
        """Copy password from the single checked or selected row."""
        row = self._resolve_single_action_row()
        if row < 0:
            return

        password_item = self.history_table.item(row, COL_PASSWORD)
        if password_item is None:
            return
        password = password_item.data(Qt.ItemDataRole.UserRole)
        clipboard = QApplication.clipboard()
        clipboard.setText(password)

        QMessageBox.information(self, "Copied", "Password copied to clipboard.")

    def _show_entry_details(self):
        """Show detailed view of selected entry."""
        row = self._resolve_single_action_row()
        if row < 0:
            return
        self._show_entry_details_for_row(row)

    def _delete_selected(self):
        """Delete checked entries (batch) or one selected row."""
        checked_rows = self._checked_rows()
        if checked_rows:
            indices = sorted(
                {
                    self._history_index_for_row(r)
                    for r in checked_rows
                    if self._history_index_for_row(r) is not None
                },
                reverse=True,
            )
            if not indices:
                return
            n = len(indices)
            reply = QMessageBox.question(
                self,
                "Confirm delete",
                f"Delete {n} password entr{'y' if n == 1 else 'ies'}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            for idx in indices:
                self._generator.delete_from_history(idx)
            self._load_history()
            QMessageBox.information(self, "Deleted", "Selected entries removed.")
            return

        row = self._resolve_single_action_row()
        if row < 0:
            return

        service_item = self.history_table.item(row, COL_SERVICE)
        service = service_item.text() if service_item else "entry"
        hist_idx = self._history_index_for_row(row)
        if hist_idx is None:
            return

        reply = QMessageBox.question(
            self,
            "Confirm delete",
            f"Delete password for '{service}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._generator.delete_from_history(hist_idx):
                self._load_history()
                QMessageBox.information(self, "Deleted", "Entry deleted successfully.")

    def _export_history(self, format: str):
        """Export history to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Saved Passwords ({format.upper()})",
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
                QMessageBox.information(
                    self, "Export Complete", f"Saved passwords exported to {file_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Export Failed", "Failed to export saved passwords."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def refresh_theme_styles(self) -> None:
        """Reapply theme-dependent inline styles (e.g. after global theme change)."""
        self.stats_label.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')};"
        )
        self._populate_table(self._filtered_pairs())

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
        strength_label.setStyleSheet("font-weight: bold;")
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
