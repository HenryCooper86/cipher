#!/usr/bin/env python3
import secrets
import string
import argparse
import math
import sys

# --- Configuration & Constants ---

WORDLIST = [
    "able", "acid", "aged", "also", "area", "army", "away", "baby", "back", "ball",
    "band", "bank", "base", "bath", "bear", "beat", "been", "beer", "bell", "belt",
    "best", "bill", "bird", "blow", "blue", "boat", "body", "bomb", "bond", "bone",
    "book", "boom", "born", "boss", "both", "bowl", "bulk", "burn", "bush", "busy",
    "call", "calm", "came", "camp", "card", "care", "case", "cash", "cast", "cell",
    "chat", "chip", "city", "club", "coal", "coat", "code", "cold", "come", "cook",
    "cool", "cope", "copy", "core", "cost", "crew", "crop", "dark", "data", "date",
    "dawn", "days", "dead", "deal", "dean", "dear", "debt", "deep", "deny", "desk",
    "dial", "diet", "disc", "disk", "does", "done", "door", "dose", "down", "draw",
    "drew", "drop", "drug", "dual", "duke", "dust", "duty", "each", "earn", "ease",
    "east", "easy", "edge", "else", "even", "ever", "evil", "exit", "face", "fact",
    "fail", "fair", "fall", "farm", "fast", "fate", "fear", "feed", "feel", "feet",
    "fell", "felt", "file", "fill", "film", "find", "fine", "fire", "firm", "fish",
    "five", "flat", "flow", "folk", "food", "foot", "ford", "form", "fort", "four",
    "free", "from", "fuel", "full", "fund", "gain", "game", "gate", "gave", "gear",
    "gene", "gift", "girl", "give", "glad", "goal", "goes", "gold", "golf", "gone",
    "good", "gray", "grew", "grey", "grow", "gulf", "hair", "half", "hall", "hand",
    "hang", "hard", "harm", "hate", "have", "head", "hear", "heat", "held", "hell",
    "help", "here", "hero", "high", "hill", "hire", "hold", "hole", "holy", "home",
    "hope", "host", "hour", "huge", "hung", "hunt", "hurt", "idea", "inch", "into",
]

# --- Core Functions ---

def calculate_entropy(password):
    """Calculate the entropy of a password in bits."""
    pool_size = 0
    if any(c.islower() for c in password): pool_size += 26
    if any(c.isupper() for c in password): pool_size += 26
    if any(c.isdigit() for c in password): pool_size += 10
    if any(c in string.punctuation for c in password): pool_size += 32
    
    if pool_size == 0: return 0
    return math.log2(pool_size) * len(password)

def generate_password(length=16, use_upper=True, use_lower=True, use_digits=True, use_special=True):
    """Generate a secure random password."""
    if length < 8:
        print("Warning: Password length < 8 is not secure.")
    
    chars = ''
    if use_upper: chars += string.ascii_uppercase
    if use_lower: chars += string.ascii_lowercase
    if use_digits: chars += string.digits
    if use_special: chars += string.punctuation

    if not chars:
        return "Error: No character types selected."

    # Ensure at least one of each selected type
    password = []
    if use_upper: password.append(secrets.choice(string.ascii_uppercase))
    if use_lower: password.append(secrets.choice(string.ascii_lowercase))
    if use_digits: password.append(secrets.choice(string.digits))
    if use_special: password.append(secrets.choice(string.punctuation))

    # Fill the rest
    remaining = length - len(password)
    for _ in range(remaining):
        password.append(secrets.choice(chars))
    
    # Shuffle to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

def generate_passphrase(words=4, separator='-'):
    """Generate a passphrase using random words."""
    passphrase_words = []
    for _ in range(words):
        word = secrets.choice(WORDLIST)
        # Randomly capitalize words for extra entropy
        if secrets.choice([True, False]):
            word = word.capitalize()
        passphrase_words.append(word)
    
    # Add a number and special char for better complexity
    return separator.join(passphrase_words) + str(secrets.randbelow(100)) + secrets.choice('!@#$%^&*')

def generate_pin(length=6):
    """Generate a secure random PIN."""
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))

# --- CLI & Interactive Mode ---

def interactive_mode():
    print("\n--- Simple Secure Password Generator ---")
    print("1. Generate Random Password")
    print("2. Generate Passphrase (e.g. Correct-Horse-Battery-Staple)")
    print("3. Generate PIN")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        try:
            length = int(input("Length (default 16): ") or 16)
            pwd = generate_password(length)
            print(f"\nPassword: {pwd}")
            print(f"Entropy:  {calculate_entropy(pwd):.1f} bits")
        except ValueError:
            print("Invalid length.")
            
    elif choice == '2':
        try:
            words = int(input("Number of words (default 4): ") or 4)
            pwd = generate_passphrase(words)
            print(f"\nPassphrase: {pwd}")
            print(f"Entropy:    {calculate_entropy(pwd):.1f} bits")
        except ValueError:
            print("Invalid number.")

    elif choice == '3':
        try:
            length = int(input("Length (default 6): ") or 6)
            pin = generate_pin(length)
            print(f"\nPIN: {pin}")
        except ValueError:
            print("Invalid length.")
            
    elif choice == '4':
        sys.exit(0)
    else:
        print("Invalid choice.")

def main():
    parser = argparse.ArgumentParser(description="Simple Secure Password Generator")
    subparsers = parser.add_subparsers(dest="command")

    # Generate Password
    pwd_parser = subparsers.add_parser("password", help="Generate a standard password")
    pwd_parser.add_argument("-l", "--length", type=int, default=16, help="Password length")
    pwd_parser.add_argument("--no-special", action="store_true", help="Exclude special characters")

    # Generate Passphrase
    phrase_parser = subparsers.add_parser("passphrase", help="Generate a diceware-style passphrase")
    phrase_parser.add_argument("-w", "--words", type=int, default=4, help="Number of words")

    # Generate PIN
    pin_parser = subparsers.add_parser("pin", help="Generate a numeric PIN")
    pin_parser.add_argument("-l", "--length", type=int, default=6, help="PIN length")

    args = parser.parse_args()

    if args.command == "password":
        pwd = generate_password(length=args.length, use_special=not args.no_special)
        print(pwd)
    elif args.command == "passphrase":
        pwd = generate_passphrase(words=args.words)
        print(pwd)
    elif args.command == "pin":
        pwd = generate_pin(length=args.length)
        print(pwd)
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
