"""Static regression checks for v8.4.37 distributed infrastructure hardening."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = {
    "Redis rate limiter": 'from redis.asyncio import Redis' in (ROOT/'app/core/rate_limiter.py').read_text(),
    "Production rate-limit fail closed": 'Rate limiting service unavailable' in (ROOT/'app/core/rate_limiter.py').read_text(),
    "Atomic Redis increment": 'await redis.incr(key)' in (ROOT/'app/core/rate_limiter.py').read_text(),
    "Redis cache": 'REDIS_DB_CACHE' in (ROOT/'app/core/cache.py').read_text(),
    "Production cache no unsafe local fallback": 'if settings.ENVIRONMENT.lower() == "production":' in (ROOT/'app/core/cache.py').read_text(),
    "No previous in-memory rate-limit declaration": 'In-memory storage' not in (ROOT/'app/core/rate_limiter.py').read_text(),
    "No previous in-memory cache declaration": 'Simple in-memory cache' not in (ROOT/'app/core/cache.py').read_text(),
    "Version backend": '8.4.37' in (ROOT/'app/core/config.py').read_text(),
    "Version web": '8.4.37' in (ROOT/'frontend/package.json').read_text(),
    "Version mobile": '8.4.37+860' in (ROOT/'mobile/pubspec.yaml').read_text(),
}
failed=[k for k,v in checks.items() if not v]
if failed:
    print('v8.4.37 integrity: FAIL', failed); raise SystemExit(1)
print('v8.4.37 integrity: 10/10 PASS')
