from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
errors=[]

# Web invoice payload must match InvoiceCreate: client_id + non-empty items.
inv=(root/'frontend/src/pages/Invoices.tsx').read_text()
for needle in ["client_id: Number(form.client_id)", "items: [{ description: form.description, quantity: Number(form.quantity) || 1, unit_price: Number(form.unit_price) }]"]:
    if needle not in inv: errors.append(f"Web invoice contract missing: {needle}")
# Mobile invoice payload contract.
mi=(root/'mobile/lib/presentation/screens/invoices/invoices_screen.dart').read_text()
if "'client_id': clientId" not in mi or "'items': [{'description': description.text.trim(), 'quantity': 1, 'unit_price': amount}]" not in mi:
    errors.append('Mobile invoice payload contract missing')
# Mobile deal payload contract.
md=(root/'mobile/lib/presentation/screens/deals/deals_screen.dart').read_text()
if "'client_id': clientId" not in md: errors.append('Mobile deal create requires client_id')
# Mobile move contract must use query stage_id.
ac=(root/'mobile/lib/data/datasources/remote/api_client.dart').read_text()
if "moveDeal(int id, int stageId)" not in ac or "queryParameters: {'stage_id': stageId}" not in ac:
    errors.append('Mobile deal move contract mismatch')
# Tax reports are a list, mobile must normalize list.
tr=(root/'mobile/lib/presentation/screens/accounting/tax_reports_screen.dart').read_text()
if "response.data is List" not in tr: errors.append('Mobile tax reports list normalization missing')
# Invoice list is paginated dict.
if "res.data?.invoices || []" not in inv: errors.append('Web invoice list normalization missing')
# No raw Dio in presentation screens (shared client handles refresh/auth).
for p in (root/'mobile/lib/presentation/screens').rglob('*.dart'):
    if 'package:dio/dio.dart' in p.read_text(): errors.append(f'Raw Dio import remains: {p.relative_to(root)}')
# Python compilation already handled externally; ensure no accidental debug markers in core app.
for p in [root/'frontend/src/pages/Invoices.tsx', root/'frontend/src/pages/Deals.tsx']:
    txt=p.read_text()
    if 'console.log(' in txt: errors.append(f'Debug console.log: {p.relative_to(root)}')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print('FUNCTIONAL CONTRACT AUDIT: PASS')
