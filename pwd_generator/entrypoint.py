"""Console entry points for installed package (CLI + interactive + GUI)."""

from __future__ import annotations

import logging
import sys


def main() -> None:
    """Run CLI with arguments, or interactive mode when argv has only the program name."""
    try:
        if len(sys.argv) > 1:
            from pwd_generator.cli import main_cli

            main_cli()
        else:
            from pwd_generator.logging_config import setup_logging
            from pwd_generator.paths import default_log_file_path

            setup_logging(str(default_log_file_path()), verbose=False)
            from pwd_generator.interactive import main_interactive

            main_interactive()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error in main")
        print(f"\nFatal error: {e}")
        sys.exit(1)


def main_gui() -> None:
    """Launch the graphical interface (requires optional GUI extra)."""
    from pwd_generator.gui.main_window import run_gui

    sys.exit(run_gui())
