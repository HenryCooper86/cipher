from datetime import datetime, timedelta


def test_generate_random_string_default(gen):
    password = gen.generate_random_string()
    assert isinstance(password, str)
    assert len(password) >= 12


def test_generate_random_string_custom_length(gen):
    password = gen.generate_random_string(20)
    assert len(password) == 20


def test_generate_random_string_validation(gen):
    password = gen.generate_random_string(16)
    is_valid, _ = gen.validate(password)
    assert is_valid


def test_generate_passphrase(gen):
    passphrase = gen.generate_passphrase(5)
    assert isinstance(passphrase, str)
    assert "-" in passphrase


def test_generate_passphrase_min_words(gen):
    passphrase = gen.generate_passphrase(2)
    parts = passphrase.split("-")
    word_parts = [p for p in parts if any(c.isalpha() for c in p)]
    assert len(word_parts) >= 4


def test_generate_pin(gen):
    pin = gen.generate_pin(6)
    assert len(pin) == 6
    assert pin.isdigit()


def test_generate_pin_no_repeats(gen):
    pin = gen.generate_pin(6)
    unique_digits = len(set(pin))
    assert unique_digits >= 3


def test_batch_generate(gen):
    passwords = gen.batch_generate(5, 16, "random")
    assert len(passwords) == 5
    for pwd in passwords:
        assert isinstance(pwd, str)


def test_clear_sensitive_data(gen):
    pwd1 = gen.generate_random_string(16)
    pwd2 = gen.generate_random_string(16)

    assert len(gen.session_generated) > 0
    assert pwd1 in gen.session_generated

    gen.clear_sensitive_data()

    assert len(gen.session_generated) == 0
    assert pwd1 not in gen.session_generated
    assert pwd2 not in gen.session_generated


def test_calculate_entropy(gen):
    entropy = gen.calculate_entropy("Test123!")
    assert entropy > 0


def test_calculate_strength_score(gen):
    score = gen.calculate_strength_score("Test123!")
    assert score in ["Weak", "Fair", "Good", "Strong", "Very Strong"]


def test_get_password_stats_basic(gen):
    password = gen.generate_random_string(16)
    stats = gen.get_password_stats(password)
    assert "length" in stats
    assert "entropy" in stats
    assert "strength" in stats
    assert "is_valid" in stats
    assert stats["length"] == 16


def test_validate_password_too_short(gen):
    is_valid, reason = gen.validate("Short1!")
    assert not is_valid
    assert "short" in reason.lower()


def test_validate_password_missing_uppercase(gen):
    password = "simpleword468!$%"
    is_valid, reason = gen.validate(password, strict=True)
    assert not is_valid
    assert "uppercase" in reason.lower()


def test_validate_password_consecutive_pattern(gen):
    is_valid, reason = gen.validate("abc123DEF!@#", strict=False)
    if not is_valid:
        assert "consecutive" in (reason.lower() or "")


def test_get_password_stats_full(gen):
    password = "TestPassword123!"
    stats = gen.get_password_stats(password)

    keys = [
        "length",
        "entropy",
        "strength",
        "has_uppercase",
        "has_lowercase",
        "has_digits",
        "has_special",
        "unique_chars",
        "is_valid",
        "validation_message",
    ]
    for key in keys:
        assert key in stats

    assert stats["length"] == len(password)
    assert stats["entropy"] > 0
    assert isinstance(stats["strength"], str)


def test_get_expired_passwords_empty(gen):
    expired = gen.get_expired_passwords()
    assert len(expired) == 0


def test_get_expired_passwords_with_history(gen_with_history):
    # Add old password (100 days ago)
    old_date = (datetime.now() - timedelta(days=100)).isoformat()
    gen_with_history.history = [
        {
            "password": "OldPassword123!",
            "metadata": {
                "service": "test",
                "created_at": old_date,
                "entropy": 60.0,
                "strength": "Good",
            },
        }
    ]

    expired = gen_with_history.get_expired_passwords()
    assert len(expired) == 1
    assert expired[0][1]["metadata"]["service"] == "test"


def test_add_to_history(gen_with_history):
    password = gen_with_history.generate_random_string(16)
    gen_with_history.add_to_history(password, "test_service", "test notes")
    assert len(gen_with_history.history) == 1
    assert gen_with_history.history[0]["metadata"]["service"] == "test_service"


def test_delete_from_history(gen_with_history):
    password = gen_with_history.generate_random_string(16)
    gen_with_history.add_to_history(password, "test_service")
    assert gen_with_history.delete_from_history(0)
    assert len(gen_with_history.history) == 0


def test_update_history_entry(gen_with_history):
    password = gen_with_history.generate_random_string(16)
    gen_with_history.add_to_history(password, "old_service")
    assert gen_with_history.update_history_entry(0, service="new_service")
    assert gen_with_history.history[0]["metadata"]["service"] == "new_service"
