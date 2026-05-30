from typing import Optional

import bleach


def sanitize_text(value: str) -> str:
    return bleach.clean(value, tags=[], attributes={}, strip=True).strip()


def sanitize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return sanitize_text(value)
