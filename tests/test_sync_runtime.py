"""Exercise installed-file synchronization on real isolated directories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/sync_runtime.py'


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        (self.root / 'references').mkdir(parents=True)
        self.source = '---\nname: zs-teach-skill\ndescription: 示例\n---\n\n[模式](references/mode.md)\n'
        (self.root / 'SKILL.md').write_text(self.source)
        (self.root / 'references/mode.md').write_text('# 规则\n')
        self.codex = self.base / 'codex-home/skills/zs-teach-skill'
        self.opencode = self.base / 'config/opencode/skills/zs-teach-skill'
        self.env = dict(os.environ, CODEX_HOME=str(self.base / 'codex-home'),
                        XDG_CONFIG_HOME=str(self.base / 'config'), TMPDIR=str(self.base))

    def run_sync(self, *args, target='both'):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
                               '--target', target, *args], env=self.env,
                              capture_output=True, text=True)

    def snapshot(self):
        return {str(p.relative_to(self.base)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.base.rglob('*') if p.is_file()}

    def apply(self, **kwargs):
        result = self.run_sync('--apply', **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_preview_and_check_never_write(self):
        before = self.snapshot()
        preview = self.run_sync()
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn('+[模式](references/mode.md)', preview.stdout)
        self.assertEqual(self.run_sync('--check').returncode, 1)
        self.assertEqual(self.snapshot(), before)

    def test_apply_copies_complete_selected_bundle_and_ignores_generated_drift(self):
        # Runtime source must be canonical even when a checked-in generated copy is old.
        stale = self.root / '.opencode/skills/zs-teach-skill'
        stale.mkdir(parents=True)
        (stale / 'SKILL.md').write_text('stale')
        self.apply(target='opencode')
        self.assertFalse(self.codex.exists())
        self.assertIn('[模式](references/mode.md)', (self.opencode / 'SKILL.md').read_text())
        self.assertEqual((self.opencode / 'references/mode.md').read_text(), '# 规则\n')
        self.apply(target='codex')
        self.assertEqual((self.codex / 'SKILL.md').read_text(), self.source)
        self.assertEqual(self.run_sync('--check').returncode, 0)

    def test_update_backs_up_originals_preserves_unknown_files_and_is_idempotent(self):
        self.apply()
        (self.codex / 'agents').mkdir()
        (self.codex / 'agents/openai.yaml').write_text('custom metadata')
        (self.codex / 'references/local.md').write_text('local notes')
        old = (self.codex / 'references/mode.md').read_bytes()
        (self.root / 'references/mode.md').write_text('# 新规则\n')
        result = self.apply()
        backups = list(self.base.glob('teach-runtime-backup-*/codex/references/mode.md'))
        self.assertTrue(any(p.read_bytes() == old for p in backups), result.stdout)
        self.assertEqual((self.codex / 'references/mode.md').read_text(), '# 新规则\n')
        self.assertEqual((self.codex / 'agents/openai.yaml').read_text(), 'custom metadata')
        self.assertEqual((self.codex / 'references/local.md').read_text(), 'local notes')
        before = self.snapshot()
        self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_removed_managed_reference_is_backed_up_and_pruned(self):
        self.apply()
        (self.root / 'SKILL.md').write_text(self.source.replace('[模式](references/mode.md)', '教学'))
        (self.root / 'references/mode.md').unlink()
        before = self.snapshot()
        self.assertEqual(self.run_sync('--check').returncode, 1)
        self.assertEqual(self.snapshot(), before)
        self.apply()
        self.assertFalse((self.codex / 'references/mode.md').exists())
        self.assertTrue(any(p.read_text() == '# 规则\n' for p in
                            self.base.glob('teach-runtime-backup-*/codex/references/mode.md')))

    def test_modified_obsolete_reference_aborts_all_targets(self):
        self.apply()
        (self.opencode / 'references/mode.md').write_text('user changes')
        (self.root / 'SKILL.md').write_text(self.source.replace('[模式](references/mode.md)', '教学'))
        (self.root / 'references/mode.md').unlink()
        before = self.snapshot()
        result = self.run_sync('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('modified obsolete', result.stderr.lower())
        self.assertEqual(self.snapshot(), before)

    def test_invalid_source_link_cannot_partially_update_runtime(self):
        self.apply()
        (self.root / 'references/mode.md').write_text('[missing](absent.md)')
        before = self.snapshot()
        result = self.run_sync('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('link', result.stderr.lower())
        self.assertEqual(self.snapshot(), before)

    def test_target_symlink_cannot_write_outside_destination(self):
        self.codex.parent.mkdir(parents=True)
        outside = self.base / 'outside'
        outside.mkdir()
        self.codex.symlink_to(outside, target_is_directory=True)
        result = self.run_sync('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('symlink', result.stderr.lower())
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse(self.opencode.exists())

    def test_manifest_path_traversal_aborts_without_touching_other_files(self):
        self.apply()
        sentinel = self.codex.parent / 'sentinel.md'
        sentinel.write_text('keep')
        (self.codex / '.teach-skill-sync.json').write_text(json.dumps(
            {'version': 1, 'files': {'../sentinel.md': 'irrelevant'}}))
        before = self.snapshot()
        result = self.run_sync('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_parent_file_conflict_is_found_before_any_runtime_write(self):
        self.opencode.mkdir(parents=True)
        (self.opencode / 'references').write_text('not a directory')
        before = self.snapshot()
        result = self.run_sync('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
