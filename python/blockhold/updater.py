"""Auto-updater: checks GitHub for a newer version of the game and installs it.

How it decides there's an update: it compares python/VERSION in your copy with
python/VERSION on GitHub. So to publish an update for everyone:
    1. change the number in python/VERSION (for example 1.1.0 -> 1.2.0)
    2. write what changed at the top of python/CHANGELOG.md
    3. push to GitHub

How it installs:
  * If the game folder is a git clone, it runs `git pull`.
  * Otherwise (downloaded as a ZIP) it downloads the newest ZIP from GitHub and
    copies the files over. Any file it replaces that you had changed is backed
    up first in python/_backup/<old version>/, so your own edits are never lost.
"""
import io
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
import zipfile
from pathlib import Path

REPO = 'masterxxstabs/killcraft-remake'   # GitHub owner/name
BRANCH = 'HEAD'                           # HEAD = the repository's default branch
SUBDIR = 'python'                         # the game lives in this folder of the repo

GAME_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = GAME_DIR.parent
VERSION_FILE = GAME_DIR / 'VERSION'
CHANGELOG_FILE = GAME_DIR / 'CHANGELOG.md'
BACKUP_DIR = GAME_DIR / '_backup'
SKIP_PARTS = {'__pycache__', '_generated_sounds', '_backup', '.git'}


def parse_version(text):
    nums = [int(n) for n in re.findall(r'\d+', text or '')[:3]]
    return tuple(nums + [0] * (3 - len(nums)))


def local_version():
    try:
        return VERSION_FILE.read_text().strip()
    except OSError:
        return '0.0.0'


def _fetch(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent': 'blockhold-updater', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _raw(path):
    return _fetch(f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}').decode('utf-8', 'replace')


def latest_notes(changelog, version):
    """The bullet points under '## <version>' in CHANGELOG.md."""
    lines, on = [], False
    for line in changelog.splitlines():
        if line.startswith('## '):
            if on:
                break
            on = version in line
        elif on and line.strip().startswith(('-', '*')):
            lines.append(line.strip().lstrip('-* ').strip())
    return lines


def is_git_checkout():
    return (REPO_DIR / '.git').exists() and shutil.which('git') is not None


def _git(*args, timeout=60):
    return subprocess.run(['git', '-C', str(REPO_DIR), *args], capture_output=True, text=True, timeout=timeout)


class Updater:
    """status: idle, checking, up_to_date, available, offline, installing, installed, failed"""

    def __init__(self):
        self.status = 'idle'
        self.local = local_version()
        self.remote = None
        self.notes = []
        self.message = ''
        self.mode = 'git' if is_git_checkout() else 'zip'

    # ── checking ─────────────────────────────────────────────────────────────
    def check_async(self):
        threading.Thread(target=self.check, daemon=True).start()

    def check(self):
        self.status = 'checking'
        try:
            if self.mode == 'git':
                fetched = _git('fetch', '--quiet')
                if fetched.returncode != 0:
                    raise OSError(fetched.stderr.strip())
                shown = _git('show', f'@{{u}}:{SUBDIR}/VERSION')
                if shown.returncode != 0:
                    raise OSError(shown.stderr.strip())
                remote = shown.stdout.strip()
                changelog = _git('show', f'@{{u}}:{SUBDIR}/CHANGELOG.md').stdout
            else:
                remote = _raw(f'{SUBDIR}/VERSION').strip()
                try:
                    changelog = _raw(f'{SUBDIR}/CHANGELOG.md')
                except Exception:
                    changelog = ''
            self.remote = remote
            if parse_version(remote) > parse_version(self.local):
                self.notes = latest_notes(changelog, remote)
                self.status = 'available'
            else:
                self.status = 'up_to_date'
        except Exception as e:
            self.message = str(e)[:200]
            self.status = 'offline'
        return self.status

    # ── installing ───────────────────────────────────────────────────────────
    def install_async(self, on_done=None):
        def run():
            self.install()
            if on_done:
                on_done(self)
        threading.Thread(target=run, daemon=True).start()

    def install(self):
        self.status = 'installing'
        try:
            if self.mode == 'git':
                result = _git('pull', '--ff-only', timeout=180)
                if result.returncode != 0:
                    self.status = 'failed'
                    self.message = ('Could not update with git (you probably changed some files). '
                                    'Commit or stash your changes, then try again.\n' + result.stderr.strip()[:300])
                    return self.status
            else:
                self._install_zip()
            self.local = local_version()
            self.status = 'installed'
        except Exception as e:
            self.status = 'failed'
            self.message = f'Update failed: {e}'[:300]
        return self.status

    def _install_zip(self):
        data = _fetch(f'https://github.com/{REPO}/archive/{BRANCH}.zip', timeout=120)
        backup = BACKUP_DIR / self.local
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            prefix = None
            for name in z.namelist():
                parts = Path(name).parts
                if len(parts) >= 2 and parts[1] == SUBDIR:
                    prefix = parts[0] + '/' + SUBDIR + '/'
                    break
            if prefix is None:
                raise RuntimeError(f'the download has no {SUBDIR}/ folder')
            for info in z.infolist():
                if info.is_dir() or not info.filename.startswith(prefix):
                    continue
                rel = Path(info.filename[len(prefix):])
                if not rel.parts or rel.is_absolute() or '..' in rel.parts or SKIP_PARTS & set(rel.parts):
                    continue
                new = z.read(info)
                target = GAME_DIR / rel
                if target.exists():
                    old = target.read_bytes()
                    if old == new:
                        continue
                    keep = backup / rel                 # keep the old file, just in case
                    keep.parent.mkdir(parents=True, exist_ok=True)
                    keep.write_bytes(old)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(new)


def restart():
    """Start a fresh copy of the game and let the caller quit this one."""
    subprocess.Popen([sys.executable] + sys.argv, cwd=str(GAME_DIR))


def run_cli():
    """python main.py --update"""
    u = Updater()
    print(f'BLOCKHOLD {u.local}  ({u.mode} install)\nChecking {REPO} for updates...')
    status = u.check()
    if status == 'offline':
        print('Could not reach GitHub:', u.message)
    elif status == 'up_to_date':
        print(f'You have the newest version ({u.local}).')
    else:
        print(f'Version {u.remote} is available:')
        for n in u.notes:
            print('  -', n)
        print('Installing...')
        if u.install() == 'installed':
            print(f'Updated to {u.local}. Start the game again!')
        else:
            print(u.message)
