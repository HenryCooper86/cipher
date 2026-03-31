#!/usr/bin/env python3
"""
Horizon Password Generator GUI launcher.

Prefer: horizon-cipher-gui (after pip install -e ".[gui]")
"""

from pwd_generator.entrypoint import main_gui

if __name__ == "__main__":
    main_gui()
