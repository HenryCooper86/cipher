import pytest
from pwd_generator.validation import PasswordValidator


@pytest.fixture
def validator():
    return PasswordValidator(
        username="testuser",
        policy={
            "min_length": 12,
            "max_length": 128,
            "min_entropy": 60,
            "max_history_check": 10,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digits": True,
            "require_special": True,
        },
    )


def test_has_consecutive_pattern_sequential_numbers(validator):
    assert validator.has_consecutive_pattern("abc123DEF!")


def test_has_consecutive_pattern_sequential_letters(validator):
    assert validator.has_consecutive_pattern("TestABC123!")


def test_has_consecutive_pattern_keyboard(validator):
    assert validator.has_consecutive_pattern("TestQWE123!")


def test_has_consecutive_pattern_no_pattern(validator):
    assert not validator.has_consecutive_pattern("ComplexPass135!$%")


def test_has_username_leak_detected(validator):
    assert validator.has_username_leak("TestUser123!")


def test_has_username_leak_not_detected(validator):
    assert not validator.has_username_leak("MySecurePassword123!")


def test_has_repeated_characters(validator):
    assert validator.has_repeated_characters("TestAAA123!")


def test_has_repeated_characters_no_repeats(validator):
    assert not validator.has_repeated_characters("TestXyZ123!")


def test_calculate_entropy(validator):
    assert validator.calculate_entropy("Test123!") > 0


def test_calculate_entropy_empty_string(validator):
    assert validator.calculate_entropy("") == 0.0


def test_calculate_strength_score_weak(validator):
    assert validator.calculate_strength_score("Test") == "Weak"


def test_calculate_strength_score_strong(validator):
    assert validator.calculate_strength_score("VeryStrongPassword123!@#") in [
        "Strong",
        "Very Strong",
    ]


def test_validate_too_short(validator):
    is_valid, reason = validator.validate("Short1!")
    assert not is_valid
    assert "short" in reason.lower()


def test_validate_missing_uppercase(validator):
    is_valid, reason = validator.validate("lowercase123!@#")
    assert not is_valid
    assert "uppercase" in reason.lower()


def test_validate_missing_lowercase(validator):
    is_valid, reason = validator.validate("UPPERCASE123!")
    assert not is_valid
    assert "lowercase" in reason.lower()


def test_validate_missing_digit(validator):
    is_valid, reason = validator.validate("TestPassword!")
    assert not is_valid
    assert "digit" in reason.lower()


def test_validate_missing_special(validator):
    is_valid, reason = validator.validate("TestPassword123")
    assert not is_valid
    assert "special" in reason.lower()


def test_validate_valid_password(validator):
    is_valid, reason = validator.validate("ComplexPass135!$%")
    assert is_valid
    assert reason == "Valid"
