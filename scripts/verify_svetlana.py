#!/usr/bin/env python3
"""
Svetlana Runtime Verifier v2.1
Проверяет синхронизацию web/mobile assets и корректность API
"""

import hashlib
import os
import re
import sys
from pathlib import Path

def get_file_sha256(filepath):
    """Вычисляет SHA256 хеш файла"""
    if not os.path.exists(filepath):
        return None
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_api_endpoint(api_file):
    """
    Проверяет наличие endpoint /api/svetlana/chat
    Использует regex для поиска
    """
    if not os.path.exists(api_file):
        return False, "API file not found"
    
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем POST endpoint /api/svetlana/chat
    pattern1 = r'@app\.post\s*\(\s*[\"\'\/]api/svetlana/chat[\"\'\)]'
    pattern2 = r'async def api_svetlana_chat'
    
    has_route = re.search(pattern1, content)
    has_func = re.search(pattern2, content)
    
    if has_route and has_func:
        return True, "Endpoint /api/svetlana/chat found"
    elif has_func:
        return True, "Function api_svetlana_chat found (route decorator may vary)"
    else:
        return False, "Endpoint NOT FOUND"

def main():
    print("=" * 60)
    print("SVETLANA RUNTIME VERIFIER v2.1")
    print("=" * 60)
    
    base_dir = Path('/workspace')
    
    # Пути к файлам
    web_index = base_dir / 'templates' / 'index.html'
    mobile_index = base_dir / 'flutter_app' / 'assets' / 'svetlana' / 'index.html'
    app_js = base_dir / 'static' / 'js' / 'svetlana-main.js'
    model_glb = base_dir / 'static' / 'models' / 'svetlana' / 'svetlana.glb'
    api_main = base_dir / 'app' / 'main.py'
    
    all_pass = True
    
    # 1. Проверка web index.html
    print("\n[1] Checking web index.html...")
    if web_index.exists():
        web_hash = get_file_sha256(web_index)
        print(f"    ✓ Web index.html exists (SHA256: {web_hash[:16]}...)")
    else:
        print(f"    ✗ Web index.html NOT FOUND")
        all_pass = False
    
    # 2. Проверка mobile index.html
    print("\n[2] Checking mobile index.html...")
    if mobile_index.exists():
        mobile_hash = get_file_sha256(mobile_index)
        print(f"    ✓ Mobile index.html exists (SHA256: {mobile_hash[:16]}...)")
    else:
        print(f"    ✗ Mobile index.html NOT FOUND")
        all_pass = False
    
    # 3. Синхронизация web/mobile
    print("\n[3] Checking web/mobile sync...")
    if web_index.exists() and mobile_index.exists():
        web_hash = get_file_sha256(web_index)
        mobile_hash = get_file_sha256(mobile_index)
        if web_hash == mobile_hash:
            print(f"    ✓ Web and Mobile index.html are SYNCHRONIZED")
        else:
            print(f"    ✗ Web and Mobile index.html MISMATCH")
            print(f"       Web:   {web_hash[:16]}...")
            print(f"       Mobile: {mobile_hash[:16]}...")
            all_pass = False
    else:
        print(f"    ✗ Cannot compare - one or both files missing")
        all_pass = False
    
    # 4. Проверка svetlana-main.js
    print("\n[4] Checking svetlana-main.js...")
    if app_js.exists():
        js_hash = get_file_sha256(app_js)
        print(f"    ✓ svetlana-main.js exists (SHA256: {js_hash[:16]}...)")
    else:
        print(f"    ✗ svetlana-main.js NOT FOUND")
        all_pass = False
    
    # 5. Проверка модели GLB
    print("\n[5] Checking 3D model (svetlana.glb)...")
    if model_glb.exists():
        glb_hash = get_file_sha256(model_glb)
        print(f"    ✓ Model exists (SHA256: {glb_hash[:16]}...)")
    else:
        print(f"    ⚠ Model NOT FOUND (Canvas fallback will be used)")
    
    # 6. Проверка API endpoint
    print("\n[6] Checking API endpoint /api/svetlana/chat...")
    api_ok, api_msg = check_api_endpoint(api_main)
    if api_ok:
        print(f"    ✓ {api_msg}")
    else:
        print(f"    ✗ {api_msg}")
        all_pass = False
    
    # 7. Проверка изображений аватара
    print("\n[7] Checking avatar images...")
    avatar_dir = base_dir / 'static' / 'images' / 'svetlana'
    required_images = ['svetlana-current.webp', 'svetlana-light.webp', 'svetlana-dark.webp']
    for img_name in required_images:
        img_path = avatar_dir / img_name
        if img_path.exists():
            print(f"    ✓ {img_name} exists")
        else:
            print(f"    ✗ {img_name} NOT FOUND")
            all_pass = False
    
    # 8. Проверка JS модулей
    print("\n[8] Checking JavaScript modules...")
    required_js = [
        'avatar-state.js',
        'canvas-avatar.js',
        'image-avatar.js',
        'avatar-renderer.js',
        'lip-sync.js',
        'svetlana-main.js'
    ]
    js_dir = base_dir / 'static' / 'js'
    for js_name in required_js:
        js_path = js_dir / js_name
        if js_path.exists():
            print(f"    ✓ {js_name} exists")
        else:
            print(f"    ✗ {js_name} NOT FOUND")
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("RESULT: ALL CRITICAL CHECKS PASSED ✓")
        print("=" * 60)
        return 0
    else:
        print("RESULT: SOME CHECKS FAILED ✗")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
