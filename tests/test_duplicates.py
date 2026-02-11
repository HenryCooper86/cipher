import pytest
from pwd_generator.duplicates import (
    find_duplicate_passwords,
    find_similar_passwords,
    get_password_frequency,
)


@pytest.fixture
def history():
    return [
        {"password": "Password123!"},
        {"password": "Password123!"},
        {"password": "DifferentP@ss1"},
        {"password": "Password123!"},
        {"password": "AnotherPass456"},
    ]


def test_find_duplicate_passwords(history):
    duplicates = find_duplicate_passwords(history)
    assert len(duplicates) == 1
    assert duplicates[0][0] == "Password123!"
    assert len(duplicates[0][1]) == 3


def test_find_duplicate_passwords_no_duplicates():
    unique_history = [
        {"password": "Pass1"},
        {"password": "Pass2"},
        {"password": "Pass3"},
    ]
    duplicates = find_duplicate_passwords(unique_history)
    assert len(duplicates) == 0


def test_find_similar_passwords():
    history = [
        {"password": "Password123"},
        {"password": "Password124"},
        {"password": "DifferentPass"},
    ]
    similar = find_similar_passwords(history, threshold=0.8)
    assert len(similar) > 0


def test_find_similar_passwords_no_similar():
    history = [
        {"password": "Password123"},
        {"password": "CompletelyDifferent"},
    ]
    similar = find_similar_passwords(history, threshold=0.8)
    assert len(similar) == 0


def test_get_password_frequency(history):
    frequency = get_password_frequency(history)
    assert frequency["Password123!"] == 3
    assert frequency["DifferentP@ss1"] == 1
    assert frequency["AnotherPass456"] == 1


def test_empty_history():
    assert len(find_duplicate_passwords([])) == 0
    assert len(get_password_frequency([])) == 0
