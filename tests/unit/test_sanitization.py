from app.core.sanitization import sanitize_optional_text, sanitize_text


def test_sanitize_text_removes_html_tags() -> None:
    raw = "<script>alert('x')</script><b>Hello</b>"

    cleaned = sanitize_text(raw)

    assert "<" not in cleaned
    assert "script" not in cleaned.lower()
    assert cleaned == "alert('x')Hello"


def test_sanitize_text_trims_surrounding_whitespace() -> None:
    assert sanitize_text("   hello world   ") == "hello world"


def test_sanitize_text_keeps_plain_text() -> None:
    assert sanitize_text("safe-text_123") == "safe-text_123"


def test_sanitize_optional_text_none_passthrough() -> None:
    assert sanitize_optional_text(None) is None


def test_sanitize_optional_text_sanitizes_present_value() -> None:
    assert sanitize_optional_text(" <i>Hi</i> ") == "Hi"
