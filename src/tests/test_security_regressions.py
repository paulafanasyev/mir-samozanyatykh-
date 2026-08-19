import base64
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_no_legacy_plaintext_auth_tokens():
    auth = (ROOT / "app/api/auth.py").read_text()
    assert "email_verification_token=" not in auth
    assert "User.email_verification_token ==" not in auth
    assert "user.email_verification_token =" not in auth

def test_frontend_does_not_persist_access_token():
    store = (ROOT / "frontend/src/stores/authStore.ts").read_text()
    assert "persist(" not in store
    assert "localStorage.setItem" not in store
    for name in ['login.html','dashboard.html','marketplace.html','finance.html','crm.html','grants.html','achievements.html']:
        html = (ROOT / 'templates' / name).read_text()
        assert "localStorage.setItem('access_token'" not in html
        assert "localStorage.getItem('access_token'" not in html

def test_nginx_has_no_unsafe_inline_or_legacy_xss_header():
    nginx = (ROOT / "nginx/nginx.conf").read_text()
    assert "unsafe-inline" not in nginx
    assert "X-XSS-Protection" not in nginx

def test_bank_code_uses_authenticated_encryption():
    bank = (ROOT / "app/api/bank.py").read_text()
    assert "base64.b64encode(token.encode())" not in bank
    assert "get_token_encryption().encrypt" in bank
    assert "BANK_ENCRYPTION_KEY" in (ROOT / 'app/core/config.py').read_text()

def test_release_has_no_repo_or_runtime_artifacts():
    bad = []
    for p in ROOT.rglob("*"):
        if p.name in {".git", "__pycache__", "test.db"} or p.suffix in {".pyc", ".pyo", ".log"}:
            bad.append(p)
    assert not bad, bad

def test_refresh_rotation_locks_session_row():
    auth = (ROOT / 'app/api/auth.py').read_text()
    assert '.with_for_update()' in auth

def test_pending_2fa_tokens_cannot_access_api():
    security = (ROOT / 'app/core/security.py').read_text()
    assert '2fa_pending' in security and 'cannot access protected resources' in security

def test_mfa_backup_codes_are_hashed():
    mfa = (ROOT / 'app/api/mfa.py').read_text()
    assert 'get_password_hash(code)' in mfa
    assert 'verify_password(verify.code' in mfa
