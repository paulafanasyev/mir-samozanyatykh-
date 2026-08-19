from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
checks = []

def check(name, ok):
    checks.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name)

bank = (ROOT / 'app/api/bank.py').read_text()
svetlana = (ROOT / 'mobile/lib/presentation/screens/svetlana/svetlana_screen.dart').read_text()
analytics = (ROOT / 'mobile/lib/presentation/screens/analytics/analytics_screen.dart').read_text()
integrations = (ROOT / 'mobile/lib/presentation/screens/integrations/integrations_screen.dart').read_text()
reports = (ROOT / 'app/api/reports.py').read_text()
html_routes = (ROOT / 'app/html_routes.py').read_text()
api_client = (ROOT / 'mobile/lib/data/datasources/remote/api_client.dart').read_text()

check('bank external errors do not expose provider status text', 'detail=f"Tinkoff API error:' not in bank)
check('Svetlana screen calls real API', 'sendMessage(text)' in svetlana and 'Simulate AI response' not in svetlana)
check('Svetlana screen has no fabricated response generator', '_generateResponse(' not in svetlana)
check('analytics screen loads real dashboard', 'getDashboardStats()' in analytics)
check('analytics screen loads real revenue chart', 'getRevenueAnalytics(months: 6)' in analytics)
check('analytics fake hardcoded values removed', '450 000 ₽' not in analytics and 'FlSpot(0, 1)' not in analytics)
check('integrations screen loads API keys and webhooks', 'getApiKeys()' in integrations and 'getWebhooks()' in integrations)
check('integrations screen can revoke API keys', 'revokeApiKey' in integrations)
check('reports revenue endpoint emits application/pdf', 'media_type="application/pdf"' in reports)
check('reports clients endpoint emits application/pdf', reports.count('media_type="application/pdf"') >= 2)
check('report font asset exists', (ROOT / 'app/assets/fonts/DejaVuSans.ttf').exists())
check('legacy demo profile data removed', 'demo@example.com' not in html_routes and 'Демо Пользователь' not in html_routes)
check('mobile API client exposes Svetlana API', 'getSvetlanaHistory' in api_client and 'sendMessage' in api_client)

fails = [n for n, ok in checks if not ok]
print(f'RESULT: {len(checks)-len(fails)}/{len(checks)} PASS')
raise SystemExit(1 if fails else 0)
