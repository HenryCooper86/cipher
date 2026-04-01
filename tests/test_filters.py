import pytest
from pwd_generator.filters import (
    filter_history_by_entropy,
    filter_history_by_service,
    filter_history_by_strength,
    sort_history,
)


@pytest.fixture
def filter_history():
    return [
        {
            "password": "Pass1",
            "metadata": {
                "service": "gmail",
                "created_at": "2024-01-01T00:00:00",
                "strength": "Strong",
                "entropy": 80.0,
            },
        },
        {
            "password": "Pass2",
            "metadata": {
                "service": "github",
                "created_at": "2024-01-02T00:00:00",
                "strength": "Weak",
                "entropy": 40.0,
            },
        },
        {
            "password": "Pass3",
            "metadata": {
                "service": "gmail",
                "created_at": "2024-01-03T00:00:00",
                "strength": "Good",
                "entropy": 65.0,
            },
        },
    ]


def test_filter_by_service(filter_history):
    filtered = filter_history_by_service(filter_history, "gmail")
    assert len(filtered) == 2
    for entry in filtered:
        assert "gmail" in entry["metadata"]["service"].lower()


def test_filter_by_service_no_match(filter_history):
    filtered = filter_history_by_service(filter_history, "nonexistent")
    assert len(filtered) == 0


def test_filter_by_strength(filter_history):
    filtered = filter_history_by_strength(filter_history, "Good")
    assert len(filtered) == 2


def test_filter_by_strength_weak(filter_history):
    filtered = filter_history_by_strength(filter_history, "Weak")
    assert len(filtered) == 3


def test_filter_by_entropy(filter_history):
    filtered = filter_history_by_entropy(filter_history, 60.0)
    assert len(filtered) == 2


def test_sort_by_date(filter_history):
    sorted_history = sort_history(filter_history, "date", False)
    dates = [e["metadata"]["created_at"] for e in sorted_history]
    assert dates == sorted(dates)


def test_sort_by_date_reverse(filter_history):
    sorted_history = sort_history(filter_history, "date", True)
    dates = [e["metadata"]["created_at"] for e in sorted_history]
    assert dates == sorted(dates, reverse=True)


def test_sort_by_service(filter_history):
    sorted_history = sort_history(filter_history, "service", False)
    services = [e["metadata"]["service"] for e in sorted_history]
    assert services == sorted(services)


def test_sort_by_strength(filter_history):
    sorted_history = sort_history(filter_history, "strength", False)
    strengths = [e["metadata"]["strength"] for e in sorted_history]
    strength_order = ["Weak", "Fair", "Good", "Strong", "Very Strong"]
    sorted_strengths = sorted(
        strengths, key=lambda x: strength_order.index(x) if x in strength_order else 999
    )
    assert strengths == sorted_strengths


def test_sort_by_entropy(filter_history):
    sorted_history = sort_history(filter_history, "entropy", False)
    entropies = [e["metadata"]["entropy"] for e in sorted_history]
    assert entropies == sorted(entropies)
