import argparse

from pwd_generator.version import __version__


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Horizon Secure Password Generator - Generate secure passwords with encrypted history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  horizon-cipher generate --length 20
  horizon-cipher generate --type passphrase --words 6
  horizon-cipher generate --type pin --length 8
  horizon-cipher analyze "MyPassword123!"
  horizon-cipher batch --count 10 --length 16
  horizon-cipher history list
  horizon-cipher history search gmail
  horizon-cipher interactive
  horizon-cipher --history-file ./vault.enc interactive
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Log file path (default: user log directory, see documentation)",
    )

    parser.add_argument(
        "--history-file",
        type=str,
        default="password_history.enc",
        help="Path to encrypted history file (default: password_history.enc)",
    )

    parser.add_argument(
        "--master-password",
        type=str,
        help="Master password (not recommended, use interactive prompt instead)",
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Quiet mode (minimal output)"
    )

    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    gen_parser = subparsers.add_parser(
        "generate", aliases=["gen", "g"], help="Generate a password"
    )
    gen_parser.add_argument(
        "--type",
        "-t",
        choices=["random", "passphrase", "pin"],
        default="random",
        help="Password type (default: random)",
    )
    gen_parser.add_argument(
        "--length",
        "-l",
        type=int,
        default=16,
        help="Password/PIN length (default: 16 for random, 6 for PIN)",
    )
    gen_parser.add_argument(
        "--words",
        "-w",
        type=int,
        default=5,
        help="Number of words for passphrase (default: 5, minimum: 4)",
    )
    gen_parser.add_argument(
        "--separator",
        "-s",
        type=str,
        default="-",
        help="Separator for passphrase (default: -)",
    )
    gen_parser.add_argument(
        "--no-clipboard", action="store_true", help="Do not copy to clipboard"
    )
    gen_parser.add_argument(
        "--save", action="store_true", help="Save to encrypted history"
    )
    gen_parser.add_argument(
        "--service", type=str, default="", help="Service name for history entry"
    )
    gen_parser.add_argument(
        "--notes", type=str, default="", help="Notes (optional) for history entry"
    )
    gen_parser.add_argument(
        "--profile",
        type=str,
        help="Use password profile (banking, social, work, email, general)",
    )

    analyze_parser = subparsers.add_parser(
        "analyze", aliases=["a"], help="Analyze a password"
    )
    analyze_parser.add_argument("password", type=str, help="Password to analyze")

    batch_parser = subparsers.add_parser(
        "batch", aliases=["b"], help="Generate multiple passwords"
    )
    batch_parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=10,
        help="Number of passwords to generate (default: 10, max: 1000)",
    )
    batch_parser.add_argument(
        "--type",
        "-t",
        choices=["random", "passphrase", "pin"],
        default="random",
        help="Password type (default: random)",
    )
    batch_parser.add_argument(
        "--length", "-l", type=int, default=16, help="Password/PIN length"
    )
    batch_parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (if not specified, prints to stdout)",
    )
    batch_parser.add_argument(
        "--format",
        "-f",
        choices=["txt", "json", "csv"],
        default="txt",
        help="Output format (default: txt)",
    )

    history_parser = subparsers.add_parser(
        "history", aliases=["h"], help="Manage password history"
    )
    history_subparsers = history_parser.add_subparsers(dest="history_command")

    history_subparsers.add_parser(
        "list", aliases=["l"], help="List password history"
    ).add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of entries to show (default: 20)",
    )

    history_subparsers.add_parser(
        "search", aliases=["s"], help="Search password history"
    ).add_argument(
        "query", type=str, help="Search query (service name or notes)"
    )

    history_subparsers.add_parser("show", help="Show password entry").add_argument(
        "index", type=int, help="Entry index (1-based)"
    )

    history_subparsers.add_parser(
        "delete", aliases=["d"], help="Delete password entry"
    ).add_argument("index", type=int, help="Entry index (1-based)")

    history_export = history_subparsers.add_parser(
        "export", aliases=["e"], help="Export password history"
    )
    history_export.add_argument(
        "--output", "-o", type=str, required=True, help="Output file path"
    )
    history_export.add_argument(
        "--format",
        "-f",
        choices=["json", "csv"],
        default="json",
        help="Export format (default: json)",
    )
    history_export.add_argument(
        "--no-passwords",
        action="store_true",
        help="Exclude passwords from export (redacted)",
    )
    history_export.add_argument(
        "--filter-service", type=str, help="Filter by service name"
    )
    history_export.add_argument(
        "--filter-strength",
        choices=["Weak", "Fair", "Good", "Strong", "Very Strong"],
        help="Filter by minimum strength",
    )
    history_export.add_argument(
        "--filter-entropy", type=float, help="Filter by minimum entropy"
    )
    history_export.add_argument(
        "--sort",
        choices=["date", "service", "strength", "entropy"],
        default="date",
        help="Sort by field (default: date)",
    )
    history_export.add_argument(
        "--reverse", action="store_true", help="Reverse sort order"
    )

    breach_parser = subparsers.add_parser(
        "breach", help="Check if password has been breached"
    )
    breach_parser.add_argument("password", type=str, help="Password to check")

    template_parser = subparsers.add_parser(
        "template", aliases=["t"], help="Generate password using template"
    )
    template_parser.add_argument(
        "template",
        type=str,
        nargs="?",
        help="Template name (alphanumeric, numeric_only, letters_only, no_special, url_safe, readable)",
    )
    template_parser.add_argument(
        "--length", "-l", type=int, default=16, help="Password length (default: 16)"
    )
    template_parser.add_argument(
        "--list", action="store_true", help="List available templates"
    )

    config_parser = subparsers.add_parser(
        "config", aliases=["c"], help="Manage configuration"
    )
    config_parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Config file path (default: ~/.pwd_generator_config.json)",
    )
    config_parser.add_argument(
        "--show", action="store_true", help="Show current configuration"
    )
    config_parser.add_argument(
        "--create-default",
        action="store_true",
        help="Create default configuration file",
    )

    profile_parser = subparsers.add_parser(
        "profile", aliases=["p"], help="Manage password profiles"
    )
    profile_subparsers = profile_parser.add_subparsers(dest="profile_command")

    profile_subparsers.add_parser(
        "list", aliases=["l"], help="List all profiles"
    )

    profile_show = profile_subparsers.add_parser(
        "show", help="Show profile details"
    )
    profile_show.add_argument("name", type=str, help="Profile name")

    profile_create = profile_subparsers.add_parser(
        "create", help="Create new profile"
    )
    profile_create.add_argument("name", type=str, help="Profile name")
    profile_create.add_argument("--min-length", type=int, help="Minimum length")
    profile_create.add_argument("--min-entropy", type=float, help="Minimum entropy")
    profile_create.add_argument("--template", type=str, help="Template to use")

    audit_parser = subparsers.add_parser(
        "audit", aliases=["au"], help="Password security audit"
    )
    audit_parser.add_argument("--output", "-o", type=str, help="Output file for report")
    audit_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "html"],
        default="text",
        help="Report format",
    )

    import_parser = subparsers.add_parser(
        "import", aliases=["i"], help="Import passwords from file"
    )
    import_parser.add_argument("file", type=str, help="File to import from")
    import_parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json", "1password", "lastpass", "bitwarden"],
        default="csv",
        help="Import format",
    )

    pattern_parser = subparsers.add_parser(
        "pattern", help="Generate password from pattern"
    )
    pattern_parser.add_argument(
        "pattern", type=str, help="Pattern (e.g., [noun]-[verb]-[2digits]-[1special])"
    )
    pattern_parser.add_argument(
        "--examples", action="store_true", help="Show pattern examples"
    )

    qr_parser = subparsers.add_parser("qr", help="Generate QR code for password")
    qr_parser.add_argument("password", type=str, help="Password to encode")
    qr_parser.add_argument(
        "--output", "-o", type=str, help="Output file (default: auto-generated)"
    )
    qr_parser.add_argument(
        "--output-dir",
        "-d",
        type=str,
        help="Output directory (default: current directory)",
    )
    qr_parser.add_argument("--wifi", action="store_true", help="Generate WiFi QR code")
    qr_parser.add_argument("--ssid", type=str, help="WiFi SSID (required with --wifi)")
    qr_parser.add_argument(
        "--security",
        type=str,
        default="WPA",
        choices=["WPA", "WEP", "nopass"],
        help="WiFi security type",
    )
    qr_parser.add_argument(
        "--hidden", action="store_true", help="WiFi network is hidden"
    )
    qr_parser.add_argument(
        "--display", action="store_true", help="Display QR code after generation"
    )

    compare_parser = subparsers.add_parser(
        "compare", help="Compare multiple passwords"
    )
    compare_parser.add_argument(
        "passwords", nargs="+", type=str, help="Passwords to compare"
    )

    subparsers.add_parser(
        "interactive",
        aliases=["menu"],
        help="Full-screen interactive menu (master-password prompts; same as running with no arguments)",
    )

    return parser
