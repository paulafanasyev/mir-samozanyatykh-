import re, pathlib
from collections import defaultdict
backend=defaultdict(list)
for p in pathlib.Path('app/api').glob('*.py'):
    text=p.read_text(errors='ignore')
    prefix=re.search(r'APIRouter\(prefix=["\']([^"\']+)', text)
    if not prefix: continue
    base=prefix.group(1)
    for m in re.finditer(r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)', text, re.I):
        backend[(m.group(1).upper(), base+m.group(2))].append(str(p))
# obvious stale frontend paths from source literals
frontend=set()
for p in pathlib.Path('frontend/src').rglob('*'):
    if p.suffix not in {'.ts','.tsx','.js','.jsx'}: continue
    text=p.read_text(errors='ignore')
    for m in re.finditer(r'["\'](/api/[^"\']+)["\']', text): frontend.add(m.group(1))
def normalize(path):
    path = path.split('?', 1)[0]
    if path != '/api': path = path.rstrip('/')
    return path

normalized_backend = {(method, normalize(path)) for method, path in backend}

print(f'BACKEND_ROUTES={len(backend)}')
print(f'FRONTEND_LITERAL_PATHS={len(frontend)}')
missing=[]
for path in sorted(frontend):
    if '{' in path: continue
    matches=[k for k in normalized_backend if k[1]==normalize(path)]
    if not matches:
        missing.append(path)
        print('MISSING_FRONTEND_PATH', path)
duplicates=[]
for k,v in backend.items():
    if len(v)>1:
        duplicates.append((k,v))
        print('DUPLICATE_BACKEND_ROUTE',k,v)
if missing or duplicates:
    raise SystemExit(f'API CONTRACT FAIL: missing={len(missing)} duplicates={len(duplicates)}')
print('API CONTRACT PASS')
