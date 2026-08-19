from __future__ import annotations
import hashlib, json, pathlib, re, subprocess, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
WEB = ROOT / 'frontend/public/svetlana'
MOBILE = ROOT / 'mobile/assets/svetlana'
SOURCE = DOCS / 'source-archives/svetlana-avatar-v13.0.zip'
errors=[]

def sha(p: pathlib.Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def require(cond,msg):
    if not cond: errors.append(msg)

required=('app.js','index.html','model_base.glb','assets/svetlana_tts_smoke_test.wav',
          'runtime/svetlana-v9-bridge.js','runtime/svetlana-v10-host.js','runtime/svetlana-v11-tts-adapter.js')
for base in (WEB,MOBILE):
    for rel in required:
        require((base/rel).is_file(), f'missing {base/rel}')

if SOURCE.exists():
    try:
        with zipfile.ZipFile(SOURCE) as z:
            require(z.testzip() is None, 'source archive CRC/integrity failure')
    except Exception as e:
        errors.append(f'source archive is not readable: {e!r}')

for rel in ('app.js','model_base.glb','assets/svetlana_tts_smoke_test.wav'):
    require(sha(WEB/rel)==sha(MOBILE/rel), f'web/mobile mismatch: {rel}')
require((WEB/'index.html').read_bytes()==(MOBILE/'index.html').read_bytes(), 'web/mobile mismatch: index.html')

app=(WEB/'app.js').read_text()
require('SvetlanaHealth' in app, 'health API missing')
require('nativeMorphNames' in app, 'native morph rig missing')
require("./vendor/three/0.179.1/three.module.js" in app, 'Three.js local runtime import missing')
require("./vendor/three/0.179.1/examples/jsm/loaders/GLTFLoader.js" in app, 'GLTFLoader local runtime import missing')
for base in (WEB, MOBILE):
    vendor = base/'vendor/three/0.179.1'
    for rel in ('three.module.js','three.core.js','examples/jsm/loaders/GLTFLoader.js','examples/jsm/utils/BufferGeometryUtils.js','THREE_VENDOR_LOCK.json'):
        require((vendor/rel).is_file(), f'missing Three.js vendor dependency {vendor/rel}')

# Runtime command bridge hardening checks.
bridge=(WEB/'runtime/svetlana-v9-bridge.js').read_text()
require("e.origin === window.location.origin" in bridge, 'bridge accepts non-origin/null postMessage')
require('ALLOWED_EMOTIONS' in bridge and 'MAX_QUEUE' in bridge and 'MAX_TEXT' in bridge, 'bridge input limits missing')
require(bridge == (MOBILE/'runtime/svetlana-v9-bridge.js').read_text(), 'web/mobile bridge mismatch')

# Legacy server-rendered chat must not interpolate AI/user text into HTML.
base=(ROOT/'templates/base.html').read_text()
require('body.textContent = String(text ?? \'\');' in base, 'server chat XSS hardening missing')
require('${text.replace(/\\n/g, \'<br>\')}' not in base, 'unsafe chat HTML interpolation remains')

# Chat endpoint must have explicit rate limiting.
api=(ROOT/'app/api/svetlana.py').read_text()
require('@limiter.limit("30/minute")' in api, 'Svetlana chat rate limit missing')
require('request: Request' in api, 'Svetlana chat request parameter missing for rate limiter')

# Check all JavaScript runtime files.
for p in list(ROOT.glob('frontend/public/**/*.js')) + list(ROOT.glob('mobile/assets/**/*.js')):
    r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    require(r.returncode==0, f'JS syntax failure: {p}: {r.stderr.strip()}')

r=subprocess.run([sys.executable,'-m','compileall','-q',str(ROOT/'app')],capture_output=True,text=True)
require(r.returncode==0, f'Python compile failure: {r.stderr.strip()}')

result={
 'web_model_sha256':sha(WEB/'model_base.glb'),
 'mobile_model_sha256':sha(MOBILE/'model_base.glb'),
 'web_app_sha256':sha(WEB/'app.js'),
 'mobile_app_sha256':sha(MOBILE/'app.js'),
 'source_archive_sha256':sha(SOURCE) if SOURCE.exists() else None,
 'source_archive_bytes':SOURCE.stat().st_size if SOURCE.exists() else None,
 'external_three_runtime': ('cdn.jsdelivr.net' in app or 'unpkg.com' in app or 'cdnjs.cloudflare.com' in app),
 'local_three_runtime_present': all((base/'vendor/three/0.179.1'/rel).is_file() for base in (WEB,MOBILE) for rel in ('three.module.js','three.core.js','examples/jsm/loaders/GLTFLoader.js','examples/jsm/utils/BufferGeometryUtils.js')),
 'security_checks':{
   'chat_rate_limit': '@limiter.limit("30/minute")' in api,
   'legacy_chat_text_only': 'body.textContent = String(text ?? \'\');' in base,
   'bridge_origin_locked': "e.origin === window.location.origin" in bridge,
   'bridge_input_limits': all(x in bridge for x in ('ALLOWED_EMOTIONS','MAX_QUEUE','MAX_TEXT')),
 },
 'errors':errors,
 'status':'PASS' if not errors else 'FAIL'
}
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(1 if errors else 0)
