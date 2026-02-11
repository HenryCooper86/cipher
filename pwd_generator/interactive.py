import sys
import time
import getpass
import shutil
import subprocess
import platform
import os
from pathlib import Path

from pwd_generator import SecurePasswordGenerator, EncryptionError, ValidationError
from pwd_generator.utils import (
    print_password_stats,
    copy_to_clipboard,
    safe_input,
    safe_getpass,
    prompt_yes_no,
)
from pwd_generator.config import load_config
from pwd_generator.validators import (
    validate_file_path,
    validate_positive_int,
    validate_string,
    validate_length,
)


def get_input(prompt: str) -> str:
    original_response = safe_input(prompt).strip()
    # Check for "esc", "back" or the physical Escape key character (ASCII 27)
    if original_response.lower() in ["esc", "back"] or "\x1b" in original_response:
        return "back"
    return original_response


class BaseMenu:
    def __init__(self, gen, master_password):
        self.gen = gen
        self.master_password = master_password
        self.choices = {}

    def run(self):
        while True:
            self.display()
            choice = get_input(f"\nSelect option (1-{len(self.choices)}): ")

            if choice == "back":
                return

            if choice.isdigit() and int(choice) in self.choices:
                action = self.choices[int(choice)][1]
                if action:
                    try:
                        result = action()
                        if result == "exit":
                            return
                    except (ValueError, ValidationError) as e:
                        print(f"\n[ERROR] {e}")
                    except Exception as e:
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.exception("Unexpected error in menu action")
                        print(f"\n[ERROR] Unexpected error: {e}")
                else:
                    return
            else:
                print("Invalid option. Please try again.")

    def display(self):
        print("\n" + "-" * 60)
        print("OPTIONS:")
        for key, value in self.choices.items():
            print(f"  {key}. {value[0]}")
        print("-" * 60)


class MainMenu(BaseMenu):
    def __init__(self, gen, master_password):
        super().__init__(gen, master_password)
        self.choices = {
            1: ("Generate Random Password", self.generate_random_password),
            2: ("Generate Passphrase", self.generate_passphrase),
            3: ("Generate PIN", self.generate_pin),
            4: ("Generate with Template", self.generate_with_template),
            5: ("Generate with Pattern", self.generate_with_pattern),
            6: ("Generate with Profile", self.generate_with_profile),
            7: ("Analyze Custom Password", self.analyze_custom_password),
            8: ("Check Password Breach", self.check_password_breach),
            9: ("Compare Passwords", self.compare_passwords),
            10: ("Generate QR Code", self.generate_qr_code),
            11: ("View History", self.view_history),
            12: ("Search History", self.search_history),
            13: ("Filter & Sort History", self.filter_and_sort_history),
            14: ("Export History", self.export_history),
            15: ("Import Passwords", self.import_passwords),
            16: ("Security Audit", self.security_audit),
            17: ("Manage History (Delete/Update)", self.manage_history),
            18: ("Batch Generate", self.batch_generate),
            19: ("Configuration", self.configuration),
            20: ("Profiles", self.profiles),
            21: ("Exit", self.exit_menu),
        }

    def generate_random_password(self):
        try:
            length_input = get_input("Password length (default 16): ")
            if length_input == "back":
                return
            length_input = length_input or "16"
            length = validate_positive_int(
                length_input,
                "Password length",
                max_value=self.gen.policy.get("max_length", 128),
            )
            length = validate_length(
                length, 1, self.gen.policy.get("max_length", 128), "Password length"
            )
            pwd = self.gen.generate_random_string(length)
            print_password_stats(self.gen, pwd)

            if prompt_yes_no("Copy to clipboard?", default=True):
                if copy_to_clipboard(pwd):
                    print("Copied to clipboard")
                else:
                    print("Clipboard copy not available")

            if self.master_password and prompt_yes_no("Save to history?", default=True):
                service = validate_string(
                    get_input("Service name: "), "Service name", max_length=200
                )
                notes = validate_string(
                    get_input("Notes (optional): "),
                    "Notes",
                    allow_empty=True,
                    max_length=1000,
                )
                self.gen.add_to_history(pwd, service, notes)
                print("Saved to encrypted history")
        except ValueError:
            print("Invalid length")

    def generate_passphrase(self):
        try:
            num_words_input = get_input("Number of words (default 5): ")
            if num_words_input == "back":
                return
            num_words_input = num_words_input or "5"
            num_words = validate_positive_int(
                num_words_input, "Number of words", max_value=20
            )
            pwd = self.gen.generate_passphrase(num_words)
            print_password_stats(self.gen, pwd)

            if prompt_yes_no("Copy to clipboard?", default=True):
                if copy_to_clipboard(pwd):
                    print("Copied to clipboard")
                else:
                    print("Clipboard copy not available")

            if self.master_password and prompt_yes_no("Save to history?", default=True):
                service = validate_string(
                    get_input("Service name: "), "Service name", max_length=200
                )
                notes = validate_string(
                    get_input("Notes (optional): "),
                    "Notes",
                    allow_empty=True,
                    max_length=1000,
                )
                self.gen.add_to_history(pwd, service, notes)
                print("Saved to encrypted history")
        except ValueError:
            print("Invalid number")

    def generate_pin(self):
        try:
            length_input = get_input("PIN length (default 6): ")
            if length_input == "back":
                return
            length_input = length_input or "6"
            length = validate_positive_int(length_input, "PIN length", max_value=10)
            length = validate_length(length, 4, 10, "PIN length")
            pin = self.gen.generate_pin(length)
            print(f"\nGenerated PIN: {pin}")
            print(f"   Entropy: {self.gen.calculate_entropy(pin):.2f} bits\n")
        except ValueError:
            print("Invalid length")

    def generate_with_template(self):
        from pwd_generator.templates import list_templates, get_template

        templates = list_templates()
        print("\nAvailable Templates:")
        print("-" * 60)
        for i, template_name in enumerate(templates, 1):
            print(f"  {i}. {template_name}")
        print("-" * 60)

        try:
            template_choice = get_input("\nSelect template (number or name): ")
            if template_choice == "back":
                return

            template = None
            if template_choice.isdigit():
                idx = int(template_choice) - 1
                if 0 <= idx < len(templates):
                    template = get_template(templates[idx])
            else:
                template = get_template(template_choice)

            if not template:
                print("Invalid template selection")
                return

            length_input = get_input(
                f"Password length (min {template.min_length}, default 16): "
            )
            if length_input == "back":
                return
            length_input = length_input or "16"
            length = validate_positive_int(
                length_input,
                "Password length",
                max_value=self.gen.policy.get("max_length", 128),
            )
            length = validate_length(
                length,
                template.min_length,
                self.gen.policy.get("max_length", 128),
                "Password length",
            )

            pwd = template.generate(length)
            print_password_stats(self.gen, pwd)

            if prompt_yes_no("Copy to clipboard?", default=True):
                if copy_to_clipboard(pwd):
                    print("Copied to clipboard")
                else:
                    print("Clipboard copy not available")

            if self.master_password and prompt_yes_no("Save to history?", default=True):
                service = validate_string(
                    get_input("Service name: "), "Service name", max_length=200
                )
                notes = validate_string(
                    get_input("Notes (optional): "),
                    "Notes",
                    allow_empty=True,
                    max_length=1000,
                )
                self.gen.add_to_history(pwd, service, notes)
                print("Saved to encrypted history")
        except ValueError as e:
            print(f"Invalid input: {e}")
        except (OSError, IOError) as e:
            print(f"File operation error: {e}")
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.exception("Unexpected error in template generation")
            print(f"[ERROR] Unexpected error: {e}")

    def generate_with_pattern(self):
        from pwd_generator.patterns import PatternGenerator
        from pwd_generator.visualization import print_enhanced_password_stats

        pattern = get_input("Enter pattern: ")
        if pattern == "back":
            return

        try:
            generator = PatternGenerator()
            pwd = generator.generate_from_pattern(pattern)

            print_enhanced_password_stats(self.gen, pwd)

            if prompt_yes_no("Copy to clipboard?", default=True):
                if copy_to_clipboard(pwd):
                    print("Copied to clipboard")

            if self.master_password and prompt_yes_no("Save to history?", default=True):
                service = get_input("Service name: ").strip()
                notes = get_input("Notes (optional): ").strip()
                self.gen.add_to_history(pwd, service, notes)
                print("Saved to encrypted history")
        except Exception as e:
            print(f"Error generating from pattern: {e}")

    def generate_with_profile(self):
        from pwd_generator.profiles import ProfileManager

        manager = ProfileManager()
        profiles = manager.list_profiles()

        print("\nAvailable Profiles:")
        print("-" * 60)
        for i, profile_name in enumerate(profiles, 1):
            profile = manager.get_profile(profile_name)
            print(f"  {i}. {profile_name}")
            if profile:
                print(
                    f"     Min Length: {profile.policy.get('min_length', 'N/A')}, "
                    f"Min Entropy: {profile.policy.get('min_entropy', 'N/A')}, "
                    f"Template: {profile.template or 'None'}"
                )
        print("-" * 60)

        profile_choice = get_input("\nSelect profile (number or name): ")
        if profile_choice == "back":
            return

        profile = None
        if profile_choice.isdigit():
            idx = int(profile_choice) - 1
            if 0 <= idx < len(profiles):
                profile = manager.get_profile(profiles[idx])
        else:
            profile = manager.get_profile(profile_choice)

        if not profile:
            print("Invalid profile selection")
            return

        gen_with_profile = SecurePasswordGenerator(
            master_password=self.master_password,
            policy=profile.policy,
            profile=profile.name,
        )

        if profile.template:
            from pwd_generator.templates import get_template

            template = get_template(profile.template)
            if template:
                length_input = get_input(
                    f"Password length (min {template.min_length}, default 16): "
                )
                if length_input == "back":
                    return
                length_input = length_input or "16"
                length = validate_positive_int(
                    length_input,
                    "Password length",
                    max_value=gen_with_profile.policy.get("max_length", 128),
                )
                length = validate_length(
                    length,
                    template.min_length,
                    gen_with_profile.policy.get("max_length", 128),
                    "Password length",
                )
                pwd = template.generate(length)
            else:
                length_input = get_input(
                    f"Password length (min {profile.policy.get('min_length', 12)}, default 16): "
                )
                if length_input == "back":
                    return
                length_input = length_input or "16"
                length = validate_positive_int(
                    length_input,
                    "Password length",
                    max_value=gen_with_profile.policy.get("max_length", 128),
                )
                length = validate_length(
                    length,
                    profile.policy.get("min_length", 12),
                    gen_with_profile.policy.get("max_length", 128),
                    "Password length",
                )
                pwd = gen_with_profile.generate_random_string(length)
        else:
            length_input = get_input(
                f"Password length (min {profile.policy.get('min_length', 12)}, default 16): "
            )
            if length_input == "back":
                return
            length_input = length_input or "16"
            length = validate_positive_int(
                length_input,
                "Password length",
                max_value=gen_with_profile.policy.get("max_length", 128),
            )
            length = validate_length(
                length,
                profile.policy.get("min_length", 12),
                gen_with_profile.policy.get("max_length", 128),
                "Password length",
            )
            pwd = gen_with_profile.generate_random_string(length)

        from pwd_generator.visualization import print_enhanced_password_stats

        print_enhanced_password_stats(gen_with_profile, pwd)

        if prompt_yes_no("Copy to clipboard?", default=True):
            if copy_to_clipboard(pwd):
                print("Copied to clipboard")

        if self.master_password and prompt_yes_no("Save to history?", default=True):
            service = get_input("Service name: ").strip()
            notes = get_input("Notes (optional): ").strip()
            self.gen.add_to_history(pwd, service, notes)
            print("Saved to encrypted history")

    def analyze_custom_password(self):
        pwd_bytes = safe_getpass("Enter password to analyze: ")
        pwd = pwd_bytes.decode("utf-8")
        from pwd_generator.visualization import print_enhanced_password_stats

        print_enhanced_password_stats(self.gen, pwd)

    def check_password_breach(self):
        pwd_bytes = safe_getpass("Enter password to check: ")
        pwd = pwd_bytes.decode("utf-8")
        is_breached, details = self.gen.check_password_breach(pwd)

        print(f"\n{'=' * 70}")
        print(f"                    BREACH CHECK RESULT")
        print(f"{'=' * 70}")

        if details.get("error"):
            print(f"\n[WARNING] Status: Error")
            print(f"   {details['message']}")
        elif is_breached:
            print(f"\n[WARNING] Status: BREACHED")
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

    def compare_passwords(self):
        passwords = []
        print("\nCompare Passwords")
        print("-" * 60)
        print("Enter passwords to compare (press Enter with empty line to finish):")

        while True:
            pwd_bytes = safe_getpass(
                f"Password {len(passwords) + 1} (or Enter to finish): "
            )
            if not pwd_bytes:
                break
            passwords.append(pwd_bytes.decode("utf-8"))

        if len(passwords) < 2:
            print("Need at least 2 passwords to compare")
            return

        print(f"\n{'=' * 70}")
        print(f"                    PASSWORD COMPARISON")
        print(f"{'=' * 70}\n")

        results = []
        for pwd in passwords:
            stats = self.gen.get_password_stats(pwd)
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

    def generate_qr_code(self):
        from pwd_generator.qr_code import (
            generate_qr_code,
            generate_wifi_qr,
        )
        import os

        print("\nGenerate QR Code")
        print("-" * 60)
        print("  1. Password QR code")
        print("  2. WiFi QR code")
        qr_type = get_input("Select type (1-2): ")
        if qr_type == "back":
            return

        if qr_type == "1":
            pwd_bytes = safe_getpass("Enter password: ")
            pwd = pwd_bytes.decode("utf-8")
            if not pwd:
                print("[ERROR] No password provided")
                return

            output = get_input("Output filename (Enter for auto-generated): ").strip()
            filename = output if output else None

            print("\nGenerating QR code...")
            qr_file = generate_qr_code(pwd, filename)

            if qr_file:
                print(f"[OK] QR code saved to {qr_file}")
        elif qr_type == "2":
            ssid = get_input("WiFi SSID: ").strip()
            if not ssid:
                print("[ERROR] SSID required")
                return

            password_bytes = safe_getpass("WiFi Password: ")
            password = password_bytes.decode("utf-8")
            if not password:
                print("[ERROR] Password required")
                return

            security = (
                get_input("Security type (WPA/WEP/nopass, default WPA): ").strip()
                or "WPA"
            )
            hidden = get_input("Hidden network? (y/n, default n): ").lower() == "y"

            print("\nGenerating WiFi QR code...")
            qr_file = generate_wifi_qr(ssid, password, security, hidden)

            if qr_file:
                print(f"[OK] WiFi QR code saved to {qr_file}")
        else:
            print("Invalid QR code type.")

    def view_history(self):
        if not self.gen.history:
            print("\nNo password history available")
        else:
            from pwd_generator.age_calculator import (
                calculate_password_age,
                format_age,
            )

            print(f"\nPassword History ({len(self.gen.history)} entries)")
            print("-" * 70)
            for i, entry in enumerate(self.gen.history[:20], 1):
                meta = entry["metadata"]
                age_info = calculate_password_age(meta.get("created_at", ""))
                age_str = format_age(age_info)
                qr_indicator = "[QR]" if meta.get("qr_code_path") else "  "
                print(
                    f"{i:2d}. {qr_indicator} {meta['service']:23s} | {age_str:15s} | {meta['strength']:12s} | {meta['entropy']:.1f} bits"
                )
            if len(self.gen.history) > 20:
                print(f"\n... and {len(self.gen.history) - 20} more entries")

            try:
                selection = get_input(
                    "\nEnter number to view password (or press Enter to skip): "
                ).strip()
                if selection and selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(self.gen.history):
                        entry = self.gen.history[idx]
                        meta = entry["metadata"]
                        age_info = calculate_password_age(meta.get("created_at", ""))
                        print(f"\n{'=' * 70}")
                        print(f"Service:    {meta['service']}")
                        print(f"Created:    {meta['created_at']}")
                        print(f"Age:        {format_age(age_info)}")
                        print(
                            f"Strength:   {meta['strength']} ({meta['entropy']:.1f} bits)"
                        )
                        print(f"Notes:      {meta.get('notes', 'N/A')}")
                        print(f"Password:   {entry['password']}")
                        print(f"{'=' * 70}")
                    else:
                        print("Invalid number")
            except ValueError:
                pass

    def search_history(self):
        if not self.gen.history:
            print("\nNo password history available")
        else:
            query = get_input("Search (service name or notes): ").strip().lower()
            if query == "back":
                return

            results = []
            for e in self.gen.history:
                meta = e["metadata"]
                match_field = None
                if query in meta["service"].lower():
                    match_field = "service"
                elif query in meta.get("notes", "").lower():
                    match_field = "notes"

                if match_field:
                    results.append((e, match_field))

            if not results:
                print(f"\nNo results found for '{query}'")
            else:
                print(f"\nFound {len(results)} result(s)")
                print("-" * 60)
                for i, (entry, match_field) in enumerate(results, 1):
                    meta = entry["metadata"]
                    print(f"{i}. {meta['service']} [matched in: {match_field}]")
                    print(f"   Created: {meta['created_at']}")
                    print(
                        f"   Strength: {meta['strength']} ({meta['entropy']:.1f} bits)"
                    )
                    if meta.get("notes"):
                        print(f"   Notes: {meta['notes']}")

                    if prompt_yes_no("   Show password?", default=False):
                        print(f"   Password: {entry['password']}")
                    print()

    def filter_and_sort_history(self):
        from pwd_generator.filters import (
            filter_history_by_service,
            filter_history_by_strength,
            filter_history_by_entropy,
            sort_history,
        )

        if not self.gen.history:
            print("\nNo password history available")
        else:
            print("\nFilter & Sort History")
            print("-" * 60)

            filtered = self.gen.history.copy()

            print("\nFilter Options:")
            print("  1. By service name")
            print("  2. By minimum strength")
            print("  3. By minimum entropy")
            print("  4. Skip filtering")
            filter_choice = get_input("Select filter (1-4): ")
            if filter_choice == "back":
                return

            if filter_choice == "1":
                service_query = get_input("Service name to filter: ").strip()
                filtered = filter_history_by_service(filtered, service_query)
            elif filter_choice == "2":
                print("\nStrength levels: Weak, Fair, Good, Strong, Very Strong")
                min_strength = get_input("Minimum strength: ").strip()
                filtered = filter_history_by_strength(filtered, min_strength)
            elif filter_choice == "3":
                try:
                    min_entropy = float(get_input("Minimum entropy: ").strip())
                    filtered = filter_history_by_entropy(filtered, min_entropy)
                except ValueError:
                    print("Invalid entropy value")

            print("\nSort Options:")
            print("  1. By date")
            print("  2. By service name")
            print("  3. By strength")
            print("  4. By entropy")
            sort_choice = get_input("Select sort (1-4): ")
            if sort_choice == "back":
                return

            sort_map = {
                "1": "date",
                "2": "service",
                "3": "strength",
                "4": "entropy",
            }
            sort_by = sort_map.get(sort_choice, "date")

            reverse = prompt_yes_no("Reverse order?", default=False)
            filtered = sort_history(filtered, sort_by, reverse)

            if not filtered:
                print("\nNo entries match the filter criteria")
            else:
                print(f"\nFiltered History ({len(filtered)} entries)")
                print("-" * 60)
                for i, entry in enumerate(filtered[:20], 1):
                    meta = entry["metadata"]
                    print(
                        f"{i:2d}. {meta['service']:30s} | {meta['created_at'][:10]} | {meta['strength']:12s} | {meta['entropy']:.1f} bits"
                    )
                if len(filtered) > 20:
                    print(f"\n... and {len(filtered) - 20} more entries")

    def export_history(self):
        from pwd_generator.export import export_history_json, export_history_csv
        from pwd_generator.filters import (
            filter_history_by_service,
            filter_history_by_strength,
            filter_history_by_entropy,
            sort_history,
        )

        if not self.gen.history:
            print("\nNo password history available")
        else:
            print("\nExport History")
            print("-" * 60)

            filtered = self.gen.history.copy()

            apply_filters = prompt_yes_no(
                "\nApply filters before export?", default=False
            )

            if apply_filters:
                print("\nFilter Options:")
                print("  1. By service name")
                print("  2. By minimum strength")
                print("  3. By minimum entropy")
                print("  4. Skip filtering")
                filter_choice = get_input("Select filter (1-4): ")
                if filter_choice == "back":
                    return

                if filter_choice == "1":
                    service_query = get_input("Service name to filter: ").strip()
                    filtered = filter_history_by_service(filtered, service_query)
                elif filter_choice == "2":
                    print("\nStrength levels: Weak, Fair, Good, Strong, Very Strong")
                    min_strength = get_input("Minimum strength: ").strip()
                    filtered = filter_history_by_strength(filtered, min_strength)
                elif filter_choice == "3":
                    try:
                        min_entropy = float(get_input("Minimum entropy: ").strip())
                        filtered = filter_history_by_entropy(filtered, min_entropy)
                    except ValueError:
                        print("Invalid entropy value")

                sort_map = {
                    "1": "date",
                    "2": "service",
                    "3": "strength",
                    "4": "entropy",
                }
                print("\nSort Options:")
                print("  1. By date")
                print("  2. By service name")
                print("  3. By strength")
                print("  4. By entropy")
                sort_choice = get_input("Select sort (1-4): ")
                if sort_choice == "back":
                    return
                sort_by = sort_map.get(sort_choice, "date")
                reverse = prompt_yes_no("Reverse order?", default=False)
                filtered = sort_history(filtered, sort_by, reverse)

            if not filtered:
                print("\nNo entries to export")
                return

            print("\nExport Format:")
            print("  1. JSON")
            print("  2. CSV")
            format_choice = get_input("Select format (1-2): ")
            if format_choice == "back":
                return

            filename = get_input("Output filename: ").strip()
            if not filename:
                print("Export cancelled")
                return

            try:
                safe_path = validate_file_path(filename, base_dir=Path.cwd())
                filename = str(safe_path)
            except ValueError as e:
                print(f"[ERROR] Invalid file path: {e}")
                return

            include_passwords = prompt_yes_no("Include passwords?", default=True)

            if format_choice == "1":
                if export_history_json(filtered, filename, include_passwords):
                    print(
                        f"\n[OK] Exported {len(filtered)} entries to {filename} (JSON)"
                    )
                else:
                    print(f"\nError: Failed to export to {filename}")
            elif format_choice == "2":
                if export_history_csv(filtered, filename, include_passwords):
                    print(
                        f"\n[OK] Exported {len(filtered)} entries to {filename} (CSV)"
                    )
                else:
                    print(f"\nError: Failed to export to {filename}")
            else:
                print("Invalid format selection")

    def import_passwords(self):
        from pwd_generator.import_export import (
            import_from_csv,
            import_from_json,
        )

        if not self.gen.encryption_manager.cipher:
            print(
                "\nError: Encryption not initialized. Cannot import without master password."
            )
            return

        print("\nImport Passwords")
        print("-" * 60)
        filename = get_input("File to import: ").strip()
        if not filename:
            return

        try:
            safe_path = validate_file_path(
                filename, base_dir=Path.cwd(), must_exist=True
            )
            filename = str(safe_path)
        except ValueError as e:
            print(f"[ERROR] Invalid file path: {e}")
            return

        print("\nImport Format:")
        print("  1. CSV (generic)")
        print("  2. JSON")
        print("  3. 1Password CSV")
        print("  4. LastPass CSV")
        print("  5. Bitwarden CSV")
        format_choice = get_input("Select format (1-5): ")
        if format_choice == "back":
            return

        format_map = {
            "1": ("csv", "generic"),
            "2": ("json", None),
            "3": ("csv", "1password"),
            "4": ("csv", "lastpass"),
            "5": ("csv", "bitwarden"),
        }

        try:
            if format_choice == "2":
                entries = import_from_json(filename)
            else:
                fmt_type = format_map.get(format_choice, ("csv", "generic"))[1]
                entries = import_from_csv(filename, fmt_type)

            imported = 0
            for entry in entries:
                self.gen.add_to_history(
                    entry["password"],
                    entry["metadata"].get("service", ""),
                    entry["metadata"].get("notes", ""),
                )
                imported += 1

            print(f"[OK] Imported {imported} passwords from {filename}")
        except Exception as e:
            print(f"[ERROR] Error importing: {e}")

    def security_audit(self):
        from pwd_generator.audit import PasswordAuditor

        print("\nRunning Security Audit...")
        auditor = PasswordAuditor(self.gen)
        report = auditor.generate_audit_report()

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

        if prompt_yes_no("\nExport report to file?", default=False):
            filename = get_input("Filename: ").strip()
            if filename:
                try:
                    safe_path = validate_file_path(filename, base_dir=Path.cwd())
                    filename = str(safe_path)
                    import json

                    with open(filename, "w") as f:
                        json.dump(report, f, indent=2)
                    print(f"[OK] Report saved to {filename}")
                except ValueError as e:
                    print(f"[ERROR] Invalid file path: {e}")
                except (OSError, IOError) as e:
                    print(f"[ERROR] Failed to save report: {e}")

        print(f"\n{'=' * 70}\n")

    def manage_history(self):
        if not self.gen.history:
            print("\nNo password history available")
        else:
            print("\nManage History")
            print("-" * 60)
            for i, entry in enumerate(self.gen.history[:20], 1):
                meta = entry["metadata"]
                print(f"{i:2d}. {meta['service']:20s} | {meta['created_at'][:10]}")

            try:
                idx_input = get_input("\nSelect entry number (0 to cancel): ")
                if idx_input == "back" or idx_input == "0":
                    return
                idx = int(idx_input) - 1

                if 0 <= idx < len(self.gen.history):
                    print("\n1. Delete entry")
                    print("2. Update service name")
                    print("3. Update notes")
                    action = get_input("Select action: ").strip()

                    if action == "1":
                        if prompt_yes_no(
                            f"Delete '{self.gen.history[idx]['metadata']['service']}'?",
                            default=False,
                        ):
                            if self.gen.delete_from_history(idx):
                                print("Entry deleted")

                    elif action == "2":
                        new_service = validate_string(
                            get_input("New service name: "),
                            "Service name",
                            max_length=200,
                        )
                        if self.gen.update_history_entry(idx, service=new_service):
                            print("Service name updated")

                    elif action == "3":
                        new_notes = validate_string(
                            get_input("New notes: "),
                            "Notes",
                            allow_empty=True,
                            max_length=1000,
                        )
                        if self.gen.update_history_entry(idx, notes=new_notes):
                            print("Notes updated")
                else:
                    print("Invalid entry number")
            except ValueError:
                print("Invalid input")

    def batch_generate(self):
        from pwd_generator.export import (
            export_passwords_json,
            export_passwords_csv,
        )

        try:
            count_input = (
                get_input("How many passwords to generate? (default 10): ") or "10"
            )
            if count_input == "back":
                return
            count = validate_positive_int(count_input, "Count", max_value=1000)
            print("\n1. Random passwords")
            print("2. Passphrases")
            print("3. PINs")
            pwd_type_choice = get_input("Select type: ")
            if pwd_type_choice == "back":
                return

            type_map = {"1": "random", "2": "passphrase", "3": "pin"}
            pwd_type = type_map.get(pwd_type_choice, "random")

            length = 16
            if pwd_type == "random":
                length_input = get_input("Password length (default 16): ") or "16"
                if length_input == "back":
                    return
                length = validate_positive_int(
                    length_input,
                    "Password length",
                    max_value=self.gen.policy.get("max_length", 128),
                )
                length = validate_length(
                    length,
                    1,
                    self.gen.policy.get("max_length", 128),
                    "Password length",
                )
            elif pwd_type == "pin":
                length_input = get_input("PIN length (default 6): ") or "6"
                if length_input == "back":
                    return
                length = validate_positive_int(length_input, "PIN length", max_value=10)
                length = validate_length(length, 4, 10, "PIN length")

            print(f"\nGenerating {count} {pwd_type} passwords...")
            passwords = self.gen.batch_generate(
                count, length, pwd_type, show_progress=True
            )

            print(f"\nGenerated {len(passwords)} passwords:")
            print("-" * 60)
            for i, pwd in enumerate(passwords[:20], 1):
                print(f"{i:2d}. {pwd}")
            if len(passwords) > 20:
                print(f"... and {len(passwords) - 20} more")

            if prompt_yes_no("\nExport to file?", default=True):
                print("\nExport Format:")
                print("  1. Plain text (TXT)")
                print("  2. JSON")
                print("  3. CSV")
                format_choice = get_input("Select format (1-3): ")
                if format_choice == "back":
                    return

                filename = get_input("Filename: ").strip()
                if not filename:
                    print("Export cancelled")
                    return

                try:
                    safe_path = validate_file_path(filename, base_dir=Path.cwd())
                    filename = str(safe_path.resolve())
                except ValueError as e:
                    print(f"[ERROR] Invalid file path: {e}")
                    return

                print(f"\nSave location: {filename}")
                if not prompt_yes_no("Proceed with export?", default=True):
                    print("Export cancelled")
                    return

                if format_choice == "1":
                    try:
                        with open(filename, "w") as f:
                            for pwd in passwords:
                                f.write(pwd + "\n")
                        print(f"[OK] Exported to {filename}")
                    except (OSError, IOError) as e:
                        print(f"[ERROR] Failed to export: {e}")
                elif format_choice == "2":
                    if export_passwords_json(passwords, filename):
                        print(f"[OK] Exported to {filename} (JSON)")
                    else:
                        print(f"[ERROR] Failed to export to {filename}")
                elif format_choice == "3":
                    if export_passwords_csv(passwords, filename):
                        print(f"[OK] Exported to {filename} (CSV)")
                    else:
                        print(f"[ERROR] Failed to export to {filename}")
                else:
                    print("Invalid format selection")

            if self.master_password and prompt_yes_no(
                "\nSave this batch to history for later finding?", default=False
            ):
                from datetime import datetime

                default_label = f"Batch {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                label_prompt = (
                    f"Label for this batch (default: {default_label}): "
                )
                batch_label = get_input(label_prompt).strip() or default_label
                if batch_label == "back":
                    pass
                else:
                    for i, pwd in enumerate(passwords, 1):
                        self.gen.add_to_history(
                            pwd,
                            service=batch_label,
                            notes=f"Batch item {i}",
                        )
                    print(
                        f"[OK] Saved {len(passwords)} passwords to history under '{batch_label}'"
                    )
                    print("Search history for this label to find them later.")

        except ValueError:
            print("Invalid input")

    def configuration(self):
        from pwd_generator.config import save_config, create_default_config

        print("\nConfiguration Management")
        print("-" * 60)
        print("  1. View current configuration")
        print("  2. Create default configuration file")
        print("  3. Load configuration from file")
        config_choice = get_input("Select option (1-3): ")
        if config_choice == "back":
            return

        if config_choice == "1":
            config = load_config()
            import json

            print("\nCurrent Configuration:")
            print("=" * 60)
            print(json.dumps(config, indent=2))
            print("=" * 60)
        elif config_choice == "2":
            config_file = get_input("Config file path (Enter for default): ").strip()
            if not config_file:
                config_file = None
            else:
                try:
                    safe_path = validate_file_path(config_file, base_dir=Path.home())
                    config_file = str(safe_path)
                except ValueError as e:
                    print(f"[ERROR] Invalid config file path: {e}")
                    return
            if create_default_config(config_file):
                print(f"[OK] Created default configuration file")
            else:
                print("[ERROR] Failed to create configuration file")
        elif config_choice == "3":
            config_file = get_input("Config file path: ").strip()
            if config_file:
                try:
                    safe_path = validate_file_path(config_file, base_dir=Path.home())
                    config_file = str(safe_path)
                except ValueError as e:
                    print(f"[ERROR] Invalid config file path: {e}")
                    return
                config = load_config(config_file)
                print(f"[OK] Loaded configuration from {config_file}")
                print("Note: Configuration is loaded automatically on startup")
            else:
                print("Invalid file path")

    def profiles(self):
        from pwd_generator.profiles import ProfileManager, PasswordProfile

        manager = ProfileManager()

        print("\nPassword Profiles")
        print("-" * 60)
        print("  1. List profiles")
        print("  2. Show profile details")
        print("  3. Create new profile")
        profile_choice = get_input("Select option (1-3): ")
        if profile_choice == "back":
            return

        if profile_choice == "1":
            profiles = manager.list_profiles()
            print("\nAvailable Profiles:")
            print("-" * 60)
            for profile_name in profiles:
                profile = manager.get_profile(profile_name)
                print(f"  • {profile_name}")
                if profile:
                    print(
                        f"    - Min Length: {profile.policy.get('min_length', 'N/A')}"
                    )
                    print(
                        f"    - Min Entropy: {profile.policy.get('min_entropy', 'N/A')}"
                    )
                    print(f"    - Template: {profile.template or 'None'}")
            print()
        elif profile_choice == "2":
            name = get_input("Profile name: ").strip()
            profile = manager.get_profile(name)
            if profile:
                import json

                print(f"\nProfile: {profile.name}")
                print("=" * 60)
                print(json.dumps(profile.to_dict(), indent=2))
                print("=" * 60)
            else:
                print(f"Profile '{name}' not found")
        elif profile_choice == "3":
            name = validate_string(
                get_input("Profile name: "), "Profile name", max_length=100
            )
            try:
                min_length_input = get_input("Min length (Enter to skip): ") or "0"
                min_length = int(min_length_input) if min_length_input.isdigit() else 0
                if min_length > 0:
                    min_length = validate_positive_int(
                        str(min_length), "Min length", max_value=128
                    )

                min_entropy_input = get_input("Min entropy (Enter to skip): ") or "0"
                try:
                    min_entropy = float(min_entropy_input) if min_entropy_input else 0.0
                except ValueError:
                    min_entropy = 0.0

                template_input = get_input("Template name (Enter to skip): ").strip()
                template = (
                    validate_string(
                        template_input,
                        "Template name",
                        allow_empty=True,
                        max_length=100,
                    )
                    if template_input
                    else None
                )

                policy = {}
                if min_length > 0:
                    policy["min_length"] = min_length
                if min_entropy > 0:
                    policy["min_entropy"] = min_entropy

                profile = PasswordProfile(name, policy, template)
                if manager.add_profile(profile):
                    print(f"[OK] Created profile '{name}'")
                else:
                    print("[ERROR] Failed to create profile")
            except ValueError:
                print("Invalid input")

    def exit_menu(self):
        print("\nGoodbye! Stay secure!")
        sys.exit(0)


def main_interactive():
    try:
        print("=" * 60)
        print("           HORIZON SECURE PASSWORD GENERATOR            ")
        print("=" * 60)
        print()

        history_exists = Path("password_history.enc").exists()

        config = load_config()
        policy = config.get("policy", {})

        gen = None
        master_password = None

        if not history_exists:
            print(
                "Welcome! This appears to be your first time using the password generator."
            )
            print("Let's create a master password to encrypt your password history.")
            print()

            while True:
                master_password_bytes = safe_getpass(
                    "Create a master password (12+ chars): "
                )
                master_password = master_password_bytes.decode("utf-8")

                if not master_password:
                    print("Proceeding without encrypted history")
                    break

                confirm_bytes = safe_getpass("Confirm master password: ")
                confirm = confirm_bytes.decode("utf-8")

                if master_password != confirm:
                    print("Passwords don't match. Please try again.")
                    print()
                    continue

                try:
                    gen = SecurePasswordGenerator(
                        master_password=master_password, policy=policy
                    )
                    print("Master password created successfully!")
                    print()
                    break
                except ValidationError as e:
                    print(f"{e}")
                    if not prompt_yes_no("Try again?", default=True):
                        print("Proceeding without encrypted history")
                        master_password = None
                        break
        else:
            while True:
                master_password_bytes = safe_getpass(
                    "Enter master password for history (12+ chars): "
                )
                master_password = master_password_bytes.decode("utf-8")

                if not master_password:
                    print("Proceeding without encrypted history")
                    break
                try:
                    gen = SecurePasswordGenerator(
                        master_password=master_password, policy=policy
                    )
                    break
                except ValidationError as e:
                    print(f"Master password validation failed: {e}")
                    if not prompt_yes_no("Try again?", default=True):
                        print("Proceeding without encrypted history")
                        master_password = None
                        break

                except EncryptionError as e:
                    print(f"{e}")
                    print("\nThis usually means:")
                    print("  - You entered a different master password than before")
                    print("  - The history file is corrupted")
                    print("\nOptions:")
                    print("  1. Try entering the correct master password")
                    print("  2. Start fresh (will backup old history)")
                    print("  3. Exit")

                    choice = get_input("Select option (1-3): ")

                    if choice == "1":
                        continue
                    elif choice == "2":
                        history_file = Path("password_history.enc")
                        if history_file.exists():
                            try:
                                backup_file = Path(
                                    f"password_history.enc.backup.{int(time.time())}"
                                )
                                shutil.copy(history_file, backup_file)
                                print(f"Backed up old history to {backup_file}")
                                history_file.unlink()
                                print("Starting with fresh history")
                            except (OSError, IOError) as e:
                                print(f"Error handling history file backup: {e}")
                                print("Proceeding without backup...")
                                history_file.unlink(missing_ok=True)
                        try:
                            gen = SecurePasswordGenerator(
                                master_password=master_password, policy=policy
                            )
                            break
                        except Exception as e:
                            print(f"Still failed: {e}")
                            print("Proceeding without encrypted history")
                            master_password = None
                            break
                    else:
                        print("Exiting...")
                        sys.exit(0)

        if not master_password and not gen:
            gen = SecurePasswordGenerator(policy=policy)

        if gen and master_password:
            expired = gen.get_expired_passwords()
            if expired:
                print(
                    f"\nWarning: {len(expired)} password(s) have expired (>{gen.policy['expiration_days']} days old)"
                )

        main_menu = MainMenu(gen, master_password)
        main_menu.run()

    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
    except (ValueError, ValidationError) as e:
        print(f"\nValidation error: {e}")
    except (OSError, IOError) as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"File operation error: {e}")
        print(f"\nFile operation error: {e}")
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error in interactive mode")
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_interactive()
