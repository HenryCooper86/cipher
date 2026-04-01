import sys
from pathlib import Path

from pwd_generator import SecurePasswordGenerator
from pwd_generator.utils import (
    copy_to_clipboard,
    print_password_stats,
    prompt_yes_no,
    safe_input,
)
from pwd_generator.validators import (
    validate_file_path,
    validate_length,
    validate_positive_int,
)


def _escape_wifi_value(value: str) -> str:
    """Escape special characters for WiFi QR code format."""
    for char in "\\;,\":":
        value = value.replace(char, "\\" + char)
    return value


def handle_generate(args, gen: SecurePasswordGenerator) -> None:
    quiet = getattr(args, "quiet", False)
    json_output = getattr(args, "json", False)

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
    from pwd_generator.export import export_passwords_csv, export_passwords_json

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
                with open(safe_output_path, "w", encoding="utf-8") as f:
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
    from pwd_generator.export import export_history_csv, export_history_json
    from pwd_generator.filters import (
        filter_history_by_entropy,
        filter_history_by_service,
        filter_history_by_strength,
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
    print("                    BREACH CHECK RESULT")
    print(f"{'=' * 70}")

    if details.get("error"):
        print("\n[WARNING]  Status: Error")
        print(f"   {details['message']}")
    elif is_breached:
        print("\n[WARNING]  Status: BREACHED")
        print(f"   {details['message']}")
        print("\n   Details:")
        print(f"   • Breach Count: {details['count']:,} occurrences")
        print(f"   • Hash Prefix Checked: {details['hash_prefix']}****")
        print(f"   • Checked At: {details['timestamp']}")
    else:
        print("\n[OK] Status: SAFE")
        print(f"   {details['message']}")
        print("\n   Details:")
        print(f"   • Hash Prefix Checked: {details['hash_prefix']}****")
        print(f"   • Checked At: {details['timestamp']}")

    if details.get("recommendations"):
        print("\n   Recommendations:")
        for i, rec in enumerate(details["recommendations"], 1):
            print(f"   {i}. {rec}")

    print("\n   Security Note:")
    print("   • This check uses k-anonymity (only first 5 chars of hash sent)")
    print("   • Your full password never leaves your device")
    print("   • Data source: Have I Been Pwned (haveibeenpwned.com)")

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
            print("Usage: horizon-cipher template <template_name> --length <length>")
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
    from pwd_generator.config import create_default_config, load_config

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
    from pwd_generator.profiles import PasswordProfile, ProfileManager

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
            print("[ERROR] Failed to create profile")
            sys.exit(1)


def handle_audit(args, gen: SecurePasswordGenerator) -> None:
    import json

    from pwd_generator.audit import PasswordAuditor, format_audit_console_report

    auditor = PasswordAuditor(gen)
    report = auditor.generate_audit_report()

    if args.format == "json":
        output = json.dumps(report, indent=2)
        if args.output:
            try:
                safe_output_path = validate_file_path(args.output)
                with open(safe_output_path, "w", encoding="utf-8") as f:
                    f.write(output)
                print(f"[OK] Audit report saved to {safe_output_path}")
            except ValueError as e:
                print(f"[ERROR] Security policy violation - {e}")
                sys.exit(1)
        else:
            print(output)
    else:
        text = format_audit_console_report(report)
        print(text, end="")

        if args.output:
            try:
                safe_output_path = validate_file_path(args.output)
                with open(safe_output_path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"[OK] Report saved to {safe_output_path}")
            except ValueError as e:
                print(f"[ERROR] Security policy violation - {e}")
                sys.exit(1)


def handle_import(args, gen: SecurePasswordGenerator) -> None:
    from pwd_generator.import_export import import_from_csv, import_from_json

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
    import os

    from pwd_generator.qr_code import (
        display_qr_code,
        generate_qr_code,
        generate_wifi_qr,
        qr_code_to_ascii,
    )

    if args.wifi:
        if not args.ssid:
            print("[ERROR] --ssid required when using --wifi")
            sys.exit(1)
        escaped_ssid = _escape_wifi_value(args.ssid)
        escaped_password = _escape_wifi_value(args.password)
        wifi_string = f"WIFI:T:{args.security};S:{escaped_ssid};P:{escaped_password};H:{'true' if args.hidden else 'false'};;"
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
        print("                    QR CODE GENERATED")
        print(f"{'=' * 70}")

        if ascii_qr:
            print("\n[QR] QR CODE (Scan with your phone):")
            print("-" * 70)
            print(ascii_qr)
            print("-" * 70)

        print("\n[OK] QR code saved successfully!")
        print("\nFile Location:")
        print(f"   {abs_path}")
        print("\nDirectory:")
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
    print("                    PASSWORD COMPARISON")
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

