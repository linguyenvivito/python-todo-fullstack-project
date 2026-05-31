from app.slices.email.dependencies import get_email_service


def test_get_email_service_returns_singleton_instance() -> None:
    first = get_email_service()
    second = get_email_service()

    assert first is second
