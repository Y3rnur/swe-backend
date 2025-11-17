"""Logging configuration tests."""

import json
import logging

from app.core.logging import JSONFormatter, setup_logging


def test_json_formatter():
    """Test JSON formatter produces valid JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)

    # Should be valid JSON
    parsed = json.loads(formatted)
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
    assert "timestamp" in parsed


def test_logging_dev_mode(capsys):
    """Test that dev mode uses human-readable format."""
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    setup_logging("INFO", "dev")

    logger = logging.getLogger("test")
    logger.info("Test message")

    # Capture stdout
    captured = capsys.readouterr()
    output = captured.out

    # Should be human-readable, not JSON
    assert "Test message" in output
    # Should not be JSON (no opening brace at start)
    assert not output.strip().startswith("{")


def test_logging_production_mode(capsys):
    """Test that production mode uses JSON format."""
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    setup_logging("INFO", "production")

    logger = logging.getLogger("test")
    logger.info("Test message")

    # Capture stdout
    captured = capsys.readouterr()
    output = captured.out

    # Should be JSON
    assert output.strip().startswith("{")
    parsed = json.loads(output.strip())
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
