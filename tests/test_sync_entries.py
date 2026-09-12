"""Exercise real generation: paths must resolve, drift must be detected read-only."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'sync_entries.py'

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'references').mkdir()
        (self.root / 'SKILL.md').write_text('---\nname: zs-teach-skill\ndescription: 示例\n---\n\n# 教学\n\n[模式](references/mode.md)\n', encoding='utf-8')
        (self.root / 'references/mode.md').write_text('# 模式\n原始规则\n', encoding='utf-8')

    def run_sync(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), *args], capture_output=True, text=True)

    def test_generation_keeps_links_resolvable_and_copies_reference(self):
        # Fails if the generator omits the native reference or rebases a link wrong.
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for entry, target in [('.opencode/skills/zs-teach-skill/SKILL.md', 'references/mode.md'), ('.cursor/rules/zs-teach-skill.mdc', '../../references/mode.md'), ('.github/copilot-instructions.md', '../references/mode.md')]:
            path = self.root / entry
            self.assertIn(f']({target})', path.read_text())
            self.assertEqual((path.parent / target).read_text(), '# 模式\n原始规则\n')
        self.assertEqual(self.run_sync('--check').returncode, 0)

    def test_check_detects_source_change_without_writing(self):
        self.assertEqual(self.run_sync().returncode, 0)
        native = self.root / '.opencode/skills/zs-teach-skill/references/mode.md'
        before = native.read_bytes()
        (self.root / 'references/mode.md').write_text('# 模式\n更新规则\n', encoding='utf-8')
        self.assertEqual(self.run_sync('--check').returncode, 1)
        self.assertEqual(native.read_bytes(), before)
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual(native.read_text(), '# 模式\n更新规则\n')

    def test_check_detects_manual_entry_edit_and_sync_is_idempotent(self):
        self.assertEqual(self.run_sync().returncode, 0)
        entry = self.root / '.github/copilot-instructions.md'
        expected = entry.read_bytes()
        entry.write_text('手改规则\n', encoding='utf-8')
        self.assertEqual(self.run_sync('--check').returncode, 1)
        self.assertEqual(entry.read_text(), '手改规则\n')
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual(entry.read_bytes(), expected)
        stamp = entry.stat().st_mtime_ns
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual(entry.stat().st_mtime_ns, stamp)

    def test_removed_source_reference_is_detected_then_pruned(self):
        # A removed source must not survive as an alternative rule in the bundle.
        self.assertEqual(self.run_sync().returncode, 0)
        native = self.root / '.opencode/skills/zs-teach-skill/references/mode.md'
        (self.root / 'references/mode.md').unlink()
        sentinel = self.root / '.opencode/skills/zs-teach-skill/notes.txt'
        sentinel.write_text('keep', encoding='utf-8')
        self.assertEqual(self.run_sync('--check').returncode, 1)
        self.assertTrue(native.exists())
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertFalse(native.exists())
        self.assertEqual(sentinel.read_text(), 'keep')

if __name__ == '__main__':
    unittest.main()
