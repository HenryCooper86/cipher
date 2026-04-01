"""
Horizon Cypher GUI module.

A PyQt6/PySide6-based GUI for the password generator.
"""

import os
import sys

# Try PyQt6 first, fall back to PySide6
QT_BACKEND = None
try:
    from PyQt6.QtWidgets import QApplication
    QT_BACKEND = "PyQt6"
except ImportError:
    try:
        from PySide6.QtWidgets import QApplication
        QT_BACKEND = "PySide6"
    except ImportError:
        raise ImportError(
            "No Qt backend found. Please install PyQt6 or PySide6:\n"
            "  pip install PyQt6\n"
            "  or\n"
            "  pip install PySide6"
        )

# Import based on backend
if QT_BACKEND == "PyQt6":
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
    from PyQt6.QtWidgets import *
    # PyQt6 uses pyqtSignal instead of Signal
    Signal = pyqtSignal
    Slot = pyqtSlot
else:
    from PySide6.QtCore import *
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *

__all__ = [
    "QApplication", "QWidget", "QMainWindow", "QDialog",
    "QPushButton", "QLabel", "QLineEdit", "QTextEdit",
    "QVBoxLayout", "QHBoxLayout", "QGridLayout",
    "QComboBox", "QSpinBox", "QCheckBox", "QRadioButton",
    "QTabWidget", "QWidget", "QScrollArea", "QGroupBox",
    "QTableWidget", "QTableWidgetItem", "QHeaderView",
    "QProgressBar", "QSlider", "QFrame", "QSplitter",
    "QMenuBar", "QMenu", "QToolBar", "QStatusBar",
    "QFileDialog", "QMessageBox", "QInputDialog",
    "QSettings", "QTimer", "QThread", "QSize", "QPoint",
    "Qt", "Signal", "Slot", "QFont", "QColor", "QPalette",
    "QIcon", "QPixmap", "QBrush", "QPen",
    "QShortcut", "QKeySequence",
    "QT_BACKEND"
]
