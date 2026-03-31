"""
Application and UI icons (rendered with Qt, cached on disk for stylesheets).
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Dict, Optional

try:
    from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
    from PyQt6.QtGui import QPainterPath
except ImportError:
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtGui import QPainterPath

from pwd_generator.gui import (
    QBrush,
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRectF,
    Qt,
    QUrl,
)


def _cache_dir() -> Path:
    d = Path(tempfile.gettempdir()) / "horizon_pm_gui_assets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _checkbox_checked_colors(
    theme: str, colors: Dict[str, str]
) -> tuple:
    inner = QColor(colors.get("checkbox_checked_bg", colors["background_input"]))
    border = QColor(colors.get("checkbox_checked_border", colors["border_focus"]))
    tick = QColor(
        colors.get(
            "checkbox_tick",
            "#ffffff" if theme == "dark" else "#1a3d6e",
        )
    )
    return inner, border, tick


def _make_checkbox_checked_pixmap(
    inner: QColor,
    border: QColor,
    tick: QColor,
) -> QPixmap:
    dpr = 4
    base = 18
    sz = base * dpr
    pm = QPixmap(sz, sz)
    # Opaque base: transparent corners blend away the tick on dark UIs.
    pm.fill(inner)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    m = 1.5 * dpr
    rect = QRectF(m, m, sz - 2 * m, sz - 2 * m)
    r = 4 * dpr
    p.setPen(QPen(border, max(1, dpr)))
    p.setBrush(QBrush(inner))
    p.drawRoundedRect(rect, r, r)

    tw = max(3, int(3.25 * dpr))
    p.setPen(
        QPen(
            tick,
            tw,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    x0, y0 = 3.9 * dpr, 9.1 * dpr
    x1, y1 = 7.85 * dpr, 12.85 * dpr
    x2, y2 = 14.35 * dpr, 5.35 * dpr
    p.drawLine(int(x0), int(y0), int(x1), int(y1))
    p.drawLine(int(x1), int(y1), int(x2), int(y2))

    p.end()
    return pm


def _make_checkbox_tick_only_pixmap(tick: QColor) -> QPixmap:
    """Transparent 18×18 (at DPR) canvas with only the check mark strokes."""
    dpr = 4
    base = 18
    sz = base * dpr
    pm = QPixmap(sz, sz)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    tw = max(3, int(3.25 * dpr))
    p.setPen(
        QPen(
            tick,
            tw,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    x0, y0 = 3.9 * dpr, 9.1 * dpr
    x1, y1 = 7.85 * dpr, 12.85 * dpr
    x2, y2 = 14.35 * dpr, 5.35 * dpr
    p.drawLine(int(x0), int(y0), int(x1), int(y1))
    p.drawLine(int(x1), int(y1), int(x2), int(y2))
    p.end()
    return pm


def _pixmap_png_data_uri(pm: QPixmap) -> Optional[str]:
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    ok = pm.save(buf, b"PNG")
    if not ok:
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        ok = pm.save(buf, "PNG")
    if not ok:
        return None
    b64 = base64.standard_b64encode(bytes(ba)).decode("ascii")
    return f'url("data:image/png;base64,{b64}")'


def combobox_down_arrow_qss_image(colors: Dict[str, str]) -> str:
    """
    Data-URI PNG for QComboBox::down-arrow (Fusion breaks CSS border triangles).
    Transparent background; chevron uses text_primary.
    """
    fg = QColor(colors["text_primary"])
    dpr = 3
    w, h = 12, 8
    szw, szh = w * dpr, h * dpr
    pm = QPixmap(szw, szh)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen_w = max(2, int(1.75 * dpr))
    p.setPen(
        QPen(
            fg,
            pen_w,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    m = 2.0 * dpr
    cx = szw / 2.0
    y1 = m
    xl, xr = m, szw - m
    y2 = szh - m
    p.drawLine(int(xl), int(y1), int(cx), int(y2))
    p.drawLine(int(cx), int(y2), int(xr), int(y1))
    p.end()
    uri = _pixmap_png_data_uri(pm)
    if uri is not None:
        return uri
    return ""


def checkbox_tick_only_qss_image(theme: str, colors: Dict[str, str]) -> str:
    """
    PNG data URI for QSS `image:` — tick only, for use over QSS-drawn checked box fill.
    Returns empty string if encoding fails (caller should fall back to full composite).
    """
    _, _, tick = _checkbox_checked_colors(theme, colors)
    pm = _make_checkbox_tick_only_pixmap(tick)
    uri = _pixmap_png_data_uri(pm)
    return uri if uri is not None else ""


def checkbox_indicator_checked_qss_image(theme: str, colors: Dict[str, str]) -> str:
    """
    Value for QSS `image:` — embeds PNG as data URI so `file://` paths are not required.
    Qt stylesheets often fail to load local file URLs on macOS; data URIs are reliable.
    """
    inner, border, tick = _checkbox_checked_colors(theme, colors)
    pm = _make_checkbox_checked_pixmap(inner, border, tick)
    uri = _pixmap_png_data_uri(pm)
    if uri is not None:
        return uri
    return f'url("{checkbox_indicator_checked_url(theme, colors)}")'


def checkbox_indicator_checked_url(theme: str, colors: Dict[str, str]) -> str:
    """
    PNG path as file URL (fallback if in-memory encoding fails).
    """
    inner, border, tick = _checkbox_checked_colors(theme, colors)
    key = f"cb4_{theme}_{inner.name()}_{border.name()}_{tick.name()}.png"
    path = _cache_dir() / key
    if not path.exists():
        _render_checkbox_checked_png(path, inner, border, tick)
    return QUrl.fromLocalFile(str(path.resolve())).toString()


def _render_checkbox_checked_png(
    path: Path,
    inner: QColor,
    border: QColor,
    tick: QColor,
) -> None:
    pm = _make_checkbox_checked_pixmap(inner, border, tick)
    pm.save(str(path), "PNG")


def radio_indicator_checked_url(theme: str, colors: Dict[str, str]) -> str:
    """Ring + center dot instead of solid fill."""
    accent = QColor(colors["accent_primary"])
    border = QColor(colors["border_focus"])
    inner = QColor(colors["background_input"])
    dot = QColor(colors["accent_primary"])
    if theme == "light":
        dot = dot.darker(120)

    key = f"rb_{theme}_{inner.name()}_{accent.name()}.png"
    path = _cache_dir() / key
    if not path.exists():
        _render_radio_checked_png(path, inner, border, accent, dot)
    return QUrl.fromLocalFile(str(path.resolve())).toString()


def _render_radio_checked_png(
    path: Path,
    inner: QColor,
    border: QColor,
    _accent: QColor,
    dot: QColor,
) -> None:
    dpr = 4
    sz = 18 * dpr
    pm = QPixmap(sz, sz)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    m = 1.5 * dpr
    rect = QRectF(m, m, sz - 2 * m, sz - 2 * m)
    p.setPen(QPen(border, max(1, dpr)))
    p.setBrush(QBrush(inner))
    p.drawEllipse(rect)

    cx, cy = sz / 2, sz / 2
    rad = 4.5 * dpr
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(dot))
    p.drawEllipse(QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad))
    p.end()
    pm.save(str(path), "PNG")


def create_application_icon() -> QIcon:
    """
    Window / taskbar icon: rounded tile with padlock (cypher / vault motif).
    """
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pm = _render_app_icon_pixmap(size)
        icon.addPixmap(pm, QIcon.Mode.Normal, QIcon.State.Off)
    return icon


def _render_app_icon_pixmap(size: int) -> QPixmap:
    """Rounded blue tile with padlock + keyhole (readable from 16px)."""
    s = max(size, 16)
    pm = QPixmap(s, s)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    margin = s * 0.08
    r = s - 2 * margin
    grad = QLinearGradient(margin, margin, margin + r, margin + r)
    grad.setColorAt(0.0, QColor("#6b9eef"))
    grad.setColorAt(1.0, QColor("#3a5f9e"))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(margin, margin, r, r), s * 0.2, s * 0.2)

    cx = s / 2
    fg = QColor("#f0f4fc")
    deep = QColor("#2a4a84")

    bw = s * 0.38
    bh = s * 0.32
    bx = cx - bw / 2
    by = s * 0.505
    body_rr = max(1.5, s * 0.045)

    # Lock body
    p.setBrush(QBrush(fg))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(bx, by, bw, bh), body_rr, body_rr)

    # Keyhole (cypher cue); skip on tiny sizes so silhouette stays clear
    if s >= 20:
        p.setBrush(QBrush(deep))
        kh_r = s * 0.055
        kcy = by + bh * 0.34
        p.drawEllipse(QRectF(cx - kh_r, kcy - kh_r, 2 * kh_r, 2 * kh_r))
        slot_w = max(2.0, s * 0.07)
        slot_h = bh * 0.38
        p.drawRoundedRect(
            QRectF(cx - slot_w / 2, kcy + kh_r * 0.35, slot_w, slot_h),
            slot_w * 0.35,
            slot_w * 0.35,
        )

    # Shackle (stroke over body top)
    sh_w = bw * 0.78
    sh_h = bh * 1.05
    arc_rect = QRectF(cx - sh_w / 2, by - sh_h * 0.68, sh_w, sh_h * 1.2)
    lw = max(1.6, s * 0.085)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(
        QPen(
            fg,
            lw,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    shackle = QPainterPath()
    lx = bx + bw * 0.2
    rx = bx + bw * 0.8
    shackle.moveTo(lx, by + lw * 0.15)
    shackle.arcTo(arc_rect, 180.0, -180.0)
    shackle.lineTo(rx, by + lw * 0.15)
    p.drawPath(shackle)

    p.end()
    return pm
