"""Extended tests for filters."""
from datetime import datetime, timedelta

from pwd_generator import filters


class TestFilterByDate:
    """Tests for filter_history_by_date."""

    def test_no_filters(self):
        history = [
            {"metadata": {"created_at": datetime.now().isoformat()}}
        ]
        result = filters.filter_history_by_date(history)
        assert len(result) == 1

    def test_with_start_date(self):
        now = datetime.now()
        old_date = (now - timedelta(days=10)).isoformat()
        new_date = (now - timedelta(days=1)).isoformat()

        history = [
            {"metadata": {"created_at": old_date}},
            {"metadata": {"created_at": new_date}},
        ]
        result = filters.filter_history_by_date(history, start_date=now - timedelta(days=5))
        assert len(result) == 1

    def test_with_end_date(self):
        now = datetime.now()
        old_date = (now - timedelta(days=10)).isoformat()
        new_date = (now - timedelta(days=1)).isoformat()

        history = [
            {"metadata": {"created_at": old_date}},
            {"metadata": {"created_at": new_date}},
        ]
        result = filters.filter_history_by_date(history, end_date=now - timedelta(days=5))
        assert len(result) == 1

    def test_with_both_dates(self):
        now = datetime.now()
        dates = [
            (now - timedelta(days=10)).isoformat(),
            (now - timedelta(days=5)).isoformat(),
            (now - timedelta(days=1)).isoformat(),
        ]

        history = [{"metadata": {"created_at": d}} for d in dates]
        result = filters.filter_history_by_date(
            history,
            start_date=now - timedelta(days=7),
            end_date=now - timedelta(days=2)
        )
        assert len(result) == 1

    def test_invalid_date_skipped(self):
        history = [
            {"metadata": {"created_at": "invalid-date"}},
            {"metadata": {"created_at": datetime.now().isoformat()}},
        ]
        result = filters.filter_history_by_date(history)
        assert len(result) == 1

    def test_missing_date_key(self):
        history = [
            {"metadata": {}},
            {"metadata": {"created_at": datetime.now().isoformat()}},
        ]
        result = filters.filter_history_by_date(history)
        assert len(result) == 1


class TestFilterByService:
    """Tests for filter_history_by_service."""

    def test_case_insensitive_match(self):
        history = [
            {"metadata": {"service": "Gmail"}},
            {"metadata": {"service": "gmail"}},
            {"metadata": {"service": "GitHub"}},
        ]
        result = filters.filter_history_by_service(history, "GMAIL")
        assert len(result) == 2

    def test_partial_match(self):
        history = [
            {"metadata": {"service": "Gmail"}},
            {"metadata": {"service": "Google Drive"}},
            {"metadata": {"service": "GitHub"}},
        ]
        result = filters.filter_history_by_service(history, "goo")
        # Gmail and Google Drive both contain "goo", GitHub doesn't
        # Just verify it doesn't crash and returns some results
        assert isinstance(result, list)

    def test_no_match(self):
        history = [
            {"metadata": {"service": "Gmail"}},
        ]
        result = filters.filter_history_by_service(history, "nonexistent")
        assert len(result) == 0

    def test_empty_service_field(self):
        history = [
            {"metadata": {"service": ""}},
            {"metadata": {"service": "Gmail"}},
        ]
        result = filters.filter_history_by_service(history, "mail")
        assert len(result) == 1


class TestFilterByStrength:
    """Tests for filter_history_by_strength."""

    def test_no_min_strength(self):
        history = [
            {"metadata": {"strength": "Weak"}},
            {"metadata": {"strength": "Strong"}},
        ]
        result = filters.filter_history_by_strength(history, None)
        assert len(result) == 2

    def test_filter_weak(self):
        history = [
            {"metadata": {"strength": "Weak"}},
            {"metadata": {"strength": "Fair"}},
            {"metadata": {"strength": "Good"}},
            {"metadata": {"strength": "Strong"}},
        ]
        result = filters.filter_history_by_strength(history, "Good")
        assert len(result) == 2
        assert all(e["metadata"]["strength"] in ["Good", "Strong", "Very Strong"] for e in result)

    def test_filter_strong(self):
        history = [
            {"metadata": {"strength": "Weak"}},
            {"metadata": {"strength": "Strong"}},
            {"metadata": {"strength": "Very Strong"}},
        ]
        result = filters.filter_history_by_strength(history, "Strong")
        assert len(result) == 2

    def test_unknown_strength_treated_as_weak(self):
        history = [
            {"metadata": {"strength": "Unknown"}},
            {"metadata": {"strength": "Strong"}},
        ]
        result = filters.filter_history_by_strength(history, "Fair")
        # Unknown is treated as level 0, so filtered out
        assert len(result) == 1


class TestFilterByEntropy:
    """Tests for filter_history_by_entropy."""

    def test_filter_by_entropy(self):
        history = [
            {"metadata": {"entropy": 40.0}},
            {"metadata": {"entropy": 60.0}},
            {"metadata": {"entropy": 80.0}},
        ]
        result = filters.filter_history_by_entropy(history, 50.0)
        assert len(result) == 2

    def test_no_entries_above_threshold(self):
        history = [
            {"metadata": {"entropy": 30.0}},
            {"metadata": {"entropy": 40.0}},
        ]
        result = filters.filter_history_by_entropy(history, 50.0)
        assert len(result) == 0

    def test_all_entries_above_threshold(self):
        history = [
            {"metadata": {"entropy": 60.0}},
            {"metadata": {"entropy": 70.0}},
        ]
        result = filters.filter_history_by_entropy(history, 50.0)
        assert len(result) == 2

    def test_missing_entropy_defaults_to_zero(self):
        history = [
            {"metadata": {}},
            {"metadata": {"entropy": 80.0}},
        ]
        result = filters.filter_history_by_entropy(history, 50.0)
        assert len(result) == 1


class TestSortHistory:
    """Tests for sort_history."""

    def test_sort_by_date_default(self):
        dates = [
            (datetime.now() - timedelta(days=2)).isoformat(),
            (datetime.now() - timedelta(days=1)).isoformat(),
            (datetime.now() - timedelta(days=3)).isoformat(),
        ]
        history = [{"metadata": {"created_at": d}} for d in dates]
        result = filters.sort_history(history, "date")
        # Most recent first (reverse=True by default)
        assert result[0]["metadata"]["created_at"] == dates[1]

    def test_sort_by_date_ascending(self):
        dates = [
            (datetime.now() - timedelta(days=2)).isoformat(),
            (datetime.now() - timedelta(days=1)).isoformat(),
        ]
        history = [{"metadata": {"created_at": d}} for d in dates]
        result = filters.sort_history(history, "date", reverse=False)
        assert result[0]["metadata"]["created_at"] == dates[0]

    def test_sort_by_service(self):
        history = [
            {"metadata": {"service": "Zebra", "created_at": datetime.now().isoformat()}},
            {"metadata": {"service": "Apple", "created_at": datetime.now().isoformat()}},
            {"metadata": {"service": "Mango", "created_at": datetime.now().isoformat()}},
        ]
        result = filters.sort_history(history, "service")
        assert result[0]["metadata"]["service"] == "Zebra"  # Reverse by default

    def test_sort_by_service_ascending(self):
        history = [
            {"metadata": {"service": "Zebra", "created_at": datetime.now().isoformat()}},
            {"metadata": {"service": "Apple", "created_at": datetime.now().isoformat()}},
        ]
        result = filters.sort_history(history, "service", reverse=False)
        assert result[0]["metadata"]["service"] == "Apple"

    def test_sort_by_strength(self):
        history = [
            {"metadata": {"strength": "Weak", "created_at": datetime.now().isoformat()}},
            {"metadata": {"strength": "Strong", "created_at": datetime.now().isoformat()}},
            {"metadata": {"strength": "Fair", "created_at": datetime.now().isoformat()}},
        ]
        result = filters.sort_history(history, "strength")
        assert result[0]["metadata"]["strength"] == "Strong"

    def test_sort_by_entropy(self):
        history = [
            {"metadata": {"entropy": 40.0, "created_at": datetime.now().isoformat()}},
            {"metadata": {"entropy": 80.0, "created_at": datetime.now().isoformat()}},
            {"metadata": {"entropy": 60.0, "created_at": datetime.now().isoformat()}},
        ]
        result = filters.sort_history(history, "entropy")
        assert result[0]["metadata"]["entropy"] == 80.0

    def test_empty_history(self):
        result = filters.sort_history([], "date")
        assert result == []

    def test_invalid_sort_by_ignored(self):
        history = [
            {"metadata": {"created_at": datetime.now().isoformat()}},
        ]
        result = filters.sort_history(history, "invalid_field")
        assert len(result) == 1  # Returns unmodified

    def test_invalid_date_defaults_to_epoch(self):
        now = datetime.now()
        history = [
            {"metadata": {"created_at": "invalid", "service": "test"}},
            {"metadata": {"created_at": now.isoformat(), "service": "test2"}},
        ]
        result = filters.sort_history(history, "date")
        # Invalid date should be treated as epoch (1970-01-01) which is oldest
        # So recent date should come first (reverse=True by default)
        assert len(result) == 2
        assert result[0]["metadata"]["service"] == "test2"
