import pytest
from datetime import datetime, timedelta
from pwd_generator.age_calculator import (
    calculate_password_age,
    check_expiration,
    format_age,
)


def test_calculate_password_age():
    created = datetime.now() - timedelta(days=5, hours=3)
    age_info = calculate_password_age(created.isoformat())

    assert age_info["age_days"] == 5
    assert age_info["age_hours"] > 0
    assert not age_info["is_expired"]


def test_check_expiration_not_expired():
    created = datetime.now() - timedelta(days=30)
    exp_info = check_expiration(created.isoformat(), expiration_days=90)

    assert not exp_info["is_expired"]
    assert exp_info["days_until_expiry"] is not None
    assert exp_info["days_until_expiry"] > 0


def test_check_expiration_expired():
    created = datetime.now() - timedelta(days=100)
    exp_info = check_expiration(created.isoformat(), expiration_days=90)

    assert exp_info["is_expired"]
    assert "days_overdue" in exp_info
    assert exp_info["days_overdue"] > 0


@pytest.mark.parametrize(
    "age_info, expected_part",
    [
        ({"age_days": 5, "age_hours": 0, "age_minutes": 0}, "5"),
        ({"age_days": 5, "age_hours": 0, "age_minutes": 0}, "day"),
        ({"age_days": 0, "age_hours": 3, "age_minutes": 0}, "hour"),
        ({"age_days": 0, "age_hours": 0, "age_minutes": 30}, "minute"),
        ({"age_days": 400, "age_hours": 0, "age_minutes": 0}, "year"),
    ],
)
def test_format_age(age_info, expected_part):
    formatted = format_age(age_info)
    assert expected_part in formatted.lower()


def test_invalid_date_format():
    age_info = calculate_password_age("invalid-date")
    assert age_info["age_days"] == 0
    assert not age_info["is_expired"]
