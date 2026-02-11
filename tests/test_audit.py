import pytest
from datetime import datetime, timedelta
from pwd_generator.audit import PasswordAuditor
from pwd_generator.generator import SecurePasswordGenerator


@pytest.fixture
def auditor_with_history(gen):
    gen.history = [
        {
            "password": "Password123!",
            "metadata": {
                "service": "test1",
                "created_at": datetime.now().isoformat(),
                "entropy": 50.0,
                "strength": "Fair",
            },
        },
        {
            "password": "Password123!",
            "metadata": {
                "service": "test2",
                "created_at": datetime.now().isoformat(),
                "entropy": 50.0,
                "strength": "Fair",
            },
        },
        {
            "password": "StrongP@ssw0rd!2024",
            "metadata": {
                "service": "test3",
                "created_at": (datetime.now() - timedelta(days=100)).isoformat(),
                "entropy": 80.0,
                "strength": "Strong",
            },
        },
        {
            "password": "weak",
            "metadata": {
                "service": "test4",
                "created_at": datetime.now().isoformat(),
                "entropy": 20.0,
                "strength": "Weak",
            },
        },
        {
            "password": "VeryStrongP@ssw0rd!2024#Secure",
            "metadata": {
                "service": "test5",
                "created_at": datetime.now().isoformat(),
                "entropy": 95.0,
                "strength": "Very Strong",
            },
        },
        {
            "password": "Password123!",
            "metadata": {
                "service": "test6",
                "created_at": datetime.now().isoformat(),
                "entropy": 50.0,
                "strength": "Fair",
            },
        },
        {
            "password": "OldPassword123!",
            "metadata": {
                "service": "test7",
                "created_at": (datetime.now() - timedelta(days=200)).isoformat(),
                "entropy": 65.0,
                "strength": "Good",
            },
        },
    ]
    return PasswordAuditor(gen)


def test_find_duplicates(auditor_with_history):
    duplicates = auditor_with_history.find_duplicates()
    assert len(duplicates) >= 1

    password123_dup = next((d for d in duplicates if d[0] == "Password123!"), None)
    assert password123_dup is not None
    assert len(password123_dup[1]) == 3


def test_find_weak_passwords(auditor_with_history):
    weak = auditor_with_history.find_weak_passwords(min_entropy=60.0)
    assert len(weak) >= 2


def test_find_expired_passwords(auditor_with_history):
    expired = auditor_with_history.find_expired_passwords()
    assert len(expired) >= 1


def test_calculate_security_score(auditor_with_history):
    score = auditor_with_history.calculate_security_score()
    assert "score" in score
    assert "details" in score
    assert 0 <= score["score"] <= 100
    assert "total_passwords" in score["details"]
    assert "weak_passwords" in score["details"]
    assert "duplicate_passwords" in score["details"]


def test_generate_audit_report(auditor_with_history):
    report = auditor_with_history.generate_audit_report()
    keys = [
        "generated_at",
        "security_score",
        "summary",
        "duplicates",
        "weak_passwords",
        "expired_passwords",
        "strength_distribution",
    ]
    for key in keys:
        assert key in report


def test_empty_history():
    empty_gen = SecurePasswordGenerator()
    empty_auditor = PasswordAuditor(empty_gen)
    score = empty_auditor.calculate_security_score()
    assert score["score"] == 0
    assert score["percentage"] == 0
    assert score["details"] == {}


def test_find_weak_passwords_custom_threshold(auditor_with_history):
    weak_50 = auditor_with_history.find_weak_passwords(min_entropy=50.0)
    weak_60 = auditor_with_history.find_weak_passwords(min_entropy=60.0)
    assert len(weak_50) <= len(weak_60)


def test_calculate_security_score_components(auditor_with_history):
    score = auditor_with_history.calculate_security_score()
    assert score["max_score"] == 100
    assert score["percentage"] == score["score"]


def test_generate_audit_report_summary(auditor_with_history):
    report = auditor_with_history.generate_audit_report()
    summary = report["summary"]
    assert summary["total_passwords"] == len(auditor_with_history.gen.history)


def test_security_score_with_all_strong_passwords():
    strong_gen = SecurePasswordGenerator()
    strong_gen.history = [
        {
            "password": "VeryStrongP@ssw0rd!2024",
            "metadata": {
                "service": "test1",
                "created_at": datetime.now().isoformat(),
                "entropy": 90.0,
                "strength": "Very Strong",
            },
        },
        {
            "password": "AnotherStrongP@ss!2024",
            "metadata": {
                "service": "test2",
                "created_at": datetime.now().isoformat(),
                "entropy": 85.0,
                "strength": "Strong",
            },
        },
    ]
    strong_auditor = PasswordAuditor(strong_gen)
    score = strong_auditor.calculate_security_score()
    assert score["score"] > 70


def test_security_score_with_all_weak_passwords():
    weak_gen = SecurePasswordGenerator()
    weak_gen.history = [
        {
            "password": "weak1",
            "metadata": {
                "service": "test1",
                "created_at": datetime.now().isoformat(),
                "entropy": 20.0,
                "strength": "Weak",
            },
        },
        {
            "password": "weak2",
            "metadata": {
                "service": "test2",
                "created_at": datetime.now().isoformat(),
                "entropy": 25.0,
                "strength": "Weak",
            },
        },
    ]
    weak_auditor = PasswordAuditor(weak_gen)
    score = weak_auditor.calculate_security_score()
    assert score["score"] < 100


def test_security_score_with_duplicates_penalty():
    dup_gen = SecurePasswordGenerator()
    dup_gen.history = [
        {
            "password": "Same123!",
            "metadata": {
                "service": "t1",
                "created_at": datetime.now().isoformat(),
                "entropy": 60.0,
                "strength": "Good",
            },
        },
        {
            "password": "Same123!",
            "metadata": {
                "service": "t2",
                "created_at": datetime.now().isoformat(),
                "entropy": 60.0,
                "strength": "Good",
            },
        },
    ]
    dup_auditor = PasswordAuditor(dup_gen)
    score = dup_auditor.calculate_security_score()
    assert score["score"] < 100


def test_security_score_with_expired_penalty():
    expired_gen = SecurePasswordGenerator()
    expired_gen.history = [
        {
            "password": "Old123!",
            "metadata": {
                "service": "t1",
                "created_at": (datetime.now() - timedelta(days=200)).isoformat(),
                "entropy": 70.0,
                "strength": "Strong",
            },
        }
    ]
    expired_auditor = PasswordAuditor(expired_gen)
    score = expired_auditor.calculate_security_score()
    assert score["score"] < 100
