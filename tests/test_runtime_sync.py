from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC = (
    REPO_ROOT
    / "skills/setup-sci-research-runtime/scripts/sync_runtime.py"
)


class RuntimeSyncTests(unittest.TestCase):
    def run_sync(self, project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SYNC), "--project-root", str(project_root), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            result = self.run_sync(project_root, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY-RUN", result.stdout)
            self.assertFalse((project_root / ".codex").exists())

    def test_install_check_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            install = self.run_sync(project_root)
            self.assertEqual(install.returncode, 0, install.stderr)
            manifest_path = project_root / ".codex/sci-research-runtime.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["managed_files"]), 9)

            check = self.run_sync(project_root, "--check")
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn("RUNTIME_OK", check.stdout)

            uninstall = self.run_sync(project_root, "--uninstall")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertFalse(manifest_path.exists())
            for relative in manifest["managed_files"]:
                self.assertFalse((project_root / relative).exists())

    def test_repeated_install_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            first = self.run_sync(project_root)
            self.assertEqual(first.returncode, 0, first.stderr)
            manifest_path = project_root / ".codex/sci-research-runtime.json"
            before = manifest_path.read_bytes()

            second = self.run_sync(project_root)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("ALREADY_INSTALLED", second.stdout)
            self.assertEqual(manifest_path.read_bytes(), before)
            backup_root = project_root / ".codex/sci-research-backups"
            self.assertFalse(backup_root.exists())

    def test_install_updates_stale_manifest_version_with_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            first = self.run_sync(project_root)
            self.assertEqual(first.returncode, 0, first.stderr)
            manifest_path = project_root / ".codex/sci-research-runtime.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plugin_version"] = "0.0.0+codex.stale"
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )

            update = self.run_sync(project_root)
            self.assertEqual(update.returncode, 0, update.stderr)
            self.assertIn("BACKUP:", update.stdout)
            updated = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertNotEqual(updated["plugin_version"], "0.0.0+codex.stale")
            backups = list(
                (project_root / ".codex/sci-research-backups").glob(
                    "*/.codex/sci-research-runtime.json"
                )
            )
            self.assertEqual(len(backups), 1)

    def test_update_removes_obsolete_managed_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            first = self.run_sync(project_root)
            self.assertEqual(first.returncode, 0, first.stderr)

            manifest_path = project_root / ".codex/sci-research-runtime.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            obsolete_relative = (
                ".codex/agents/sci-research-reputation-resolver.toml"
            )
            obsolete_path = project_root / obsolete_relative
            obsolete_content = b"name = 'sci-research-reputation-resolver'\n"
            obsolete_path.write_bytes(obsolete_content)
            manifest["managed_files"][obsolete_relative] = hashlib.sha256(
                obsolete_content
            ).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )

            update = self.run_sync(project_root)
            self.assertEqual(update.returncode, 0, update.stderr)
            self.assertIn("REMOVE:", update.stdout)
            self.assertIn(obsolete_path.name, update.stdout)
            self.assertFalse(obsolete_path.exists())
            updated = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(len(updated["managed_files"]), 9)
            self.assertNotIn(obsolete_relative, updated["managed_files"])

    def test_refuses_to_overwrite_unmanaged_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            conflict = (
                project_root
                / ".codex/agents/sci-research-daily-news-scanner.toml"
            )
            conflict.parent.mkdir(parents=True)
            conflict.write_text("name = 'local'\n", encoding="utf-8")
            result = self.run_sync(project_root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Unmanaged agent file conflicts", result.stderr)

    def test_refuses_to_remove_modified_managed_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            install = self.run_sync(project_root)
            self.assertEqual(install.returncode, 0, install.stderr)
            manifest = json.loads(
                (project_root / ".codex/sci-research-runtime.json").read_text(
                    encoding="utf-8"
                )
            )
            relative = next(iter(manifest["managed_files"]))
            (project_root / relative).write_text("# locally modified\n", encoding="utf-8")
            result = self.run_sync(project_root, "--uninstall")
            self.assertEqual(result.returncode, 2)
            self.assertIn("modified locally", result.stderr)


if __name__ == "__main__":
    unittest.main()
