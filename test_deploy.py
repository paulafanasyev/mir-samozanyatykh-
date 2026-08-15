"""
Pre-deployment test script
MIR Samozanyatykh v8.4.1 - ANO TsPS INN 9724016805
"""

import sys
import importlib

def test_imports():
    """Test all critical imports"""
    modules = [
        "fastapi",
        "sqlalchemy",
        "asyncpg",
        "redis",
        "pydantic",
        "jwt",
        "passlib",
        "bcrypt",
        "slowapi",
        "httpx",
        "aiohttp",
        "jinja2",
        "reportlab",
        "qrcode",
        "PIL",
        "email_validator",
        "cryptography",
        "pyotp",
        "prometheus_client",
    ]

    failed = []
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"  ✅ {mod}")
        except ImportError as e:
            print(f"  ❌ {mod}: {e}")
            failed.append(mod)

    return failed

def test_app_imports():
    """Test app module imports"""
    import os
    os.chdir("/app")  # Adjust path as needed

    try:
        from app.core.config import settings
        print("  ✅ app.core.config")

        from app.core.database import Base, engine
        print("  ✅ app.core.database")

        from app.core.security import get_password_hash
        print("  ✅ app.core.security")

        from app.core.rate_limit import limiter
        print("  ✅ app.core.rate_limit")

        from app.core.xss_protection import sanitize_html
        print("  ✅ app.core.xss_protection")

        from app.services.yookassa import yookassa_service_instance
        print("  ✅ app.services.yookassa")

        from app.services.ssrf import SSRFProtector
        print("  ✅ app.services.ssrf")

        return []
    except Exception as e:
        print(f"  ❌ App import failed: {e}")
        return [str(e)]

if __name__ == "__main__":
    print("="*60)
    print("MIR Samozanyatykh v8.4.1 - Pre-deployment Tests")
    print("="*60)

    print("
📦 Testing Python dependencies:")
    failed_deps = test_imports()

    print("
🔧 Testing app modules:")
    failed_app = test_app_imports()

    print("
" + "="*60)
    if not failed_deps and not failed_app:
        print("✅ ALL TESTS PASSED - Ready for deployment!")
    else:
        print(f"❌ TESTS FAILED: {len(failed_deps)} deps, {len(failed_app)} app")
        sys.exit(1)
    print("="*60)
