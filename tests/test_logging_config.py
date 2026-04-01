import logging

import pytest
from pwd_generator.logging_config import SecurityFilter, setup_logging


@pytest.fixture
def security_filter():
    return SecurityFilter()


@pytest.fixture
def log_record():
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="",
        args=(),
        exc_info=None,
    )


def test_password_redaction(security_filter, log_record):
    log_record.msg = "User entered password: secret123"
    security_filter.filter(log_record)
    assert "***REDACTED***" in log_record.msg
    assert "secret123" not in log_record.msg


def test_master_password_redaction(security_filter, log_record):
    log_record.msg = "Master password=secret123 validated"
    security_filter.filter(log_record)
    assert "***REDACTED***" in log_record.msg
    assert "secret123" not in log_record.msg


def test_token_redaction(security_filter, log_record):
    log_record.msg = "API token: abc123xyz"
    security_filter.filter(log_record)
    assert "***REDACTED***" in log_record.msg


def test_key_value_pair_redaction(security_filter, log_record):
    log_record.msg = "password=secret123"
    security_filter.filter(log_record)
    assert "password=***REDACTED***" in log_record.msg
    assert "secret123" not in log_record.msg


def test_key_value_colon_redaction(security_filter, log_record):
    log_record.msg = "api_key: abc123"
    security_filter.filter(log_record)
    assert "api_key: ***REDACTED***" in log_record.msg


def test_ssid_redaction(security_filter, log_record):
    log_record.msg = "WiFi SSID: MyNetwork"
    security_filter.filter(log_record)
    assert "***REDACTED***" in log_record.msg


def test_wifi_redaction(security_filter, log_record):
    log_record.msg = "wifi_password=secret123 configured"
    security_filter.filter(log_record)
    assert "***REDACTED***" in log_record.msg
    assert "secret123" not in log_record.msg


def test_service_name_not_redacted(security_filter, log_record):
    log_record.msg = "Service name: Gmail"
    security_filter.filter(log_record)
    assert "***REDACTED***" not in log_record.msg


def test_username_not_redacted(security_filter, log_record):
    log_record.msg = "Username: john.doe"
    security_filter.filter(log_record)
    assert "***REDACTED***" not in log_record.msg


def test_email_not_redacted(security_filter, log_record):
    log_record.msg = "Email: user@example.com"
    security_filter.filter(log_record)
    assert "***REDACTED***" not in log_record.msg


def test_passphrase_not_redacted(security_filter, log_record):
    log_record.msg = "Passphrase generated"
    security_filter.filter(log_record)
    assert "***REDACTED***" not in log_record.msg


def test_pin_redaction(security_filter, log_record):
    log_record.msg = "PIN: 123456"
    security_filter.filter(log_record)
    assert "***REDACTED***" in log_record.msg


def test_non_sensitive_message_not_redacted(security_filter, log_record):
    # The filter should not redact generic messages without secret values
    log_record.msg = "Password generation completed successfully"
    security_filter.filter(log_record)
    assert "***REDACTED***" not in log_record.msg


def test_multiple_sensitive_patterns(security_filter, log_record):
    log_record.msg = "password=secret token=abc123"
    security_filter.filter(log_record)
    assert "***REDACTED***" in log_record.msg
    assert "secret" not in log_record.msg
    assert "abc123" not in log_record.msg


def test_empty_message(security_filter, log_record):
    log_record.msg = ""
    assert security_filter.filter(log_record)


def test_non_string_message(security_filter, log_record):
    log_record.msg = 12345
    assert security_filter.filter(log_record)
    assert log_record.msg == 12345


def test_setup_logging_default():
    setup_logging()


def test_setup_logging_with_file(temp_dir):
    log_file = temp_dir / "test.log"
    setup_logging(log_file=str(log_file))
    assert log_file.exists()


def test_setup_logging_verbose():
    setup_logging(verbose=True)


def test_security_filter_applied(temp_dir):
    log_file = temp_dir / "test.log"
    setup_logging(log_file=str(log_file))

    logger = logging.getLogger()
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            filters = [f for f in handler.filters if isinstance(f, SecurityFilter)]
            assert len(filters) > 0
