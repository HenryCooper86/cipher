"""CLI package: argparse entrypoints and command handlers."""

import logging
import sys
import warnings
from pathlib import Path

from pwd_generator import SecurePasswordGenerator
from pwd_generator.encryption import clear_memory
from pwd_generator.exceptions import (
    EncryptionError,
    FileOperationError,
    HistoryError,
    PasswordGeneratorError,
    ValidationError,
)
from pwd_generator.paths import default_log_file_path
from pwd_generator.utils import (
    copy_to_clipboard,
    print_password_stats,
    prompt_yes_no,
    safe_getpass,
    safe_input,
)

from .core import constant_time_compare, get_master_password, setup_logging
from .errors import format_cli_error_text
from .handlers import (
    _escape_wifi_value,
    handle_analyze,
    handle_audit,
    handle_batch,
    handle_breach_check,
    handle_compare,
    handle_config,
    handle_generate,
    handle_history_delete,
    handle_history_export,
    handle_history_list,
    handle_history_search,
    handle_history_show,
    handle_import,
    handle_pattern,
    handle_profile,
    handle_qr,
    handle_save,
    handle_template,
)
from .parser import create_parser


def dispatch_cli_command(args, gen: SecurePasswordGenerator, parser) -> None:
    """
    Run a single parsed CLI command using an existing generator instance.
    May call sys.exit on errors (same as standalone CLI).
    """
    if args.command in ["generate", "gen", "g"]:
        handle_generate(args, gen)
    elif args.command in ["analyze", "a"]:
        handle_analyze(args, gen)
    elif args.command in ["save", "sv"]:
        handle_save(args, gen)
    elif args.command in ["batch", "b"]:
        handle_batch(args, gen)
    elif args.command in ["history", "h"]:
        if args.history_command in ("list", "l"):
            handle_history_list(args, gen)
        elif args.history_command in ("search", "s"):
            handle_history_search(args, gen)
        elif args.history_command == "show":
            handle_history_show(args, gen)
        elif args.history_command in ("delete", "d"):
            handle_history_delete(args, gen)
        elif args.history_command in ("export", "e"):
            handle_history_export(args, gen)
        else:
            parser.parse_args(["history", "--help"])
    elif args.command == "breach":
        handle_breach_check(args, gen)
    elif args.command in ["template", "t"]:
        handle_template(args, gen)
    elif args.command in ["config", "c"]:
        handle_config(args)
    elif args.command in ["profile", "p"]:
        handle_profile(args, gen)
    elif args.command in ["audit", "au"]:
        handle_audit(args, gen)
    elif args.command in ["import", "i"]:
        handle_import(args, gen)
    elif args.command == "pattern":
        handle_pattern(args, gen)
    elif args.command == "qr":
        handle_qr(args, gen)
    elif args.command == "compare":
        handle_compare(args, gen)
    else:
        print(f"[ERROR] Unknown command: {args.command!r}")
        sys.exit(1)


__all__ = [
    "SecurePasswordGenerator",
    "constant_time_compare",
    "copy_to_clipboard",
    "create_parser",
    "dispatch_cli_command",
    "get_master_password",
    "main_cli",
    "print_password_stats",
    "prompt_yes_no",
    "safe_getpass",
    "safe_input",
    "setup_logging",
    "_escape_wifi_value",
    "handle_analyze",
    "handle_audit",
    "handle_batch",
    "handle_breach_check",
    "handle_compare",
    "handle_config",
    "handle_generate",
    "handle_history_delete",
    "handle_history_export",
    "handle_history_list",
    "handle_history_search",
    "handle_history_show",
    "handle_import",
    "handle_pattern",
    "handle_profile",
    "handle_qr",
    "handle_template",
]


def main_cli():
    from pwd_generator.config import load_config

    parser = create_parser()
    args = parser.parse_args()

    log_file = getattr(args, "log_file", None)
    if not log_file:
        log_file = str(default_log_file_path())
    verbose = getattr(args, "verbose", False)
    setup_logging(log_file, verbose)

    config = load_config()
    policy = config.get("policy", {})

    commands_requiring_history = ["history", "h", "audit", "au", "import", "i"]
    commands_not_requiring_master = [
        "config",
        "c",
        "template",
        "t",
        "breach",
        "analyze",
        "a",
        "pattern",
        "qr",
        "compare",
        "profile",
        "p",
    ]

    history_file = getattr(args, "history_file", "password_history.enc")
    history_exists = Path(history_file).exists()

    master_password = None
    command = getattr(args, "command", None)

    if not command:
        parser.print_help()
        print(
            "\nTip: for the full interactive menu, run with no arguments or use:\n"
            f"  {parser.prog} interactive",
            file=sys.stderr,
        )
        sys.exit(0)

    if command in ("interactive", "menu"):
        from pwd_generator.interactive import main_interactive
        from pwd_generator.logging_config import quiet_console_for_interactive_menu

        quiet_console_for_interactive_menu()
        main_interactive(history_file=str(history_file))
        return

    if command in commands_not_requiring_master:
        if command in ["config", "c"]:
            handle_config(args)
            return
    elif getattr(args, "master_password", None):
        warnings.warn(
            "\n"
            "=" * 70 + "\n"
            "SECURITY WARNING: Passing master password via --master-password argument\n"
            "is NOT RECOMMENDED for production use. The password may be visible in:\n"
            "  - Process list (ps, top, Activity Monitor, etc.)\n"
            "  - Shell history (~/.bash_history, ~/.zsh_history, etc.)\n"
            "  - System logs\n\n"
            "Use interactive mode (omit --master-password) for secure password entry.\n"
            "=" * 70,
            UserWarning,
            stacklevel=2,
        )
        master_password = bytearray(args.master_password.encode("utf-8"))
    elif history_exists or (command in commands_requiring_history):
        master_password = get_master_password(history_exists)

    try:
        gen = SecurePasswordGenerator(
            history_file=history_file, master_password=master_password, policy=policy
        )
    except ValidationError as e:
        print(f"[ERROR] {e}")
        if master_password:
            clear_memory(master_password)
        sys.exit(1)
    except EncryptionError as e:
        print(f"[ERROR] {e}")
        print("\nThis usually means:")
        print("  - You entered a different master password than before")
        print("  - The history file is corrupted")
        if master_password:
            clear_memory(master_password)
        sys.exit(1)

    try:
        dispatch_cli_command(args, gen, parser)
    except BrokenPipeError:
        if master_password:
            clear_memory(master_password)
        try:
            sys.stdout.close()
        except OSError:
            pass
        raise SystemExit(0)
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        if master_password:
            clear_memory(master_password)
        sys.exit(0)
    except SystemExit:
        if master_password:
            clear_memory(master_password)
        raise
    except (
        ValidationError,
        FileOperationError,
        HistoryError,
        EncryptionError,
        ValueError,
        PasswordGeneratorError,
    ) as e:
        msg = format_cli_error_text(e)
        if msg:
            print(msg, end="")
        if master_password:
            clear_memory(master_password)
        sys.exit(1)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error in CLI")
        print(f"[ERROR] An unexpected error occurred: {e}")
        print("   Please report this issue if it persists.")
        if master_password:
            clear_memory(master_password)
        sys.exit(1)
    finally:
        if master_password:
            clear_memory(master_password)
            logger = logging.getLogger(__name__)
            logger.debug("Master password cleared from memory")
