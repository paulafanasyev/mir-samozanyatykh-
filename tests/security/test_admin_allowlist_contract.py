"""Контракт безопасности явного ADMIN allowlist."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings

EXPECTED = {
    "xongphavietnam@gmail.com",
    "it-laboratory@bk.ru",
}


def test_admin_allowlist_is_exactly_expected():
    configured = {
        email.strip().lower()
        for email in settings.ADMIN_EMAILS.split(",")
        if email.strip()
    }
    assert configured == EXPECTED
    assert len(configured) == 2


def test_admin_allowlist_contains_no_passwords():
    for email in settings.ADMIN_EMAILS.split(","):
        value = email.strip()
        assert "://" not in value
        assert "=" not in value
        assert " " not in value
