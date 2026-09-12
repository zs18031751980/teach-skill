#!/usr/bin/env python3
"""Preview installed skill changes; --apply backs up and writes, --check is read-only."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import unquote

# Keep preview/check read-only even when importing the shared entry generator.
sys.dont_write_bytecode = True
from sync_entries import outputs

MANIFEST = Path('.teach-skill-sync.json')


def regular_path(path):
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise ValueError(f'Symlink is not supported: {ancestor}')
        if ancestor != path and ancestor.exists() and not ancestor.is_dir():
            raise ValueError(f'Expected a directory: {ancestor}')
    if path.exists() and not path.is_file():
        raise ValueError(f'Expected a regular file: {path}')


def digest(content):
    return hashlib.sha256(content).hexdigest()


def bundles(root):
    paths = [root / 'SKILL.md', *sorted((root / 'references').rglob('*.md'))]
    native = {}
    for path in paths:
        regular_path(path)
        native[path.relative_to(root)] = path.read_bytes()
    # Validate shipped Markdown links against the actual bundle, not arbitrary repo files.
    for relative, content in native.items():
        for link in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', content.decode('utf-8')):
            if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', link) or link.startswith(('#', '//')):
                continue
            target = (root / relative.parent / unquote(link.split('#', 1)[0])).resolve()
            if not target.is_relative_to(root) or target.relative_to(root) not in native:
                raise ValueError(f'Broken or unshipped link in {relative}: {link}')
    prefix = Path('.opencode/skills/zs-teach-skill')
    opencode = {path.relative_to(prefix): text.encode('utf-8')
                for path, text in outputs(root).items() if path.is_relative_to(prefix)}
    return {'codex': native, 'opencode': opencode}


def plan(destination, expected):
    regular_path(destination / MANIFEST)
    manifest_content = (destination / MANIFEST).read_bytes() if (destination / MANIFEST).exists() else None
    old_files = {}
    if manifest_content is not None:
        old = json.loads(manifest_content)
        if not isinstance(old, dict) or old.get('version') != 1 or not isinstance(old.get('files'), dict):
            raise ValueError(f'Invalid manifest: {destination / MANIFEST}')
        old_files = old['files']
        for name, checksum in old_files.items():
            path = Path(name)
            if (path.as_posix() != name or path.is_absolute() or '..' in path.parts or
                    not (path == Path('SKILL.md') or
                         (len(path.parts) > 1 and path.parts[0] == 'references' and path.suffix == '.md')) or
                    not isinstance(checksum, str) or not re.fullmatch('[0-9a-f]{64}', checksum)):
                raise ValueError(f'Invalid managed path or checksum: {name}')
    files = dict(expected)
    files[MANIFEST] = (json.dumps({'version': 1, 'files': {str(p): digest(c) for p, c in expected.items()}},
                                ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    changes = {}
    for relative in files.keys() | {Path(name) for name in old_files}:
        path = destination / relative
        regular_path(path)
        before = path.read_bytes() if path.exists() else None
        after = files.get(relative)
        if after is None and before is not None and digest(before) != old_files[str(relative)]:
            raise ValueError(f'Modified obsolete file needs manual resolution: {path}')
        if before != after:
            changes[relative] = (before, after)
    return files, changes


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.teach-sync-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
        os.chmod(temporary, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply(plans):
    backup = Path(tempfile.mkdtemp(prefix='teach-runtime-backup-'))
    print(f'Backup: {backup}', flush=True)
    restore = {}
    # Finish all backups before changing any installed file.
    for label, (destination, _, changes) in plans.items():
        restore[label] = {'destination': str(destination), 'created': [], 'saved': []}
        for relative, (before, _) in changes.items():
            path = destination / relative
            regular_path(path)
            actual = path.read_bytes() if path.exists() else None
            if actual != before:
                raise ValueError(f'File changed since preview; rerun: {path}')
            if before is None:
                restore[label]['created'].append(str(relative))
            else:
                saved = backup / label / relative
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, saved)
                if saved.read_bytes() != before:
                    raise ValueError(f'Backup mismatch: {path}')
                restore[label]['saved'].append(str(relative))
    (backup / 'restore.json').write_text(json.dumps(restore, ensure_ascii=False, indent=2) + '\n')
    for destination, expected, changes in plans.values():
        for relative, (_, after) in sorted(changes.items()):
            if after is None:
                (destination / relative).unlink()
            else:
                atomic_write(destination / relative, after)
        for relative, content in expected.items():
            if (destination / relative).read_bytes() != content:
                raise ValueError(f'Verification mismatch: {destination / relative}')
        for relative, (_, after) in changes.items():
            if after is None and (destination / relative).exists():
                raise ValueError(f'Obsolete file remains: {destination / relative}')
    print('Installed contents verified.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--target', choices=('codex', 'opencode', 'both'), required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        root = Path(os.path.abspath(args.root))
        sources = bundles(root)
        destinations = {
            'codex': Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex') / 'skills/zs-teach-skill',
            'opencode': Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'opencode/skills/zs-teach-skill',
        }
        labels = tuple(destinations) if args.target == 'both' else (args.target,)
        plans = {}
        for label in labels:
            destination = Path(os.path.abspath(destinations[label]))
            if destination.is_relative_to(root) or root.is_relative_to(destination):
                raise ValueError(f'Source and runtime must not overlap: {destination}')
            for other, _, _ in plans.values():
                if destination.is_relative_to(other) or other.is_relative_to(destination):
                    raise ValueError('Runtime destinations must not overlap')
            expected, changes = plan(destination, sources[label])
            plans[label] = destination, expected, changes
        for label, (destination, _, changes) in plans.items():
            print(f'{label}: {destination} ({len(changes)} changed files)')
            if not args.check:
                for relative, (before, after) in sorted(changes.items()):
                    if relative == MANIFEST:
                        print(f'Update managed-file record: {relative}')
                        continue
                    print(''.join(difflib.unified_diff(
                        (before or b'').decode('utf-8', errors='replace').splitlines(keepends=True),
                        (after or b'').decode('utf-8', errors='replace').splitlines(keepends=True),
                        fromfile=str(destination / relative), tofile=f'source/{relative}')), end='\n')
        changed = any(changes for _, _, changes in plans.values())
        if args.apply and changed:
            apply(plans)
        elif not args.check and not args.apply:
            print('Preview only. Use --apply to install these changes.')
        return int(args.check and changed)
    except (OSError, ValueError, StopIteration) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
