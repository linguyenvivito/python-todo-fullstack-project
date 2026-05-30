import json
import logging
import sys

from app.core.logging_config import JsonFormatter


def test_json_formatter_outputs_structured_log() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.request",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="GET /health -> %s",
        args=(200,),
        exc_info=None,
    )

    output = formatter.format(record)
    payload = json.loads(output)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.request"
    assert payload["message"] == "GET /health -> 200"
    assert "timestamp" in payload


def test_json_formatter_includes_exception_text() -> None:
    formatter = JsonFormatter()

    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            name="app.request",
            level=logging.ERROR,
            pathname=__file__,
            lineno=25,
            msg="request failed",
            args=(),
            exc_info=True,
        )
        record.exc_info = sys.exc_info()

    output = formatter.format(record)
    payload = json.loads(output)

    assert payload["level"] == "ERROR"
    assert payload["message"] == "request failed"
    assert "ValueError: boom" in payload["exception"]
