import json
import logging
import sys

from app.core import logging_config as logging_config_module
from app.core.logging_config import JsonFormatter, configure_logging


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


def test_configure_logging_uses_json_formatter_when_enabled(mocker) -> None:
    fake_handler = mocker.Mock()
    mocker.patch.object(logging_config_module, "_LOGGING_CONFIGURED", False)
    mocker.patch("app.core.logging_config.os.getenv", side_effect=lambda key, default=None: {
        "LOG_LEVEL": "debug",
        "LOG_JSON": "true",
    }.get(key, default))
    mocker.patch("app.core.logging_config.logging.StreamHandler", return_value=fake_handler)
    basic_config = mocker.patch("app.core.logging_config.logging.basicConfig")

    configure_logging()

    fake_handler.setFormatter.assert_called_once()
    formatter = fake_handler.setFormatter.call_args.args[0]
    assert isinstance(formatter, JsonFormatter)
    basic_config.assert_called_once_with(level=logging.DEBUG, handlers=[fake_handler], force=True)
    assert logging_config_module._LOGGING_CONFIGURED is True


def test_configure_logging_uses_plain_formatter_when_json_disabled(mocker) -> None:
    fake_handler = mocker.Mock()
    mocker.patch.object(logging_config_module, "_LOGGING_CONFIGURED", False)
    mocker.patch("app.core.logging_config.os.getenv", side_effect=lambda key, default=None: {
        "LOG_LEVEL": "warning",
        "LOG_JSON": "false",
        "LOG_FORMAT": "%(levelname)s::%(message)s",
    }.get(key, default))
    mocker.patch("app.core.logging_config.logging.StreamHandler", return_value=fake_handler)
    basic_config = mocker.patch("app.core.logging_config.logging.basicConfig")

    configure_logging()

    fake_handler.setFormatter.assert_called_once()
    formatter = fake_handler.setFormatter.call_args.args[0]
    assert isinstance(formatter, logging.Formatter)
    assert not isinstance(formatter, JsonFormatter)
    assert formatter._style._fmt == "%(levelname)s::%(message)s"
    basic_config.assert_called_once_with(level=logging.WARNING, handlers=[fake_handler], force=True)
    assert logging_config_module._LOGGING_CONFIGURED is True


def test_configure_logging_is_idempotent(mocker) -> None:
    mocker.patch.object(logging_config_module, "_LOGGING_CONFIGURED", True)
    basic_config = mocker.patch("app.core.logging_config.logging.basicConfig")

    configure_logging()

    basic_config.assert_not_called()
