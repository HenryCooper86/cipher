"""
PTY-backed interactive shell for the GUI (Unix). Renders with pyte.
"""

from __future__ import annotations

import logging
import os
import signal
import struct
import subprocess
import sys

from pwd_generator.gui import (
    QColor,
    QEvent,
    QFont,
    QFontMetrics,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSocketNotifier,
    Qt,
    QTextCharFormat,
    QTextCursor,
    QTextEdit,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from pwd_generator.gui.widgets import theme_manager

logger = logging.getLogger(__name__)

# PyQt6 omits QPlainTextEdit.ExtraSelection; QTextEdit.ExtraSelection is the same struct.
_EXTRA_SELECTION_TYPE = getattr(QPlainTextEdit, "ExtraSelection", None) or QTextEdit.ExtraSelection

TERMINAL_FONT_POINT_SIZE = 12


def _cell_to_doc_offset(display_lines: list[str], col: int, row: int) -> int:
    """Character offset in newline-joined display lines for grid cell (col, row)."""
    if not display_lines:
        return 0
    row = max(0, min(row, len(display_lines) - 1))
    offset = sum(len(display_lines[i]) + 1 for i in range(row))
    line = display_lines[row]
    if not line:
        return offset
    # Cursor past last column: highlight last cell (terminal cursor at line end).
    c = min(max(col, 0), len(line) - 1)
    return offset + c


def pty_shell_supported() -> bool:
    if sys.platform == "win32":
        return False
    try:
        import pty as _pty  # noqa: PLC0415

        return hasattr(_pty, "openpty")
    except ImportError:
        return False


def _try_import_pyte():
    try:
        import pyte  # noqa: PLC0415

        return pyte
    except ImportError:
        return None


def _mono_terminal_font(point_size: int = TERMINAL_FONT_POINT_SIZE) -> QFont:
    """Fixed-pitch font for column-aligned terminal output (overrides global UI sans-serif)."""
    for family in (
        "Menlo",
        "Monaco",
        "Consolas",
        "DejaVu Sans Mono",
        "Liberation Mono",
        "Courier New",
        "Courier",
    ):
        f = QFont(family, point_size)
        f.setFixedPitch(True)
        f.setStyleHint(QFont.StyleHint.Monospace, QFont.StyleStrategy.PreferDefault)
        if f.exactMatch():
            return f
    f = QFont()
    f.setPointSize(point_size)
    f.setFixedPitch(True)
    f.setStyleHint(QFont.StyleHint.Monospace, QFont.StyleStrategy.PreferDefault)
    return f


def _pty_make_controlling_tty() -> None:
    """Child pre-exec: attach stdin (slave PTY) as the controlling terminal."""
    import fcntl  # noqa: PLC0415
    import termios  # noqa: PLC0415

    try:
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
    except OSError:
        pass


class PtyTerminalWidget(QWidget):
    """
    Full TTY: user's login shell on a pseudo-terminal, with terminal emulation.
    """

    def __init__(self, parent: QWidget | None = None, cwd: str | None = None) -> None:
        super().__init__(parent)
        self._read_poll: QTimer | None = None
        self._cwd = cwd or os.path.expanduser("~")
        self._pyte = _try_import_pyte()
        self._master: int | None = None
        self._proc: subprocess.Popen | None = None
        self._notifier: QSocketNotifier | None = None
        self._poll: QTimer | None = None
        self._screen = None
        self._stream = None
        self._session_started = False
        self._session_end_announced = False
        self._pty_io_warned = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        if not pty_shell_supported() or self._pyte is None:
            reason = (
                "Integrated shell needs macOS or Linux and the pyte package.\n"
                "Install GUI extras: pip install 'horizon-cipher[gui]'"
                if self._pyte is None and pty_shell_supported()
                else "Integrated shell is not available on this platform (PTY required)."
            )
            self._banner = QLabel(reason)
            self._banner.setWordWrap(True)
            self._banner.setStyleSheet(
                f"color: {theme_manager.get_color('text_secondary')}; padding: 8px;"
            )
            layout.addWidget(self._banner)
            self._out: QPlainTextEdit | None = None
            self._restart_btn = None
            return

        self._banner = None
        row = QHBoxLayout()
        self._restart_btn = QPushButton("New shell")
        self._restart_btn.setToolTip("Start a fresh shell session")
        self._restart_btn.clicked.connect(self._restart_session)
        row.addWidget(self._restart_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self._out = QPlainTextEdit()
        self._out.setObjectName("embeddedTerminalOutput")
        self._out.setReadOnly(True)
        self._out.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._out.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._out.setMinimumHeight(160)
        self._out.setFont(_mono_terminal_font())
        self._out.setCursorWidth(0)
        layout.addWidget(self._out, 1)
        self._out.installEventFilter(self)
        self.refresh_theme_styles()

    def eventFilter(self, obj, event) -> bool:  # type: ignore[no-untyped-def]
        if (
            self._out is not None
            and obj is self._out
            and event.type() == QEvent.Type.MouseButtonPress
        ):
            self.setFocus(Qt.FocusReason.MouseFocusReason)
        return super().eventFilter(obj, event)

    def focusInEvent(self, event) -> None:  # type: ignore[override]
        super().focusInEvent(event)

    def ensure_started(self) -> None:
        if self._out is None:
            return
        if self._session_started:
            return
        self._session_started = True
        self._start_session()

    def refresh_theme_styles(self) -> None:
        if self._out is None:
            return
        bg = theme_manager.get_color("background_input")
        fg = theme_manager.get_color("text_primary")
        border = theme_manager.get_color("border_primary")
        # Force monospace in stylesheet so global QWidget { Segoe UI } does not apply.
        self._out.setStyleSheet(
            f"""
            QPlainTextEdit#embeddedTerminalOutput {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 8px;
                font-family: Menlo, Monaco, Consolas, 'DejaVu Sans Mono',
                    'Liberation Mono', 'Courier New', monospace;
                font-size: {TERMINAL_FONT_POINT_SIZE}px;
            }}
        """
        )
        if self._screen is not None and self._master is not None:
            self._apply_terminal_view()

    def _notify_pty_io_problem(self, message: str) -> None:
        if self._out is None or self._pty_io_warned:
            return
        self._pty_io_warned = True
        self._out.appendPlainText(f"\n[Warning] {message}\n")

    def _pty_write(self, data: bytes) -> bool:
        if self._master is None:
            return False
        try:
            os.write(self._master, data)
            return True
        except OSError as e:
            logger.warning("PTY write failed: %s", e)
            self._notify_pty_io_problem(
                "Could not send input to the shell (session may have ended). "
                'Use "New shell" to start again.'
            )
            return False

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_winsize()
        if self._screen is not None and self._out is not None and self._master is not None:
            self._apply_terminal_view()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if self._master is None:
            super().keyPressEvent(event)
            return

        key = event.key()
        mods = event.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        alt = bool(mods & Qt.KeyboardModifier.AltModifier)

        if ctrl and key == Qt.Key.Key_C:
            self._pty_write(b"\x03")
            event.accept()
            return
        if ctrl and key == Qt.Key.Key_D:
            self._pty_write(b"\x04")
            event.accept()
            return
        if ctrl and Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            ch = key - Qt.Key.Key_A + 1
            self._pty_write(bytes([ch]))
            event.accept()
            return

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self._pty_write(b"\r")
            event.accept()
            return
        if key == Qt.Key.Key_Backspace:
            self._pty_write(b"\x7f")
            event.accept()
            return
        if key == Qt.Key.Key_Tab and not ctrl:
            self._pty_write(b"\t")
            event.accept()
            return
        if key == Qt.Key.Key_Escape:
            self._pty_write(b"\x1b")
            event.accept()
            return
        if key == Qt.Key.Key_Up:
            self._pty_write(b"\x1b[A")
            event.accept()
            return
        if key == Qt.Key.Key_Down:
            self._pty_write(b"\x1b[B")
            event.accept()
            return
        if key == Qt.Key.Key_Right:
            self._pty_write(b"\x1b[C")
            event.accept()
            return
        if key == Qt.Key.Key_Left:
            self._pty_write(b"\x1b[D")
            event.accept()
            return
        if key == Qt.Key.Key_Home:
            seq = b"\x1b[H" if not alt else b"\x1b[1;3H"
            self._pty_write(seq)
            event.accept()
            return
        if key == Qt.Key.Key_End:
            seq = b"\x1b[F" if not alt else b"\x1b[1;3F"
            self._pty_write(seq)
            event.accept()
            return
        if key == Qt.Key.Key_PageUp:
            self._pty_write(b"\x1b[5~")
            event.accept()
            return
        if key == Qt.Key.Key_PageDown:
            self._pty_write(b"\x1b[6~")
            event.accept()
            return
        if key == Qt.Key.Key_Delete:
            self._pty_write(b"\x1b[3~")
            event.accept()
            return

        text = event.text()
        if text and not ctrl:
            try:
                self._pty_write(text.encode("utf-8"))
            except UnicodeEncodeError:
                logger.warning("PTY: could not encode key text as UTF-8")
                self._notify_pty_io_problem(
                    "This character cannot be sent as UTF-8 to the shell."
                )
            event.accept()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._teardown_session()
        super().closeEvent(event)

    def _restart_session(self) -> None:
        if self._out is None:
            return
        self._teardown_session()
        self._start_session()

    def _start_session(self) -> None:
        if self._out is None or self._pyte is None:
            return
        import fcntl  # noqa: PLC0415
        import pty as pty_mod  # noqa: PLC0415
        import termios  # noqa: PLC0415

        self._teardown_session()
        rows, cols = self._terminal_geometry()
        try:
            master, slave = pty_mod.openpty()
        except OSError as e:
            logger.exception("openpty failed")
            self._out.setPlainText(
                f"Could not allocate a pseudo-terminal (openpty): {e}\n\n"
                "Try closing other terminals or restarting the app. On some systems, "
                "running out of PTYs or file descriptors causes this."
            )
            return
        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(slave, termios.TIOCSWINSZ, winsize)
        except OSError as e:
            logger.warning("TIOCSWINSZ failed: %s", e)

        flags = fcntl.fcntl(master, fcntl.F_GETFL)
        fcntl.fcntl(master, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        shell = os.environ.get("SHELL") or "/bin/bash"
        cmd = [shell, "-il"]
        env = os.environ.copy()
        env["TERM"] = env.get("TERM", "xterm-256color")

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                cwd=self._cwd,
                env=env,
                start_new_session=True,
                preexec_fn=_pty_make_controlling_tty,
            )
        except OSError as e:
            logger.exception("Failed to start shell")
            self._out.setPlainText(
                f"Could not start shell ({shell!r}): {e}\n\n"
                "Check that SHELL is set correctly and that the shell binary exists "
                "and is executable."
            )
            try:
                os.close(master)
            except OSError:
                pass
            try:
                os.close(slave)
            except OSError:
                pass
            return

        os.close(slave)
        self._master = master
        self._proc = proc
        self._pty_io_warned = False
        self._session_end_announced = False
        self._screen = self._pyte.Screen(cols, rows)
        self._stream = self._pyte.Stream(self._screen)
        self._notifier = QSocketNotifier(master, QSocketNotifier.Type.Read)
        self._notifier.activated.connect(self._on_master_readable)
        self._poll = QTimer(self)
        self._poll.timeout.connect(self._check_proc)
        self._poll.start(400)
        self._read_poll = QTimer(self)
        self._read_poll.timeout.connect(self._drain_pty_via_timer)
        self._read_poll.start(25)
        self._out.setPlainText("")
        self._out.setExtraSelections([])
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _terminal_geometry(self) -> tuple[int, int]:
        if self._out is None:
            return 24, 80
        fm = QFontMetrics(self._out.font())
        char_w = max(1, fm.horizontalAdvance("M"))
        char_h = max(1, fm.height())
        w = max(40, self._out.width() - 24)
        h = max(40, self._out.height() - 24)
        cols = max(40, w // char_w)
        rows = max(8, h // char_h)
        return rows, cols

    def _apply_winsize(self) -> None:
        if self._master is None or self._screen is None:
            return
        import fcntl  # noqa: PLC0415
        import termios  # noqa: PLC0415

        rows, cols = self._terminal_geometry()
        self._screen.resize(rows, cols)
        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self._master, termios.TIOCSWINSZ, winsize)
        except OSError as e:
            logger.debug("winsize ioctl: %s", e)
        if self._proc and self._proc.pid:
            try:
                os.kill(self._proc.pid, signal.SIGWINCH)
            except (OSError, ProcessLookupError):
                pass

    def _apply_terminal_view(self) -> None:
        """Scroll to pyte cursor and draw a block cursor via extra selections."""
        if self._out is None or self._screen is None:
            return
        display = self._screen.display
        plain = "\n".join(display)
        if not plain:
            self._out.setExtraSelections([])
            return
        cx = int(self._screen.cursor.x)
        cy = int(self._screen.cursor.y)
        off = _cell_to_doc_offset(display, cx, cy)
        doc = self._out.document()
        char_count = doc.characterCount()
        if char_count <= 1 or not plain:
            return
        # Positions 0 .. len(plain)-1 map to content; QTextDocument adds one block separator.
        off = min(max(off, 0), len(plain) - 1)
        end = off + 1
        if end > char_count:
            end = char_count
        if end <= off:
            return

        fmt = QTextCharFormat()
        bg = QColor(theme_manager.get_color("accent_primary"))
        fg = QColor(theme_manager.get_color("background_input"))
        fmt.setBackground(bg)
        fmt.setForeground(fg)

        sel = _EXTRA_SELECTION_TYPE()
        cur = QTextCursor(doc)
        cur.setPosition(off)
        cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        sel.cursor = cur
        sel.format = fmt
        self._out.setExtraSelections([sel])

        scroll_cur = QTextCursor(doc)
        scroll_cur.setPosition(off)
        self._out.setTextCursor(scroll_cur)
        self._out.ensureCursorVisible()

    def _drain_pty_via_timer(self) -> None:
        self._drain_pty_output()

    def _on_master_readable(self) -> None:
        self._drain_pty_output()

    def _drain_pty_output(self) -> None:
        if (
            self._master is None
            or self._stream is None
            or self._screen is None
            or self._out is None
        ):
            return
        while True:
            try:
                chunk = os.read(self._master, 65536)
            except BlockingIOError:
                break
            except OSError as e:
                logger.debug("read master: %s", e)
                break
            if not chunk:
                self._handle_proc_exit()
                break
            self._stream.feed(chunk.decode("utf-8", errors="replace"))
            plain = "\n".join(self._screen.display)
            self._out.setPlainText(plain)
            self._apply_terminal_view()

    def _check_proc(self) -> None:
        if self._proc is None:
            return
        code = self._proc.poll()
        if code is not None:
            self._handle_proc_exit()

    def _handle_proc_exit(self) -> None:
        if self._proc is None:
            return
        if self._proc.poll() is None:
            return
        if self._out is not None and not self._session_end_announced:
            self._session_end_announced = True
            exit_code = self._proc.poll()
            if exit_code is not None:
                self._out.appendPlainText(f"\n[Session ended — exit code {exit_code}]\n")
            else:
                self._out.appendPlainText("\n[Session ended]\n")
        self._teardown_session()

    def _teardown_session(self) -> None:
        if self._read_poll is not None:
            self._read_poll.stop()
            self._read_poll.deleteLater()
            self._read_poll = None
        if self._poll is not None:
            self._poll.stop()
            self._poll.deleteLater()
            self._poll = None
        if self._notifier is not None:
            self._notifier.setEnabled(False)
            self._notifier.deleteLater()
            self._notifier = None
        if self._proc is not None:
            try:
                os.killpg(self._proc.pid, signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(self._proc.pid, signal.SIGKILL)
                except (OSError, ProcessLookupError):
                    pass
            self._proc = None
        if self._master is not None:
            try:
                os.close(self._master)
            except OSError:
                pass
            self._master = None
        self._screen = None
        self._stream = None
        if self._out is not None:
            self._out.setExtraSelections([])
