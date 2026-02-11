import argparse
import sys
import getpass
from pathlib import Path
from typing import Optional, Union

from pwd_generator import SecurePasswordGenerator, EncryptionError, ValidationError
from pwd_generator.utils import (
    print_password_stats,
    copy_to_clipboard,
    safe_input,
    safe_getpass,
    prompt_yes_no,
)
from pwd_generator.validators import (
    validate_positive_int,
    validate_length,
    validate_file_path,
    validate_string,
)
from pwd_generator.encryption import clear_memory


def setup_logging(log_file: Optional[str] = None, verbose: bool = False):
    from pwd_generator.logging_config import setup_logging as setup_logging_enhanced

    setup_logging_enhanced(log_file, verbose)


def get_master_password(history_exists: bool = False) -> Optional[bytearray]:
    if not history_exists:
        print(
            "Welcome! This appears to be your first time using the password generator."
        )
        print("Let's create a master password to encrypt your password history.")
        print()

        while True:
            master_password = safe_getpass("Create a master password (12+ chars): ")
            if not master_password:
                return None

            confirm = safe_getpass("Confirm master password: ")
            if master_password != confirm:
                print("Passwords don't match. Please try again.")
                print()
                clear_memory(master_password)
                clear_memory(confirm)
                continue

            clear_memory(confirm)
            try:
                gen = SecurePasswordGenerator(master_password=master_password)
                print("Master password created successfully!")
                return master_password
            except ValidationError as e:
                print(f"{e}")
                clear_memory(master_password)
                if not prompt_yes_no("Try again?", default=True):
                    return None
    else:
        master_password = safe_getpass(
            "Enter master password for history (12+ chars): "
        )
        return master_password if master_password else None


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Horizon Secure Password Generator - Generate secure passwords with encrypted history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cipher.py --generate --length 20
  python cipher.py --generate --type passphrase --words 6
  python cipher.py --generate --type pin --length 8
  python cipher.py --analyze "MyPassword123!"
  python cipher.py --batch --count 10 --length 16
  python cipher.py --history --list
  python cipher.py --history --search "gmail"
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--log-file", type=str, help="Log file path (default: password_generator.log)"
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

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

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
        "--notes", type=str, default="", help="Notes for history entry"
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

    history_list = history_subparsers.add_parser(
        "list", aliases=["l"], help="List password history"
    )
    history_list.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of entries to show (default: 20)",
    )

    history_search = history_subparsers.add_parser(
        "search", aliases=["s"], help="Search password history"
    )
    history_search.add_argument(
        "query", type=str, help="Search query (service name or notes)"
    )

    history_show = history_subparsers.add_parser("show", help="Show password entry")
    history_show.add_argument("index", type=int, help="Entry index (1-based)")

    history_delete = history_subparsers.add_parser(
        "delete", aliases=["d"], help="Delete password entry"
    )
    history_delete.add_argument("index", type=int, help="Entry index (1-based)")

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

    profile_list = profile_subparsers.add_parser(
        "list", aliases=["l"], help="List all profiles"
    )
    profile_show = profile_subparsers.add_parser("show", help="Show profile details")
    profile_show.add_argument("name", type=str, help="Profile name")
    profile_create = profile_subparsers.add_parser("create", help="Create new profile")
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

    compare_parser = subparsers.add_parser("compare", help="Compare multiple passwords")
    compare_parser.add_argument(
        "passwords", nargs="+", type=str, help="Passwords to compare"
    )

    return parser


def handle_generate(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.profiles import ProfileManager

    quiet = getattr(args, "quiet", False)
    json_output = getattr(args, "json", False)

    if args.profile:
        manager = ProfileManager()
        profile_obj = manager.get_profile(args.profile)
        if profile_obj:
            pass
        else:
            print(f"[ERROR] Profile '{args.profile}' not found")
            sys.exit(1)

    try:
        if args.type == "random":
            length = validate_length(
                args.length, 1, gen.policy["max_length"], "Password length"
            )
            password = gen.generate_random_string(length)
        elif args.type == "passphrase":
            words = validate_positive_int(str(args.words), "Number of words")
            password = gen.generate_passphrase(words, args.separator)
        elif args.type == "pin":
            length = validate_length(args.length, 4, 10, "PIN length")
            password = gen.generate_pin(length)
        else:
            print(f"[ERROR] Unknown password type: {args.type}")
            sys.exit(1)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if json_output:
        import json

        stats = gen.get_password_stats(password)
        stats["password"] = password
        print(json.dumps(stats, indent=2))
    elif quiet:
        print(password)
    else:
        from pwd_generator.visualization import print_enhanced_password_stats

        print_enhanced_password_stats(gen, password)

        if not args.no_clipboard:
            if copy_to_clipboard(password):
                print("Copied to clipboard")
            else:
                print("Clipboard copy not available")

        if args.save and gen.encryption_manager.cipher:
            service = args.service or safe_input("Service name: ").strip()
            notes = args.notes or safe_input("Notes (optional): ").strip()
            gen.add_to_history(password, service, notes)
            print("Saved to encrypted history")
        elif args.save and not gen.encryption_manager.cipher:
            print("Warning: Cannot save - encryption not initialized")


def handle_analyze(args, gen: SecurePasswordGenerator) -> None:
    quiet = getattr(args, "quiet", False)
    json_output = getattr(args, "json", False)

    if json_output:
        import json

        stats = gen.get_password_stats(args.password)
        print(json.dumps(stats, indent=2))
    elif quiet:
        print(gen.generate_random_string(16) if not args.password else args.password)
    else:
        from pwd_generator.visualization import print_enhanced_password_stats

        print_enhanced_password_stats(gen, args.password)


def handle_batch(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.export import export_passwords_json, export_passwords_csv

    try:
        count = validate_positive_int(str(args.count), "Count")
        count = validate_length(count, 1, 1000, "Count")
        length = (
            validate_length(args.length, 1, gen.policy["max_length"], "Password length")
            if args.type == "random"
            else args.length
        )
        passwords = gen.batch_generate(count, length, args.type, show_progress=True)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if args.output:
        try:
            safe_output_path = validate_file_path(args.output)

            if args.format == "json":
                if export_passwords_json(passwords, str(safe_output_path)):
                    print(
                        f"Generated {len(passwords)} passwords and saved to {safe_output_path} (JSON)"
                    )
                else:
                    print(f"[ERROR] Failed to export to {safe_output_path}")
                    sys.exit(1)
            elif args.format == "csv":
                if export_passwords_csv(passwords, str(safe_output_path)):
                    print(
                        f"Generated {len(passwords)} passwords and saved to {safe_output_path} (CSV)"
                    )
                else:
                    print(f"[ERROR] Failed to export to {safe_output_path}")
                    sys.exit(1)
            else:
                with open(safe_output_path, "w") as f:
                    for pwd in passwords:
                        f.write(pwd + "\n")
                print(
                    f"Generated {len(passwords)} passwords and saved to {safe_output_path}"
                )
        except ValueError as e:
            print(f"[ERROR] Security policy violation - {e}")
            sys.exit(1)
    else:
        print(f"\nGenerated {len(passwords)} passwords:")
        print("-" * 60)
        for i, pwd in enumerate(passwords, 1):
            print(f"{i:2d}. {pwd}")


def handle_history_list(args, gen: SecurePasswordGenerator) -> None:
    if not gen.history:
        print("\nNo password history available")
        return

    try:
        limit = validate_positive_int(str(args.limit), "Limit")
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"\nPassword History ({len(gen.history)} entries)")
    print("-" * 60)
    for i, entry in enumerate(gen.history[:limit], 1):
        meta = entry["metadata"]
        print(
            f"{i:2d}. {meta['service']:30s} | {meta['created_at'][:10]} | {meta['strength']:12s} | {meta['entropy']:.1f} bits"
        )
    if len(gen.history) > limit:
        print(f"\n... and {len(gen.history) - limit} more entries")


def handle_history_search(args, gen: SecurePasswordGenerator) -> None:
    if not gen.history:
        print("\nNo password history available")
        return

    query = args.query.lower()
    results = []
    for e in gen.history:
        meta = e["metadata"]
        match_field = None
        if query in meta["service"].lower():
            match_field = "service"
        elif query in meta.get("notes", "").lower():
            match_field = "notes"

        if match_field:
            results.append((e, match_field))

    if not results:
        print(f"\nNo results found for '{args.query}'")
    else:
        print(f"\nFound {len(results)} result(s)")
        print("-" * 60)
        for i, (entry, match_field) in enumerate(results, 1):
            meta = entry["metadata"]
            print(f"{i}. {meta['service']} [matched in: {match_field}]")
            print(f"   Created: {meta['created_at']}")
            print(f"   Strength: {meta['strength']} ({meta['entropy']:.1f} bits)")
            if meta.get("notes"):
                print(f"   Notes: {meta['notes']}")
            print()


def handle_history_show(args, gen: SecurePasswordGenerator) -> None:
    try:
        idx = validate_positive_int(str(args.index), "Entry index") - 1
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if 0 <= idx < len(gen.history):
        entry = gen.history[idx]
        meta = entry["metadata"]
        print(f"\n{'=' * 60}")
        print(f"Service:    {meta['service']}")
        print(f"Created:    {meta['created_at']}")
        print(f"Strength:   {meta['strength']} ({meta['entropy']:.1f} bits)")
        print(f"Notes:      {meta.get('notes', 'N/A')}")
        print(f"Password:   {entry['password']}")
        print(f"{'=' * 60}")
    else:
        print(f"[ERROR] Invalid entry number. Valid range: 1-{len(gen.history)}")
        sys.exit(1)


def handle_history_delete(args, gen: SecurePasswordGenerator) -> None:
    try:
        idx = validate_positive_int(str(args.index), "Entry index") - 1
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if 0 <= idx < len(gen.history):
        if prompt_yes_no(
            f"Delete '{gen.history[idx]['metadata']['service']}'?", default=False
        ):
            if gen.delete_from_history(idx):
                print("Entry deleted")
            else:
                print("[ERROR] Failed to delete entry")
                sys.exit(1)
    else:
        print(f"[ERROR] Invalid entry number. Valid range: 1-{len(gen.history)}")
        sys.exit(1)


def handle_history_export(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.export import export_history_json, export_history_csv
    from pwd_generator.filters import (
        filter_history_by_service,
        filter_history_by_strength,
        filter_history_by_entropy,
        sort_history,
    )

    if not gen.history:
        print("\nNo password history available")
        return

    filtered_history = gen.history.copy()

    if args.filter_service:
        filtered_history = filter_history_by_service(
            filtered_history, args.filter_service
        )

    if args.filter_strength:
        filtered_history = filter_history_by_strength(
            filtered_history, args.filter_strength
        )

    if args.filter_entropy:
        filtered_history = filter_history_by_entropy(
            filtered_history, args.filter_entropy
        )

    filtered_history = sort_history(filtered_history, args.sort, args.reverse)

    if not filtered_history:
        print("No entries match the filter criteria")
        return

    try:
        safe_output_path = validate_file_path(args.output)

        if args.format == "json":
            if export_history_json(
                filtered_history, str(safe_output_path), not args.no_passwords
            ):
                print(
                    f"Exported {len(filtered_history)} entries to {safe_output_path} (JSON)"
                )
            else:
                print(f"[ERROR] Failed to export to {safe_output_path}")
                sys.exit(1)
        elif args.format == "csv":
            if export_history_csv(
                filtered_history, str(safe_output_path), not args.no_passwords
            ):
                print(
                    f"Exported {len(filtered_history)} entries to {safe_output_path} (CSV)"
                )
            else:
                print(f"[ERROR] Failed to export to {safe_output_path}")
                sys.exit(1)
    except ValueError as e:
        print(f"[ERROR] Security policy violation - {e}")
        sys.exit(1)


def handle_breach_check(args, gen: SecurePasswordGenerator) -> None:
    is_breached, details = gen.check_password_breach(args.password)

    print(f"\n{'=' * 70}")
    print(f"                    BREACH CHECK RESULT")
    print(f"{'=' * 70}")

    if details.get("error"):
        print(f"\n[WARNING]  Status: Error")
        print(f"   {details['message']}")
    elif is_breached:
        print(f"\n[WARNING]  Status: BREACHED")
        print(f"   {details['message']}")
        print(f"\n   Details:")
        print(f"   • Breach Count: {details['count']:,} occurrences")
        print(f"   • Hash Prefix Checked: {details['hash_prefix']}****")
        print(f"   • Checked At: {details['timestamp']}")
    else:
        print(f"\n[OK] Status: SAFE")
        print(f"   {details['message']}")
        print(f"\n   Details:")
        print(f"   • Hash Prefix Checked: {details['hash_prefix']}****")
        print(f"   • Checked At: {details['timestamp']}")

    if details.get("recommendations"):
        print(f"\n   Recommendations:")
        for i, rec in enumerate(details["recommendations"], 1):
            print(f"   {i}. {rec}")

    print(f"\n   Security Note:")
    print(f"   • This check uses k-anonymity (only first 5 chars of hash sent)")
    print(f"   • Your full password never leaves your device")
    print(f"   • Data source: Have I Been Pwned (haveibeenpwned.com)")

    print(f"{'=' * 70}\n")


def handle_template(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.templates import get_template, list_templates

    if args.list or not args.template:
        templates = list_templates()
        print("\nAvailable Templates:")
        print("-" * 60)
        for template in templates:
            print(f"  - {template}")
        print()
        if not args.list:
            print("Usage: python cipher.py template <template_name> --length <length>")
        return

    template = get_template(args.template)
    if not template:
        print(f"[ERROR] Unknown template '{args.template}'")
        print(f"Available templates: {', '.join(list_templates())}")
        sys.exit(1)

    try:
        length = validate_length(
            args.length,
            template.min_length,
            gen.policy["max_length"],
            "Password length",
        )
        password = template.generate(length)

        print_password_stats(gen, password)

        if copy_to_clipboard(password):
            print("Copied to clipboard")
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def handle_config(args) -> None:
    from pwd_generator.config import load_config, save_config, create_default_config

    config_path = None
    if args.file:
        try:
            safe_path = validate_file_path(args.file, base_dir=Path.home())
            config_path = str(safe_path)
        except ValueError as e:
            print(f"[ERROR] Invalid config file path: {e}")
            sys.exit(1)

    if args.create_default:
        if create_default_config(config_path):
            print(
                f"Created default configuration file: {config_path or '~/.pwd_generator_config.json'}"
            )
        else:
            print("[ERROR] Failed to create configuration file")
            sys.exit(1)
    elif args.show:
        config = load_config(config_path)
        import json

        print("\nCurrent Configuration:")
        print("=" * 60)
        print(json.dumps(config, indent=2))
        print("=" * 60)
    else:
        print("Use --show to view config or --create-default to create default config")


def handle_profile(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.profiles import ProfileManager, PasswordProfile

    manager = ProfileManager()

    if args.profile_command == "list" or args.profile_command == "l":
        profiles = manager.list_profiles()
        print("\nAvailable Profiles:")
        print("-" * 60)
        for profile_name in profiles:
            profile = manager.get_profile(profile_name)
            print(f"  • {profile_name}")
            if profile:
                print(f"    - Min Length: {profile.policy.get('min_length', 'N/A')}")
                print(f"    - Min Entropy: {profile.policy.get('min_entropy', 'N/A')}")
                print(f"    - Template: {profile.template or 'None'}")
        print()
    elif args.profile_command == "show":
        profile = manager.get_profile(args.name)
        if profile:
            import json

            print(f"\nProfile: {profile.name}")
            print("=" * 60)
            print(json.dumps(profile.to_dict(), indent=2))
            print("=" * 60)
        else:
            print(f"[ERROR] Profile '{args.name}' not found")
            sys.exit(1)
    elif args.profile_command == "create":
        policy = {}
        if args.min_length:
            policy["min_length"] = args.min_length
        if args.min_entropy:
            policy["min_entropy"] = args.min_entropy

        profile = PasswordProfile(args.name, policy, args.template)
        if manager.add_profile(profile):
            print(f"[OK] Created profile '{args.name}'")
        else:
            print(f"[ERROR] Failed to create profile")
            sys.exit(1)


def handle_audit(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.audit import PasswordAuditor
    import json

    auditor = PasswordAuditor(gen)
    report = auditor.generate_audit_report()

    if args.format == "json":
        output = json.dumps(report, indent=2)
        if args.output:
            try:
                safe_output_path = validate_file_path(args.output)
                with open(safe_output_path, "w") as f:
                    f.write(output)
                print(f"[OK] Audit report saved to {safe_output_path}")
            except ValueError as e:
                print(f"[ERROR] Security policy violation - {e}")
                sys.exit(1)
        else:
            print(output)
    else:
        print(f"\n{'=' * 70}")
        print(f"                    PASSWORD SECURITY AUDIT")
        print(f"{'=' * 70}")
        print(f"\nGenerated: {report['generated_at']}")

        score = report["security_score"]
        print(f"\nSecurity Score: {score['score']:.1f}/100")
        print(f"  • Total Passwords: {score['details']['total_passwords']}")
        print(f"  • Weak Passwords: {score['details']['weak_passwords']}")
        print(f"  • Duplicate Passwords: {score['details']['duplicate_passwords']}")
        print(f"  • Expired Passwords: {score['details']['expired_passwords']}")

        if report["duplicates"]:
            print(f"\n[WARNING]  Duplicate Passwords ({len(report['duplicates'])}):")
            for dup in report["duplicates"][:10]:
                length_info = f", length {dup['length']}" if 'length' in dup else ""
                print(f"   • {dup['password']} (used {dup['count']} times{length_info})")

        if report["weak_passwords"]:
            print(f"\n[WARNING]  Weak Passwords ({len(report['weak_passwords'])}):")
            for weak in report["weak_passwords"][:10]:
                print(f"   • {weak['service']}: {weak['entropy']:.1f} bits")

        if report["expired_passwords"]:
            print(
                f"\n[WARNING]  Expired Passwords ({len(report['expired_passwords'])}):"
            )
            for exp in report["expired_passwords"][:10]:
                print(f"   • {exp['service']}: {exp['created_at'][:10]}")

        print(f"\n{'=' * 70}\n")

        if args.output:
            try:
                safe_output_path = validate_file_path(args.output)
                with open(safe_output_path, "w") as f:
                    f.write(f"Password Security Audit Report\n")
                    f.write(f"Generated: {report['generated_at']}\n")
                    f.write(f"Security Score: {score['score']:.1f}/100\n\n")
                print(f"[OK] Report saved to {safe_output_path}")
            except ValueError as e:
                print(f"[ERROR] Security policy violation - {e}")
                sys.exit(1)


def handle_import(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.import_export import (
        import_from_csv,
        import_from_json,
        export_to_1password_csv,
        export_to_lastpass_csv,
        export_to_bitwarden_csv,
    )

    if not gen.encryption_manager.cipher:
        print(
            "Error: Encryption not initialized. Cannot import without master password."
        )
        sys.exit(1)

    try:
        safe_import_path = validate_file_path(args.file, base_dir=Path.home())
        import_path = str(safe_import_path)
        if args.format == "json":
            entries = import_from_json(import_path)
        else:
            format_map = {
                "csv": "generic",
                "1password": "1password",
                "lastpass": "lastpass",
                "bitwarden": "bitwarden",
            }
            entries = import_from_csv(import_path, format_map.get(args.format, "generic"))

        imported = 0
        for entry in entries:
            gen.add_to_history(
                entry["password"],
                entry["metadata"].get("service", ""),
                entry["metadata"].get("notes", ""),
            )
            imported += 1

        print(f"[OK] Imported {imported} passwords from {import_path}")
    except ValueError as e:
        print(f"[ERROR] Invalid file path: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error importing: {e}")
        sys.exit(1)


def handle_pattern(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.patterns import PatternGenerator, validate_pattern

    if args.examples:
        print("\nPattern Examples:")
        print("-" * 60)
        print("  [noun]-[verb]-[2digits]-[1special]")
        print("  [4letters][2digits][1special]")
        print("  [word]-[word]-[3digits]!")
        print("  [upper][lower][number][special]")
        print("\nAvailable tokens:")
        print("  [noun], [verb], [adj] - word lists")
        print("  [word] - random word")
        print("  [Nletters] - N random letters")
        print("  [Ndigits] - N random digits")
        print("  [Nspecial] - N special characters")
        print("  [upper], [lower], [number], [special] - single characters")
        print()
        return

    is_valid, message = validate_pattern(args.pattern)
    if not is_valid:
        print(f"[ERROR] Invalid pattern - {message}")
        sys.exit(1)

    generator = PatternGenerator()
    password = generator.generate_from_pattern(args.pattern)

    print_password_stats(gen, password)

    if copy_to_clipboard(password):
        print("Copied to clipboard")


def handle_qr(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.qr_code import (
        generate_qr_code,
        generate_wifi_qr,
        display_qr_code,
        qr_code_to_ascii,
    )
    import os

    if args.wifi:
        if not args.ssid:
            print("[ERROR] --ssid required when using --wifi")
            sys.exit(1)
        wifi_string = f"WIFI:T:{args.security};S:{args.ssid};P:{args.password};H:{'true' if args.hidden else 'false'};;"
        qr_file = generate_wifi_qr(
            args.ssid,
            args.password,
            args.security,
            args.hidden,
            output_dir=args.output_dir,
        )
        text_for_ascii = wifi_string
    else:
        qr_file = generate_qr_code(
            args.password, args.output, output_dir=args.output_dir
        )
        text_for_ascii = args.password

    if qr_file:
        abs_path = os.path.abspath(qr_file)

        ascii_qr = qr_code_to_ascii(text_for_ascii)

        print(f"\n{'=' * 70}")
        print(f"                    QR CODE GENERATED")
        print(f"{'=' * 70}")

        if ascii_qr:
            print(f"\n[QR] QR CODE (Scan with your phone):")
            print("-" * 70)
            print(ascii_qr)
            print("-" * 70)

        print(f"\n[OK] QR code saved successfully!")
        print(f"\nFile Location:")
        print(f"   {abs_path}")
        print(f"\nDirectory:")
        print(f"   {os.path.dirname(abs_path)}")

        if args.display:
            if display_qr_code(qr_file):
                print("\n[OK] QR code displayed")
            else:
                print("\n[WARNING]  Could not display QR code (no GUI available)")
                print(f"   You can open it manually: {abs_path}")

        print(f"\n{'=' * 70}\n")
    else:
        print("[ERROR] Failed to generate QR code")
        sys.exit(1)


def handle_compare(args, gen: SecurePasswordGenerator) -> None:
    print(f"\n{'=' * 70}")
    print(f"                    PASSWORD COMPARISON")
    print(f"{'=' * 70}\n")

    results = []
    for pwd in args.passwords:
        stats = gen.get_password_stats(pwd)
        results.append(
            {
                "password": pwd[:20] + "..." if len(pwd) > 20 else pwd,
                "length": stats["length"],
                "entropy": stats["entropy"],
                "strength": stats["strength"],
                "unique": stats["unique_chars"],
            }
        )

    print(
        f"{'Password':<25} {'Length':<8} {'Entropy':<10} {'Strength':<12} {'Unique':<8}"
    )
    print("-" * 70)
    for r in results:
        print(
            f"{r['password']:<25} {r['length']:<8} {r['entropy']:<10.1f} {r['strength']:<12} {r['unique']:<8}"
        )

    print(f"\n{'=' * 70}\n")


def main_cli():
    from pwd_generator.config import load_config

    parser = create_parser()
    args = parser.parse_args()

    log_file = args.log_file if hasattr(args, "log_file") else "password_generator.log"
    verbose = args.verbose if hasattr(args, "verbose") else False
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

    history_file = (
        args.history_file if hasattr(args, "history_file") else "password_history.enc"
    )
    history_exists = Path(history_file).exists()

    master_password = None
    command = args.command if hasattr(args, "command") else None

    if not command:
        parser.print_help()
        sys.exit(0)

    if command in commands_not_requiring_master:
        if command in ["config", "c"]:
            handle_config(args)
            return
    elif hasattr(args, "master_password") and args.master_password:
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
        if args.command in ["generate", "gen", "g"]:
            handle_generate(args, gen)
        elif args.command in ["analyze", "a"]:
            handle_analyze(args, gen)
        elif args.command in ["batch", "b"]:
            handle_batch(args, gen)
        elif args.command in ["history", "h"]:
            if args.history_command == "list" or args.history_command == "l":
                handle_history_list(args, gen)
            elif args.history_command == "search" or args.history_command == "s":
                handle_history_search(args, gen)
            elif args.history_command == "show":
                handle_history_show(args, gen)
            elif args.history_command == "delete" or args.history_command == "d":
                handle_history_delete(args, gen)
            elif args.history_command == "export" or args.history_command == "e":
                handle_history_export(args, gen)
            else:
                parser.parse_args(["history", "--help"])
        elif args.command in ["breach", "b"]:
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
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        if master_password:
            clear_memory(master_password)
        sys.exit(0)
    except (ValueError, ValidationError) as e:
        print(f"[ERROR] {e}")
        if master_password:
            clear_memory(master_password)
        sys.exit(1)
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error in CLI")
        print(f"[ERROR] {e}")
        if master_password:
            clear_memory(master_password)
        sys.exit(1)
    finally:
        if master_password:
            clear_memory(master_password)
            import logging

            logger = logging.getLogger(__name__)
            logger.debug("Master password cleared from memory")


if __name__ == "__main__":
    main_cli()
