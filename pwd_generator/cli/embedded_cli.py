"""
Run horizon-cipher CLI commands in-process using an existing SecurePasswordGenerator
(GUI embedded terminal). Captures stdout/stderr; maps sys.exit to a return code.
"""

from __future__ import annotations

import logging
import os
import shlex
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING

from pwd_generator.cli.errors import format_cli_error_text
from pwd_generator.exceptions import (
    EncryptionError,
    FileOperationError,
    HistoryError,
    PasswordGeneratorError,
    ValidationError,
)

if TYPE_CHECKING:
    from pwd_generator import SecurePasswordGenerator

logger = logging.getLogger(__name__)

_EMBEDDED_NO_INTERACTIVE_MSG = (
    "The full interactive menu needs a real terminal (TTY).\n"
    "From a shell, run one of:\n"
    "  horizon-cipher\n"
    "  horizon-cipher interactive\n"
    "  python cipher.py\n"
    "(This panel only runs single commands like: generate -l 20)\n"
)


def run_cli_line_embedded(
    line: str, generator: SecurePasswordGenerator
) -> tuple[int, str]:
    """
    Parse a single command line (like shell args, no program name) and execute
    using the same vault/session as the GUI. Not a full TTY; interactive prompts
    in handlers will not work.

    Returns:
        (exit_code, combined stdout/stderr text)
    """
    class CliExit(Exception):
        __slots__ = ("code",)

        def __init__(self, code: int = 0):
            self.code = code
            super().__init__()

    def fake_exit(code=0):
        if isinstance(code, str):
            print(code, file=sys.stderr)
            raise CliExit(1)
        if code is None:
            raise CliExit(0)
        raise CliExit(int(code))

    try:
        tokens = shlex.split(line, posix=os.name != "nt")
    except ValueError as e:
        return 1, f"{e}\n"

    if not tokens:
        return 0, ""

    buf = StringIO()
    old_exit = sys.exit
    sys.exit = fake_exit
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            from pwd_generator.cli.parser import create_parser

            parser = create_parser()
            try:
                args = parser.parse_args(tokens)
            except SystemExit as e:
                ec = e.code
                if ec is None:
                    ec = 0
                elif not isinstance(ec, int):
                    ec = 1
                return ec, buf.getvalue()

            cmd = getattr(args, "command", None)
            if cmd in ("interactive", "menu"):
                return 1, _EMBEDDED_NO_INTERACTIVE_MSG
            if not cmd:
                parser.print_help()
                return 0, buf.getvalue()

            from pwd_generator.cli import dispatch_cli_command
            from pwd_generator.cli.core import setup_logging
            from pwd_generator.paths import default_log_file_path

            setup_logging(str(default_log_file_path()), verbose=False)
            dispatch_cli_command(args, generator, parser)
    except CliExit as e:
        return e.code, buf.getvalue()
    except SystemExit as e:
        ec = e.code
        if ec is None:
            ec = 0
        elif not isinstance(ec, int):
            ec = 1
        return ec, buf.getvalue()
    except (
        ValidationError,
        FileOperationError,
        HistoryError,
        EncryptionError,
        ValueError,
        PasswordGeneratorError,
    ) as e:
        msg = format_cli_error_text(e)
        suffix = msg if msg else f"[ERROR] {e}\n"
        return 1, buf.getvalue() + suffix
    except Exception as e:
        logger.exception("Embedded CLI unexpected error")
        return (
            1,
            buf.getvalue()
            + "[ERROR] An unexpected error occurred.\n"
            + f"        ({type(e).__name__}) {e}\n",
        )
    finally:
        sys.exit = old_exit

    return 0, buf.getvalue()
