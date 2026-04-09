# -*- coding: utf-8 -*-
"""
Extension ID 자동 반영 스크립트
cws_submit.py 실행 후 자동으로 호출됩니다.
수동 실행: python apply_extension_id.py
"""

import pathlib, sys, subprocess

BASE = pathlib.Path(__file__).parent
ID_FILE = BASE / '.extension_id'

def apply(ext_id):
    ext_id = ext_id.strip()
    if not ext_id or len(ext_id) != 32:
        print(f'ERROR: Invalid Extension ID: "{ext_id}"')
        sys.exit(1)

    files = {
        BASE / 'popup.html': 'EXTENSION_ID',
        BASE / 'docs' / 'index.html': 'EXTENSION_ID',
        BASE / 'README.md': 'EXTENSION_ID',
    }

    changed = []
    for path, placeholder in files.items():
        if not path.exists():
            continue
        content = path.read_text(encoding='utf-8')
        if placeholder in content:
            path.write_text(content.replace(placeholder, ext_id), encoding='utf-8')
            changed.append(path.name)
            print(f'  Updated: {path.name}')

    if not changed:
        print('  No placeholders found. Already applied?')
        return

    # Git commit & push
    print('\n  Committing to GitHub...')
    subprocess.run(['git', 'add', '-A'], cwd=BASE, check=True)
    subprocess.run(
        ['git', 'commit', '-m', f'Set Chrome Extension ID: {ext_id}'],
        cwd=BASE, check=True
    )
    subprocess.run(['git', 'push'], cwd=BASE, check=True)
    print(f'\n  Done! Extension ID {ext_id} applied and pushed.')
    print(f'  Store page: https://chromewebstore.google.com/detail/walmart-smart-filter/{ext_id}')

if __name__ == '__main__':
    if ID_FILE.exists():
        ext_id = ID_FILE.read_text().strip()
        print(f'\nExtension ID found: {ext_id}')
        apply(ext_id)
    elif len(sys.argv) > 1:
        apply(sys.argv[1])
    else:
        ext_id = input('Extension ID (32 chars): ').strip()
        apply(ext_id)
