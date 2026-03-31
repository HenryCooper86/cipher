# Horizon Cypher

Secure password generator with **encrypted saved passwords**, CLI, optional **desktop GUI**, breach checks (Have I Been Pwned), QR codes, and audits.

## Quick start

| What | Command |
|------|---------|
| **GUI** (after `pip install -e ".[gui]"`) | `horizon-cipher-gui` or `python gui.py` |
| **CLI** (full app) | `horizon-cipher` or `python cipher.py` |
| **Minimal demo** (stdlib only, no `pip install`) | `python simple_cipher.py` |

First full-app run asks for a **master password** (12+ characters) to encrypt your history file.

## Install

- **Python 3.9+**
- From the repo root:

```bash
pip install -e .
```

- **GUI:** `pip install -e ".[gui]"` (PyQt6)
- **Argon2 KDF** (optional; else PBKDF2): `pip install -e ".[argon2]"`

Dependencies are listed in `pyproject.toml` / `requirements.txt`.

## Common CLI examples

```bash
horizon-cipher generate --length 20
horizon-cipher generate --type passphrase --words 5
horizon-cipher generate --type pin --length 6
horizon-cipher analyze "your-password-here"
horizon-cipher breach "your-password-here"
horizon-cipher history list
horizon-cipher history search gmail
```

Use `python cipher.py …` instead of `horizon-cipher` if you did not install the package.

Interactive menu: run `horizon-cipher` or `python cipher.py` with no arguments.

## What you get

- Random passwords, passphrases, PINs; patterns, templates, profiles  
- Encrypted history (PBKDF2 or Argon2 + Fernet), search/filter/sort, import/export (JSON, CSV, and common manager formats)  
- Strength and entropy checks, reuse and pattern rules, security audit  
- QR codes for passwords / Wi‑Fi (optional `qrcode` + Pillow; often already installed with the package)  
- JSON/YAML config under the paths used by `pwd_generator.config`

## Configuration

Optional `config.json` / `config.yaml` beside your working directory or user config paths—see `pwd_generator/config.py` for discovery. Typical knobs: length/entropy limits, history size, expiration days.

## Security (short)

- **Lost master password** → encrypted history cannot be recovered. Back up `password_history.enc` safely.  
- Breach checks use **k-anonymity** (hash prefix only to HIBP).  
- History files aim for restrictive permissions; keep backups and OS access control in mind.

## Development

```bash
pip install -e ".[dev]"
pytest -q
ruff check pwd_generator cipher.py gui.py simple_cipher.py
```

## License

MIT — see `pyproject.toml`.
