"""
Embedded CLI terminal: quick commands against the GUI session; optional full PTY shell tab.
"""

from __future__ import annotations

import logging
import os

from pwd_generator.gui import (
    QDialog,
    QDialogButtonBox,
    QFont,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    Qt,
    QTabWidget,
    QTextCursor,
    QThread,
    QVBoxLayout,
    QWidget,
    Signal,
)
from pwd_generator.gui.pty_terminal import PtyTerminalWidget
from pwd_generator.gui.widgets import theme_manager

logger = logging.getLogger(__name__)

# Embedded terminal: arguments only (no horizon-cipher prefix).
CLI_CHEATSHEET = """\
── Shell tab (macOS / Linux) ──
  Full login shell in a PTY: run horizon-cipher, ssh, editors, etc.
  Requires pyte (installed with horizon-cipher[gui]). Not available on Windows.

── Interactive menu (Quick commands cannot run it; use Shell or an external terminal) ──
  interactive
  menu
  (or run horizon-cipher with no arguments)

── Generate ──
  generate -l 20
  generate -t passphrase -w 5
  generate -t pin -l 6
  generate --save --service MySite --notes "optional"
  g -l 16 --no-clipboard

── Saved passwords (history) ──
  history list
  history search gmail
  history show 1
  history export -o backup.json --format json
  history export -o strong.csv -f csv --filter-strength Strong
  history delete 2

── Analyze & breach ──
  analyze "your-password-here"
  breach "password-to-check"

── Batch & audit ──
  batch -c 10 -l 16
  audit
  audit --output report.json --format json

── QR & patterns ──
  qr "text-or-password" -o myqr.png
  pattern "[noun]-[verb]-[2digits]-[1special]"

── Profiles & import ──
  profile list
  profile show banking
  import file.json -f json

── Compare ──
  compare "password-one" "password-two"

── Config ──
  config show

Tip: Type exactly as above; use quotes around values with spaces.
Quick commands: no getpass/interactive prompts. Use the Shell tab for those.
"""


class _EmbeddedCliThread(QThread):
    finished_run = Signal(int, str)

    def __init__(self, line: str, generator, parent=None):
        super().__init__(parent)
        self._line = line
        self._generator = generator

    def run(self):
        from pwd_generator.cli.embedded_cli import run_cli_line_embedded

        try:
            code, text = run_cli_line_embedded(self._line, self._generator)
        except Exception as e:
            logger.exception("Embedded CLI run failed")
            code, text = 1, f"[ERROR] {e}\n"
        self.finished_run.emit(code, text)


class _QuickCommandsPanel(QWidget):
    """Single-line embedded horizon-cipher arguments (vault session)."""

    command_finished = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._generator = None
        self._thread: _EmbeddedCliThread | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        hint = QLabel(
            "Arguments only (no horizon-cipher prefix). "
            "Use Cheatsheet for copy-paste examples."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"font-size: 11px; color: {theme_manager.get_color('text_secondary')};"
        )
        layout.addWidget(hint)

        cheat_btn = QPushButton("Command cheatsheet…")
        cheat_btn.setToolTip("Common CLI commands for this terminal")
        cheat_btn.clicked.connect(self.show_cheatsheet_dialog)
        layout.addWidget(cheat_btn)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setMinimumHeight(120)
        self._output.setMaximumBlockCount(5000)
        mono = QFont("Menlo")
        if not mono.exactMatch():
            mono = QFont("Consolas")
        if not mono.exactMatch():
            mono = QFont("monospace")
        self._output.setFont(mono)
        layout.addWidget(self._output, 1)

        row = QHBoxLayout()
        self._prompt = QLabel("$")
        self._prompt.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')}; font-weight: 600;"
        )
        row.addWidget(self._prompt)
        self._input = QLineEdit()
        self._input.setPlaceholderText("generate -l 16")
        self._input.returnPressed.connect(self._run_line)
        row.addWidget(self._input, 1)
        self._run_btn = QPushButton("Run")
        self._run_btn.clicked.connect(self._run_line)
        row.addWidget(self._run_btn)
        layout.addLayout(row)

        self._cheatsheet_btn = cheat_btn
        self._apply_theme()

    def set_generator(self, generator) -> None:
        self._generator = generator
        enabled = generator is not None
        self._input.setEnabled(enabled)
        self._run_btn.setEnabled(enabled)
        self._cheatsheet_btn.setEnabled(True)

    def refresh_theme_styles(self) -> None:
        self._apply_theme()

    def _apply_theme(self) -> None:
        bg = theme_manager.get_color("background_input")
        fg = theme_manager.get_color("text_primary")
        border = theme_manager.get_color("border_primary")
        self._output.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 8px;
            }}
        """
        )
        self._input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 8px;
            }}
        """
        )

    def show_cheatsheet_dialog(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("CLI command cheatsheet")
        dlg.setMinimumSize(520, 420)
        v = QVBoxLayout(dlg)
        te = QPlainTextEdit()
        te.setReadOnly(True)
        te.setPlainText(CLI_CHEATSHEET)
        te.setFont(self._output.font())
        te.setStyleSheet(self._output.styleSheet())
        v.addWidget(te)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn = box.button(QDialogButtonBox.StandardButton.Close)
        if close_btn is not None:
            close_btn.clicked.connect(dlg.accept)
        box.rejected.connect(dlg.reject)
        v.addWidget(box)
        dlg.exec()

    def append_welcome(self) -> None:
        self._output.appendPlainText(
            "Commands use your unlocked vault. Interactive prompts are not supported here.\n"
        )

    def ensure_welcome_shown(self) -> None:
        if not self._output.toPlainText().strip():
            self.append_welcome()

    def focus_cli_input(self) -> None:
        self._input.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _append(self, text: str) -> None:
        cur = self._output.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        self._output.setTextCursor(cur)
        self._output.insertPlainText(text)

    def _run_line(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        line = self._input.text().strip()
        if not line or self._generator is None:
            return
        self._append(f"$ {line}\n")
        self._input.clear()
        self._run_btn.setEnabled(False)
        self._input.setEnabled(False)
        self._thread = _EmbeddedCliThread(line, self._generator, self)
        self._thread.finished_run.connect(self._on_thread_finished)
        self._thread.start()

    def _on_thread_finished(self, code: int, text: str) -> None:
        if text:
            self._append(text)
            if not text.endswith("\n"):
                self._append("\n")
        if code != 0:
            self._append(f"[Exit code {code}]\n")
        self._run_btn.setEnabled(True)
        self._input.setEnabled(True)
        self.command_finished.emit(code)
        self._thread = None


class CliTerminalPanel(QWidget):
    """Tabs: quick vault-bound commands, and a full PTY shell (Unix + pyte)."""

    command_finished = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        title = QLabel("CLI & shell")
        title.setStyleSheet(
            f"font-weight: 600; color: {theme_manager.get_color('text_primary')};"
        )
        outer.addWidget(title)

        subtitle = QLabel(
            "Quick commands use this window’s vault. The Shell tab is your system login shell."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"font-size: 11px; color: {theme_manager.get_color('text_secondary')};"
        )
        outer.addWidget(subtitle)

        self._tabs = QTabWidget()
        self._quick = _QuickCommandsPanel()
        self._quick.command_finished.connect(self.command_finished.emit)
        self._tabs.addTab(self._quick, "Quick commands")
        self._shell = PtyTerminalWidget(self, cwd=os.path.expanduser("~"))
        self._tabs.addTab(self._shell, "Shell")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        outer.addWidget(self._tabs, 1)

    def _on_tab_changed(self, index: int) -> None:
        if self._tabs.widget(index) is self._shell:
            self._shell.ensure_started()

    def set_generator(self, generator) -> None:
        self._quick.set_generator(generator)

    def refresh_theme_styles(self) -> None:
        self._quick.refresh_theme_styles()
        self._shell.refresh_theme_styles()

    def show_cheatsheet_dialog(self) -> None:
        self._quick.show_cheatsheet_dialog()

    def append_welcome(self) -> None:
        self._quick.append_welcome()

    def ensure_welcome_shown(self) -> None:
        self._quick.ensure_welcome_shown()

    def focus_cli_input(self) -> None:
        self._tabs.setCurrentWidget(self._quick)
        self._quick.focus_cli_input()
