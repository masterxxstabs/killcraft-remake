"""Download free gun models from Sketchfab and put them in the game.

You need a free Sketchfab account and its API token:
    sketchfab.com -> log in -> Settings -> Password & API -> "API token"

Easiest: just run it and answer the questions
    python tools/sketchfab_guns.py

Or use commands:
    python tools/sketchfab_guns.py search                    # most-liked downloadable guns
    python tools/sketchfab_guns.py search shotgun            # search for words
    python tools/sketchfab_guns.py get <model uid or link> <weapon id>
    python tools/sketchfab_guns.py list                      # which weapons have a model
    python tools/sketchfab_guns.py remove <weapon id>        # go back to the block model
    python tools/sketchfab_guns.py credits                   # rebuild models/CREDITS.md

The token is read from the SKETCHFAB_API_TOKEN environment variable, or asked
for (and, if you say yes, remembered in ~/.blockhold/sketchfab_token - never
inside the game folder, so it can't end up on GitHub).

Licences: by default only models you may share are listed (CC0, CC-BY,
CC-BY-SA). CC-BY means you MUST credit the author - this tool writes
models/CREDITS.md for you, and the game shows it in the credits.
Use --license any to see everything.
"""
import argparse
import getpass
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

GAME_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = GAME_DIR / 'models'
TOKEN_FILE = Path.home() / '.blockhold' / 'sketchfab_token'
API = os.environ.get('SKETCHFAB_API', 'https://api.sketchfab.com/v3')
SAFE_LICENSES = ('cc0', 'by', 'by-sa')

LICENSE_SLUGS = {
    'cc0': 'cc0', 'public domain': 'cc0',
    'attribution-noncommercial-sharealike': 'by-nc-sa',
    'attribution-noncommercial-noderivs': 'by-nc-nd',
    'attribution-noncommercial': 'by-nc',
    'attribution-sharealike': 'by-sa',
    'attribution-noderivs': 'by-nd',
    'attribution': 'by',
}


# ── helpers ──────────────────────────────────────────────────────────────────
def weapon_ids():
    sys.path.insert(0, str(GAME_DIR))
    from blockhold.data.weapons import WEAPONS
    return [(w['id'], w['name']) for w in WEAPONS]


def license_slug(lic):
    if not lic:
        return '?'
    if isinstance(lic, str):
        lic = {'label': lic}
    if lic.get('slug'):
        return lic['slug']
    label = (lic.get('label') or '').lower()
    for key, slug in LICENSE_SLUGS.items():     # longest names are checked first
        if key in label:
            return slug
    return label or '?'


def request(url, token=None):
    headers = {'User-Agent': 'blockhold-model-tool'}
    if token:
        headers['Authorization'] = f'Token {token}'
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.loads(r.read().decode())


def download(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': 'blockhold-model-tool'})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, 'wb') as f:
        total = int(r.headers.get('Content-Length') or 0)
        done = 0
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f'\r  downloading... {done * 100 // total}%', end='', flush=True)
    print()


def get_token(ask=True):
    token = os.environ.get('SKETCHFAB_API_TOKEN')
    if token:
        return token.strip()
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    if not ask:
        return None
    print('\nSketchfab needs your API token to download models.')
    print('Find it at: sketchfab.com -> Settings -> Password & API -> API token')
    token = getpass.getpass('Paste your token (it stays hidden): ').strip()
    if token and input('Remember it on this computer? (y/n) ').lower().startswith('y'):
        TOKEN_FILE.parent.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(token)
        try:
            TOKEN_FILE.chmod(0o600)
        except OSError:
            pass
        print(f'Saved to {TOKEN_FILE}')
    return token


def parse_uid(text):
    """Accepts a uid or any Sketchfab model link."""
    m = re.search(r'([0-9a-f]{32})', text)
    if not m:
        sys.exit(f'That does not look like a Sketchfab model link or uid: {text}')
    return m.group(1)


# ── commands ─────────────────────────────────────────────────────────────────
def search(words='', licenses=SAFE_LICENSES, count=24, cursor=None):
    params = {'type': 'models', 'downloadable': 'true', 'tags': 'gun', 'sort_by': '-likeCount', 'count': count}
    if words:
        params['q'] = words
        del params['tags']
    if cursor:
        params['cursor'] = cursor
    data = request(f'{API}/search?{urllib.parse.urlencode(params)}')
    out = []
    for m in data.get('results', []):
        lic = m.get('license')
        if lic is None:          # search results sometimes leave it out: ask for the model itself
            try:
                lic = request(f"{API}/models/{m['uid']}").get('license')
            except Exception:
                lic = None
        slug = license_slug(lic)
        if licenses != 'any' and slug not in licenses:
            continue
        user = m.get('user') or {}
        out.append(dict(uid=m['uid'], name=m.get('name', '?'), author=user.get('displayName') or user.get('username', '?'),
                        likes=m.get('likeCount', 0), faces=m.get('faceCount', 0), license=slug,
                        url=m.get('viewerUrl') or f"https://sketchfab.com/3d-models/{m['uid']}"))
    nxt = (data.get('cursors') or {}).get('next')
    return out, nxt


def print_results(results):
    if not results:
        print('No models found with those licences. Try other words, or --license any')
    for i, m in enumerate(results, 1):
        heavy = '  (very detailed - may be slow)' if m['faces'] > 150_000 else ''
        print(f"{i:3d}. {m['name'][:40]:40s} by {m['author'][:18]:18s} {m['license']:8s} "
              f"{m['likes']:5d} likes{heavy}\n     {m['url']}")


def get(uid, weapon, token):
    ids = [w for w, _ in weapon_ids()]
    if weapon not in ids:
        sys.exit(f"Unknown weapon '{weapon}'. Weapons: {', '.join(ids)}")
    info = request(f'{API}/models/{uid}')
    slug = license_slug(info.get('license'))
    lic = info.get('license') or {}
    user = info.get('user') or {}
    print(f"\n{info.get('name')} by {user.get('displayName') or user.get('username')}  -  licence: {lic.get('label', slug)}")
    if slug not in SAFE_LICENSES:
        print(f"  Note: this licence ({slug}) has extra rules. Check {lic.get('url', 'the model page')} before sharing the game.")
    try:
        dl = request(f'{API}/models/{uid}/download', token)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            sys.exit('Sketchfab said no: check your API token (and that the model is downloadable).')
        raise
    target = MODELS_DIR / weapon
    tmp = Path(tempfile.mkdtemp(prefix='blockhold_'))
    try:
        if dl.get('glb', {}).get('url'):
            print(f"  GLB file, {dl['glb'].get('size', 0) / 1e6:.1f} MB")
            download(dl['glb']['url'], tmp / 'model.glb')
            files = [tmp / 'model.glb']
        elif dl.get('gltf', {}).get('url'):
            print(f"  glTF archive, {dl['gltf'].get('size', 0) / 1e6:.1f} MB")
            download(dl['gltf']['url'], tmp / 'model.zip')
            with zipfile.ZipFile(tmp / 'model.zip') as z:
                for name in z.namelist():           # don't let a bad zip write outside the folder
                    if name.startswith('/') or '..' in Path(name).parts:
                        sys.exit(f'Refusing suspicious file in archive: {name}')
                z.extractall(tmp / 'unzipped')
            files = list((tmp / 'unzipped').iterdir())
        else:
            sys.exit('Sketchfab did not offer a glTF / GLB download for this model.')
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        for f in files:
            shutil.move(str(f), target / f.name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    meta = dict(
        uid=uid, name=info.get('name'), author=user.get('displayName') or user.get('username'),
        author_url=user.get('profileUrl'), license=lic.get('label', slug), license_slug=slug,
        license_url=lic.get('url'), source_url=info.get('viewerUrl') or f'https://sketchfab.com/3d-models/{uid}',
    )
    (target / 'model.json').write_text(json.dumps(meta, indent=2))
    write_credits()
    print(f'\nDone! Saved to {target}')
    print('Start the game and hold that weapon. If the model points the wrong way, press F8 (turn) or F9 (roll).')


def list_models():
    for wid, name in weapon_ids():
        f = MODELS_DIR / wid / 'model.json'
        if f.exists():
            m = json.loads(f.read_text())
            print(f"{wid:10s} {name:20s} -> {m.get('name')} by {m.get('author')} ({m.get('license')})")
        elif (MODELS_DIR / wid).is_dir():
            print(f'{wid:10s} {name:20s} -> (your own model)')
        else:
            print(f'{wid:10s} {name:20s}    block model')


def remove(weapon):
    target = MODELS_DIR / weapon
    if not target.is_dir():
        sys.exit(f'{weapon} has no downloaded model.')
    shutil.rmtree(target)
    write_credits()
    print(f'Removed. {weapon} uses its block model again.')


def write_credits():
    lines = ['# 3D model credits', '', 'Models downloaded from Sketchfab for BLOCKHOLD.', '']
    for f in sorted(MODELS_DIR.glob('*/model.json')):
        m = json.loads(f.read_text())
        lines.append(f"- **{f.parent.name}**: [{m.get('name')}]({m.get('source_url')}) by "
                     f"[{m.get('author')}]({m.get('author_url')}), licence: [{m.get('license')}]({m.get('license_url')})")
    MODELS_DIR.mkdir(exist_ok=True)
    (MODELS_DIR / 'CREDITS.md').write_text('\n'.join(lines) + '\n')


def interactive(licenses):
    print('BLOCKHOLD gun model downloader (models from sketchfab.com)\n')
    words = input('Search for (leave empty for the most-liked guns): ').strip()
    cursor = None
    while True:
        results, cursor = search(words, licenses, cursor=cursor)
        print_results(results)
        pick = input('\nNumber to download, M for more results, Q to quit: ').strip().lower()
        if pick == 'q':
            return
        if pick == 'm' and cursor:
            continue
        if pick.isdigit() and 1 <= int(pick) <= len(results):
            break
        cursor = None
    model = results[int(pick) - 1]
    print('\nWhich weapon should use it?')
    ids = weapon_ids()
    for i, (wid, name) in enumerate(ids, 1):
        print(f'{i:3d}. {name} ({wid})')
    w = input('Number: ').strip()
    if not (w.isdigit() and 1 <= int(w) <= len(ids)):
        sys.exit('Cancelled.')
    get(model['uid'], ids[int(w) - 1][0], get_token())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', nargs='?', choices=['search', 'get', 'list', 'remove', 'credits'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--license', default=','.join(SAFE_LICENSES),
                    help="comma list of licences to show (cc0,by,by-sa,by-nc,...) or 'any'")
    ap.add_argument('--token', help='Sketchfab API token (otherwise asked for)')
    a = ap.parse_args()
    licenses = 'any' if a.license == 'any' else tuple(a.license.split(','))
    try:
        if a.command is None:
            interactive(licenses)
        elif a.command == 'search':
            print_results(search(' '.join(a.args), licenses)[0])
        elif a.command == 'get':
            if len(a.args) != 2:
                sys.exit('Usage: get <model uid or link> <weapon id>')
            get(parse_uid(a.args[0]), a.args[1], a.token or get_token())
        elif a.command == 'list':
            list_models()
        elif a.command == 'remove':
            remove(a.args[0])
        elif a.command == 'credits':
            write_credits()
            print(f"Wrote {MODELS_DIR / 'CREDITS.md'}")
    except urllib.error.URLError as e:
        sys.exit(f'Could not reach Sketchfab: {e}')


if __name__ == '__main__':
    main()
