# Horizon Cypher

**Secure password generator** with encrypted saved passwords, CLI, optional desktop GUI, breach checks, QR codes, and security audits.

---

## Quick Start

### Run the Application

| Mode | Command |
|------|---------|
| **GUI** (after `pip install -e ".[gui]"`) | `horizon-cipher-gui` or `python gui.py` |
| **CLI** (full application) | `horizon-cipher` or `python cipher.py` |
| **Minimal demo** (stdlib only) | `python simple_cipher.py` |

> **Note:** First full-app run asks for a master password (12+ characters) to encrypt your history file.

---

## Installation

### Requirements

- Python 3.9 or higher

### Install Commands

```bash
# Basic installation
pip install -e .

# With GUI support (PyQt6)
pip install -e ".[gui]"

# With Argon2 KDF (recommended for better security)
pip install -e ".[argon2]"

# Development dependencies
pip install -e ".[dev]"
```

---

## Usage Examples

### Generate Passwords

```bash
# Random password (20 characters)
horizon-cipher generate --length 20

# Passphrase (5 words)
horizon-cipher generate --type passphrase --words 5

# PIN code (6 digits)
horizon-cipher generate --type pin --length 6
```

### Analyze & Check

```bash
# Analyze password strength
horizon-cipher analyze "your-password-here"

# Check if password was in a breach
horizon-cipher breach "your-password-here"
```

### Manage History

```bash
# List saved passwords
horizon-cipher history list

# Search in history
horizon-cipher history search gmail
```

### Interactive Mode

```bash
# Run with interactive menu
horizon-cipher

# Or
python cipher.py
```

---

## Features

- **Password Generation:** Random passwords, passphrases, PINs, patterns, templates, and profiles
- **Encrypted Storage:** PBKDF2 or Argon2 + Fernet encryption for your password history
- **History Management:** Search, filter, sort, import, and export (JSON, CSV, and common manager formats)
- **Security Analysis:** Strength and entropy checks, reuse detection, pattern rules
- **Security Audit:** Comprehensive password security audit
- **Breach Checking:** Check passwords against Have I Been Pwned database (k-anonymity)
- **QR Codes:** Generate QR codes for passwords and Wi-Fi credentials
- **Configuration:** JSON/YAML config support with customizable options

---

## Configuration

Create a `config.json` or `config.yaml` file in your working directory or user config path.

### Configurable Options

- Length and entropy limits
- History size
- Password expiration days

See `pwd_generator/config.py` for the full list of options and discovery paths.

---

## Security Notes

| Topic | Description |
|-------|-------------|
| **Master Password** | If lost, encrypted history cannot be recovered. Always back up `password_history.enc`. |
| **Breach Checks** | Uses k-anonymity - only hash prefix is sent to Have I Been Pwned. |
| **File Permissions** | History files aim for restrictive permissions. Keep backups and OS access control in mind. |

---

## Development

### Run Tests

```bash
pytest -q
```

### Lint Code

```bash
ruff check pwd_generator cipher.py gui.py simple_cipher.py
```

---

## License

MIT License - See `pyproject.toml` for details.
