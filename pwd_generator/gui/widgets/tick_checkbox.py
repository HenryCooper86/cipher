"""
Clickable checkbox drawn with QPainter (no QSS `image:`), for hosts where
Qt ignores indicator images (common on macOS + native styles).
"""

from __future__ import annotations

from pwd_generator.gui import (
    QWidget,
    Qt,
    QPainter,
    QPainterPath,
    QPen,
    QBrush,
    QColor,
    QRectF,
    Signal,
)
from pwd_generator.gui.widgets.theme import theme_manager


class TickCheckBox(QWidget):
    """Minimal QCheckBox-like control with reliable dark/light painting."""

    stateChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(22, 22)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        want = bool(checked)
        if self._checked == want:
            return
        self._checked = want
        self.update()
        self.stateChanged.emit(
            Qt.CheckState.Checked.value if want else Qt.CheckState.Unchecked.value
        )

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self.setChecked(not self._checked)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (
            Qt.Key.Key_Space,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            self.setChecked(not self._checked)
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        rect = outer.adjusted(2, 2, -2, -2)
        rr = 4.0

        if self._checked:
            bg = QColor(theme_manager.get_color("checkbox_checked_bg"))
            border = QColor(theme_manager.get_color("checkbox_checked_border"))
            tick = QColor(theme_manager.get_color("checkbox_tick"))
        else:
            bg = QColor(theme_manager.get_color("checkbox_unchecked_bg"))
            border = QColor(theme_manager.get_color("checkbox_unchecked_border"))

        p.setPen(QPen(border, 2))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(rect, rr, rr)

        if self._checked:
            inset = min(rect.width(), rect.height()) * 0.24
            r = rect.adjusted(inset, inset, -inset, -inset)
            if r.width() < 4 or r.height() < 4:
                r = rect
            # Single open path: no overlapping segment caps at the knee (avoids “blob”).
            x0 = r.left() + r.width() * 0.12
            y0 = r.top() + r.height() * 0.52
            x1 = r.left() + r.width() * 0.40
            y1 = r.bottom() - r.height() * 0.12
            x2 = r.right() - r.width() * 0.10
            y2 = r.top() + r.height() * 0.22
            path = QPainterPath()
            path.moveTo(x0, y0)
            path.lineTo(x1, y1)
            path.lineTo(x2, y2)
            pen = QPen(
                tick,
                1.85,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            p.strokePath(path, pen)

        if self.hasFocus():
            fc = QColor(theme_manager.get_color("border_focus"))
            p.setPen(QPen(fc, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(outer, rr + 1, rr + 1)
