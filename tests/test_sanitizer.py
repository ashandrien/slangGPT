import re
from backend.main import sanitize_text, MAX_TEXT_LENGTH


def test_sanitize_removes_null_and_control_chars():
    raw = "Hello\x00World\x07\x1f!"
    cleaned = sanitize_text(raw)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "\x1f" not in cleaned
    assert cleaned == "HelloWorld!"


def test_sanitize_truncates_long_input():
    long = "a" * (MAX_TEXT_LENGTH + 100)
    cleaned = sanitize_text(long)
    assert len(cleaned) == MAX_TEXT_LENGTH


def test_sanitize_handles_none_and_nonstring():
    assert sanitize_text(None) == ""
    assert sanitize_text(12345) == "12345"
