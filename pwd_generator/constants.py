# Key Derivation Parameters (PBKDF2) - Legacy support
KDF_ITERATIONS = 600000
SALT_SIZE = 16

# Key Derivation Parameters (Argon2id) - Recommended
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64MB
ARGON2_PARALLELISM = 4

MIN_MASTER_PASSWORD_LENGTH = 12
MIN_MASTER_PASSWORD_ENTROPY = 50

DEFAULT_POLICY = {
    'min_length': 12,
    'max_length': 128,
    'expiration_days': 90,
    'min_entropy': 60,
    'max_history_check': 10,
    'max_history_size': 1000,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_digits': True,
    'require_special': True,
}

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

KEYBOARD_ROWS = [
    "qwertyuiop", "asdfghjkl", "zxcvbnm", 
    "1234567890", "`-=[]\\;',./",
    "~!@#$%^&*()_+{}|:\"<>?"
]
