import pytest
from pwd_generator.patterns import PatternGenerator, validate_pattern


@pytest.fixture
def pattern_gen():
    return PatternGenerator()


def test_generate_noun(pattern_gen):
    result = pattern_gen.generate_from_pattern("[noun]")
    assert isinstance(result, str)
    assert len(result) > 0
    assert result[0].isupper()


def test_generate_verb(pattern_gen):
    result = pattern_gen.generate_from_pattern("[verb]")
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_digits(pattern_gen):
    result = pattern_gen.generate_from_pattern("[2digits]")
    assert isinstance(result, str)
    assert len(result) == 2
    assert result.isdigit()


def test_generate_letters(pattern_gen):
    result = pattern_gen.generate_from_pattern("[4letters]")
    assert isinstance(result, str)
    assert len(result) == 4
    assert result.isalpha()


def test_generate_special(pattern_gen):
    result = pattern_gen.generate_from_pattern("[1special]")
    assert isinstance(result, str)
    assert len(result) == 1
    assert result in "@#$!?^&*~()[]=-_."


def test_generate_complex_pattern(pattern_gen):
    result = pattern_gen.generate_from_pattern("[noun]-[verb]-[2digits]-[1special]")
    # Split into max 4 parts to handle case where special char is '-'
    parts = result.split("-", 3)
    assert len(parts) == 4
    assert parts[0][0].isupper()
    assert parts[1][0].isupper()
    assert parts[2].isdigit()
    assert len(parts[2]) == 2
    # The special char is the last part; if it's '-', parts[3] will be '' due to split behavior
    # Check the actual last character of the result instead
    assert result[-1] in "@#$!?^&*~()[]=-_."


def test_generate_upper_lower(pattern_gen):
    result = pattern_gen.generate_from_pattern("[upper][lower][number][special]")
    assert len(result) == 4
    assert result[0].isupper()
    assert result[1].islower()
    assert result[2].isdigit()
    assert result[3] in "@#$!?^&*~()[]=-_."


def test_validate_valid_pattern():
    is_valid, message = validate_pattern("[noun]-[verb]-[2digits]")
    assert is_valid
    assert message == "Valid pattern"


def test_validate_empty_pattern():
    is_valid, message = validate_pattern("")
    assert not is_valid
    assert "empty" in message.lower()


def test_validate_unmatched_opening_bracket():
    is_valid, message = validate_pattern("[noun-[verb]")
    assert not is_valid
    assert "opening" in message.lower()


def test_validate_unmatched_closing_bracket():
    is_valid, message = validate_pattern("[noun]-[verb]]")
    assert not is_valid
    assert "closing" in message.lower()


def test_validate_nested_brackets():
    is_valid, message = validate_pattern("[[noun]]")
    assert is_valid
