"""Reads DEVLOG.md for the DEVLOG tab on the main menu.

Each entry starts with a line `## version | date | title`; everything under it until the
next entry is its text. Blank lines split paragraphs and lines starting with "- " are bullets.
"""
from .paths import DEVLOG_FILE


def load():
    """[dict(version, date, title, blocks=[('p' | 'li', text)])], newest first."""
    try:
        lines = DEVLOG_FILE.read_text(encoding='utf-8').splitlines()
    except OSError:
        return []
    entries, cur, para = [], None, []

    def flush():
        if cur is not None and para:
            cur['blocks'].append(('p', ' '.join(para)))
        para.clear()
    for line in lines:
        if line.startswith('## '):
            flush()
            parts = [p.strip() for p in line[3:].split('|')]
            parts += [''] * (3 - len(parts))
            cur = dict(version=parts[0], date=parts[1], title=parts[2], blocks=[])
            entries.append(cur)
        elif cur is None:
            continue
        elif line.startswith('- '):
            flush()
            cur['blocks'].append(('li', line[2:].strip()))
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
    flush()
    return entries


def wrap(text, width):
    """Split text into lines of at most `width` characters (for paging long entries)."""
    out, line = [], ''
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            out.append(line)
            line = word
        else:
            line = f'{line} {word}' if line else word
    if line:
        out.append(line)
    return out
