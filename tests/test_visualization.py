import pytest
from pwd_generator.visualization import (
    get_strength_color,
    get_strength_emoji,
    display_strength_meter,
    display_character_breakdown,
    format_character_breakdown,
)


@pytest.mark.parametrize("strength", ["Weak", "Fair", "Good", "Strong", "Very Strong"])
def test_get_strength_color(strength):
    result = get_strength_color(strength)
    assert strength in result


@pytest.mark.parametrize(
    "strength, expected",
    [
        ("Weak", "[WEAK]"),
        ("Fair", "[FAIR]"),
        ("Good", "[GOOD]"),
        ("Strong", "[STRONG]"),
        ("Very Strong", "[VERY STRONG]"),
    ],
)
def test_get_strength_emoji(strength, expected):
    assert get_strength_emoji(strength) == expected


def test_display_strength_meter():
    result = display_strength_meter("Password123!", 60.0, "Good")
    assert "Good" in result
    assert "60.0" in result
    assert "█" in result


def test_display_character_breakdown():
    breakdown = display_character_breakdown("Password123!")
    keys = ["uppercase", "lowercase", "digits", "special", "total", "unique"]
    for key in keys:
        assert key in breakdown
    assert breakdown["total"] > 0


def test_format_character_breakdown():
    breakdown = {
        "uppercase": 1,
        "lowercase": 7,
        "digits": 3,
        "special": 1,
        "total": 12,
        "unique": 10,
        "percent_unique": 83.3,
    }
    formatted = format_character_breakdown(breakdown)
    keys = ["Uppercase", "Lowercase", "Digits", "Special", "Unique"]
    for key in keys:
        assert key in formatted
