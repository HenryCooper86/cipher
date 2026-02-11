import pytest
import os
import shutil
from pathlib import Path
from pwd_generator.validators import (
    validate_positive_int,
    validate_length,
    validate_string,
    validate_file_path,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("5", 5),
        ("1", 1),
        ("100", 100),
    ],
)
def test_valid_positive_int(value, expected):
    assert validate_positive_int(value) == expected


@pytest.mark.parametrize(
    "value, msg",
    [
        ("0", "must be a positive number"),
        ("-5", "must be a positive number"),
        ("101", "must be <= 100"),
        ("abc", "must be a valid number"),
    ],
)
def test_invalid_positive_int(value, msg):
    with pytest.raises(ValueError, match=msg):
        if value == "101":
            validate_positive_int(value, max_value=100)
        else:
            validate_positive_int(value)


def test_validate_positive_int_empty():
    with pytest.raises(ValueError):
        validate_positive_int("")


def test_validate_positive_int_custom_field():
    with pytest.raises(ValueError, match="Count"):
        validate_positive_int("0", field_name="Count")


@pytest.mark.parametrize(
    "value, min_val, max_val, expected",
    [
        (10, 5, 20, 10),
        (5, 5, 20, 5),
        (20, 5, 20, 20),
    ],
)
def test_valid_length(value, min_val, max_val, expected):
    assert validate_length(value, min_val, max_val) == expected


@pytest.mark.parametrize(
    "value, min_val, max_val, msg",
    [
        (4, 5, 20, "must be at least 5"),
        (21, 5, 20, "must be at most 20"),
    ],
)
def test_invalid_length(value, min_val, max_val, msg):
    with pytest.raises(ValueError, match=msg):
        validate_length(value, min_val, max_val)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("hello", "hello"),
        ("  hello  ", "hello"),
        ("Hello World", "Hello World"),
        ("hello\x00\x01\x02world", "helloworld"),
    ],
)
def test_valid_string(value, expected):
    assert validate_string(value) == expected


def test_validate_string_empty_not_allowed():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_string("")


def test_validate_string_empty_allowed():
    assert validate_string("", allow_empty=True) == ""
    assert validate_string("   ", allow_empty=True) == ""


def test_validate_string_max_length():
    long_string = "a" * 1000
    assert validate_string(long_string, max_length=1000) == long_string
    with pytest.raises(ValueError, match="must be <= 1000 characters"):
        validate_string("a" * 1001, max_length=1000)


def test_validate_string_non_string():
    with pytest.raises(ValueError, match="must be a string"):
        validate_string(123)


def test_validate_file_path(temp_dir):
    test_file = temp_dir / "test_file.txt"
    test_file.write_text("test content")

    result = validate_file_path("test_file.txt", base_dir=temp_dir)
    assert result == test_file.resolve()


@pytest.mark.parametrize(
    "path, msg",
    [
        ("../test_file.txt", "outside allowed directory"),
        ("../../etc/passwd", "outside allowed directory"),
        ("test\x00file.txt", "cannot contain null bytes"),
        ("nonexistent.txt", "does not exist"),
        ("/etc/passwd", "outside allowed directory"),
    ],
)
def test_invalid_file_path(temp_dir, path, msg):
    if os.name == "nt" and path == "/etc/passwd":
        pytest.skip("Unix specific path")

    with pytest.raises(ValueError, match=msg):
        if msg == "does not exist":
            validate_file_path(path, base_dir=temp_dir, must_exist=True)
        else:
            validate_file_path(path, base_dir=temp_dir)


def test_validate_file_path_create_new(temp_dir):
    new_file = temp_dir / "new_file.txt"
    result = validate_file_path("new_file.txt", base_dir=temp_dir, must_exist=False)
    assert result == new_file.resolve()


def test_validate_file_path_nested(temp_dir):
    nested_dir = temp_dir / "nested"
    nested_dir.mkdir()
    nested_file = nested_dir / "file.txt"
    nested_file.write_text("content")

    result = validate_file_path("nested/file.txt", base_dir=temp_dir)
    assert result == nested_file.resolve()
