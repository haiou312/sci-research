#!/usr/bin/env python3
"""Install Sci-Research custom agents into a project-scoped Codex runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib
from datetime import UTC, datetime
from typing import Any


SCHEMA_VERSION = 1
PLUGIN_NAME = "sci-research"
MANIFEST_RELATIVE = Path(".codex/sci-research-runtime.json")
BACKUP_ROOT_RELATIVE = Path(".codex/sci-research-backups")
CONFIG_RELATIVE = Path(".codex/config.toml")
CONFIG_TEMPLATE_RELATIVE = Path(
    "skills/setup-sci-research-runtime/runtime/config.toml"
)
MIN_AGENT_THREADS = 10


class RuntimeErrorWithContext(RuntimeError):
    """An expected runtime setup failure with a user-facing message."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeErrorWithContext(f"Cannot read runtime manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeErrorWithContext(f"Runtime manifest is not a JSON object: {path}")
    return data


def load_plugin_version(plugin_root: Path) -> str:
    manifest_path = plugin_root / ".codex-plugin/plugin.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        version = data["version"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeErrorWithContext(
            f"Cannot read plugin version from {manifest_path}: {exc}"
        ) from exc
    if not isinstance(version, str) or not version:
        raise RuntimeErrorWithContext(f"Invalid plugin version in {manifest_path}")
    return version


def load_source_agents(plugin_root: Path) -> dict[str, dict[str, Any]]:
    agents_dir = plugin_root / ".codex/agents"
    result: dict[str, dict[str, Any]] = {}
    names: set[str] = set()
    for path in sorted(agents_dir.glob("*.toml")):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise RuntimeErrorWithContext(f"Invalid agent TOML {path}: {exc}") from exc
        missing = [
            key
            for key in ("name", "description", "developer_instructions")
            if not isinstance(data.get(key), str) or not data[key].strip()
        ]
        if missing:
            raise RuntimeErrorWithContext(
                f"Agent {path} is missing required string fields: {', '.join(missing)}"
            )
        name = data["name"]
        if not name.startswith(f"{PLUGIN_NAME}-"):
            raise RuntimeErrorWithContext(
                f"Agent name must use the {PLUGIN_NAME}- namespace: {name} ({path})"
            )
        if path.stem != name:
            raise RuntimeErrorWithContext(
                f"Agent filename must match its name: {path.name} != {name}.toml"
            )
        if name in names:
            raise RuntimeErrorWithContext(f"Duplicate agent name: {name}")
        names.add(name)
        result[path.name] = {
            "path": path,
            "sha256": sha256(path),
            "name": name,
        }
    if not result:
        raise RuntimeErrorWithContext(f"No agent TOML files found under {agents_dir}")
    return result


def load_agent_thread_limit(path: Path) -> int:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeErrorWithContext(
            f"Invalid Codex runtime config {path}: {exc}"
        ) from exc
    agents = data.get("agents")
    max_threads = agents.get("max_threads") if isinstance(agents, dict) else None
    if (
        isinstance(max_threads, bool)
        or not isinstance(max_threads, int)
        or max_threads < MIN_AGENT_THREADS
    ):
        raise RuntimeErrorWithContext(
            f"Codex runtime config must set agents.max_threads >= "
            f"{MIN_AGENT_THREADS}: {path}\n"
            "Add or update:\n"
            "[agents]\n"
            f"max_threads = {MIN_AGENT_THREADS}\n"
            "max_depth = 1"
        )
    return max_threads


def load_config_template(plugin_root: Path) -> Path:
    template = plugin_root / CONFIG_TEMPLATE_RELATIVE
    load_agent_thread_limit(template)
    data = tomllib.loads(template.read_text(encoding="utf-8"))
    if data["agents"].get("max_depth") != 1:
        raise RuntimeErrorWithContext(
            f"Runtime config template must set agents.max_depth = 1: {template}"
        )
    return template


def manifest_files(manifest: dict[str, Any]) -> dict[str, str]:
    files = manifest.get("managed_files")
    if not isinstance(files, dict):
        raise RuntimeErrorWithContext("Runtime manifest has no valid managed_files object")
    result: dict[str, str] = {}
    for relative, digest in files.items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise RuntimeErrorWithContext("Runtime manifest contains an invalid file entry")
        rel_path = Path(relative)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise RuntimeErrorWithContext(
                f"Runtime manifest contains unsafe managed path: {relative}"
            )
        result[relative] = digest
    return result


def manifest_runtime_config(
    manifest: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not manifest:
        return None
    value = manifest.get("runtime_config")
    if value is None:
        return None
    if not isinstance(value, dict):
        raise RuntimeErrorWithContext(
            "Runtime manifest contains an invalid runtime_config object"
        )
    path = value.get("path")
    minimum = value.get("minimum_max_threads")
    created = value.get("created_by_plugin")
    digest = value.get("sha256")
    if (
        path != str(CONFIG_RELATIVE)
        or isinstance(minimum, bool)
        or not isinstance(minimum, int)
        or minimum < 1
        or not isinstance(created, bool)
        or (created and (not isinstance(digest, str) or not digest))
    ):
        raise RuntimeErrorWithContext(
            "Runtime manifest contains invalid runtime_config metadata"
        )
    return value


def plan_runtime_config(
    project_root: Path,
    template: Path,
    old_manifest: dict[str, Any] | None,
) -> tuple[bool, dict[str, Any]]:
    destination = project_root / CONFIG_RELATIVE
    old_state = manifest_runtime_config(old_manifest)
    if not destination.exists():
        return True, {
            "path": str(CONFIG_RELATIVE),
            "minimum_max_threads": MIN_AGENT_THREADS,
            "created_by_plugin": True,
            "sha256": sha256(template),
        }

    load_agent_thread_limit(destination)
    created_by_plugin = False
    recorded_hash: str | None = None
    if old_state and old_state["created_by_plugin"]:
        recorded_hash = old_state["sha256"]
        created_by_plugin = sha256(destination) == recorded_hash

    state: dict[str, Any] = {
        "path": str(CONFIG_RELATIVE),
        "minimum_max_threads": MIN_AGENT_THREADS,
        "created_by_plugin": created_by_plugin,
    }
    if created_by_plugin and recorded_hash:
        state["sha256"] = recorded_hash
    return False, state


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as output, source.open("rb") as input_file:
            shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)


def atomic_write_json(destination: Path, data: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)


def build_manifest(
    project_root: Path,
    version: str,
    source_agents: dict[str, dict[str, Any]],
    runtime_config: dict[str, Any],
) -> dict[str, Any]:
    managed = {
        str(Path(".codex/agents") / filename): item["sha256"]
        for filename, item in source_agents.items()
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "plugin_name": PLUGIN_NAME,
        "plugin_version": version,
        "project_root": str(project_root),
        "installed_at": datetime.now(UTC).isoformat(),
        "managed_files": managed,
        "runtime_config": runtime_config,
    }


def validate_existing_manifest(manifest: dict[str, Any], manifest_path: Path) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeErrorWithContext(
            f"Unsupported runtime manifest schema in {manifest_path}: "
            f"{manifest.get('schema_version')!r}"
        )
    if manifest.get("plugin_name") != PLUGIN_NAME:
        raise RuntimeErrorWithContext(
            f"Runtime manifest belongs to another plugin: {manifest_path}"
        )
    manifest_files(manifest)
    manifest_runtime_config(manifest)


def plan_install(
    project_root: Path,
    source_agents: dict[str, dict[str, Any]],
    old_manifest: dict[str, Any] | None,
) -> tuple[list[tuple[Path, Path]], list[Path]]:
    old_files = manifest_files(old_manifest) if old_manifest else {}
    copies: list[tuple[Path, Path]] = []
    removals: list[Path] = []
    desired_relative: set[str] = set()

    for filename, item in source_agents.items():
        relative = str(Path(".codex/agents") / filename)
        desired_relative.add(relative)
        destination = project_root / relative
        source = item["path"]
        desired_hash = item["sha256"]
        if not destination.exists():
            copies.append((source, destination))
            continue
        actual_hash = sha256(destination)
        if relative not in old_files:
            if actual_hash != desired_hash:
                raise RuntimeErrorWithContext(
                    f"Unmanaged agent file conflicts with the plugin: {destination}"
                )
            continue
        if actual_hash != old_files[relative] and actual_hash != desired_hash:
            raise RuntimeErrorWithContext(
                f"Managed agent was modified locally; refusing to overwrite: {destination}"
            )
        if actual_hash != desired_hash:
            copies.append((source, destination))

    for relative, installed_hash in old_files.items():
        if relative in desired_relative:
            continue
        destination = project_root / relative
        if not destination.exists():
            continue
        if sha256(destination) != installed_hash:
            raise RuntimeErrorWithContext(
                f"Obsolete managed agent was modified locally; refusing to remove: {destination}"
            )
        removals.append(destination)
    return copies, removals


def make_backup(
    project_root: Path,
    manifest_path: Path,
    files: list[Path],
) -> Path | None:
    existing = [path for path in files if path.exists()]
    if manifest_path.exists():
        existing.append(manifest_path)
    if not existing:
        return None
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%fZ")
    backup_root = project_root / BACKUP_ROOT_RELATIVE / stamp
    for path in existing:
        relative = path.relative_to(project_root)
        target = backup_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return backup_root


def install(project_root: Path, plugin_root: Path, dry_run: bool) -> int:
    version = load_plugin_version(plugin_root)
    source_agents = load_source_agents(plugin_root)
    config_template = load_config_template(plugin_root)
    manifest_path = project_root / MANIFEST_RELATIVE
    old_manifest = load_json(manifest_path) if manifest_path.exists() else None
    if old_manifest:
        validate_existing_manifest(old_manifest, manifest_path)
    copies, removals = plan_install(project_root, source_agents, old_manifest)
    create_config, runtime_config = plan_runtime_config(
        project_root, config_template, old_manifest
    )
    config_path = project_root / CONFIG_RELATIVE

    action = "DRY-RUN" if dry_run else "INSTALL"
    print(f"{action}: project_root={project_root}")
    print(f"{action}: plugin_version={version}")
    for source, destination in copies:
        print(f"COPY: {source} -> {destination}")
    for destination in removals:
        print(f"REMOVE: {destination}")
    if not copies and not removals:
        print("AGENTS: already match the installed plugin payload")
    if create_config:
        print(
            f"CONFIG: create {config_path} with "
            f"agents.max_threads={MIN_AGENT_THREADS}"
        )
    else:
        print(
            f"CONFIG: verified {config_path} "
            f"agents.max_threads>={MIN_AGENT_THREADS}"
        )
    print(f"MANIFEST: {manifest_path}")
    if dry_run:
        return 0

    expected_files = {
        str(Path(".codex/agents") / filename): item["sha256"]
        for filename, item in source_agents.items()
    }
    if (
        old_manifest
        and not copies
        and not removals
        and old_manifest.get("plugin_version") == version
        and old_manifest.get("project_root") == str(project_root)
        and manifest_files(old_manifest) == expected_files
        and old_manifest.get("runtime_config") == runtime_config
    ):
        print(f"ALREADY_INSTALLED: agents={len(source_agents)}")
        print("RESTART_REQUIRED: start a new Codex task in this project")
        return 0

    backup = make_backup(
        project_root,
        manifest_path,
        [destination for _, destination in copies] + removals,
    )
    if create_config:
        atomic_copy(config_template, config_path)
    for source, destination in copies:
        atomic_copy(source, destination)
    for destination in removals:
        destination.unlink()
    atomic_write_json(
        manifest_path,
        build_manifest(project_root, version, source_agents, runtime_config),
    )
    print(f"INSTALLED: agents={len(source_agents)}")
    if backup:
        print(f"BACKUP: {backup}")
    print("RESTART_REQUIRED: start a new Codex task in this project")
    return 0


def check(project_root: Path, plugin_root: Path) -> int:
    version = load_plugin_version(plugin_root)
    source_agents = load_source_agents(plugin_root)
    load_config_template(plugin_root)
    manifest_path = project_root / MANIFEST_RELATIVE
    if not manifest_path.exists():
        raise RuntimeErrorWithContext(
            f"Runtime is not installed for this project: {manifest_path}"
        )
    manifest = load_json(manifest_path)
    validate_existing_manifest(manifest, manifest_path)
    problems: list[str] = []
    thread_limit: int | None = None
    if manifest.get("project_root") != str(project_root):
        problems.append(
            f"project root mismatch: installed={manifest.get('project_root')} "
            f"current={project_root}"
        )
    if manifest.get("plugin_version") != version:
        problems.append(
            f"version mismatch: installed={manifest.get('plugin_version')} plugin={version}"
        )
    expected_files = {
        str(Path(".codex/agents") / filename): item["sha256"]
        for filename, item in source_agents.items()
    }
    recorded_files = manifest_files(manifest)
    if recorded_files != expected_files:
        problems.append("managed file list or source hashes differ from the plugin payload")
    for relative, expected_hash in expected_files.items():
        destination = project_root / relative
        if not destination.is_file():
            problems.append(f"missing agent: {destination}")
        elif sha256(destination) != expected_hash:
            problems.append(f"agent hash mismatch: {destination}")
    config_path = project_root / CONFIG_RELATIVE
    try:
        thread_limit = load_agent_thread_limit(config_path)
    except RuntimeErrorWithContext as exc:
        problems.append(str(exc))
    runtime_config = manifest_runtime_config(manifest)
    if runtime_config is None:
        problems.append(
            "runtime manifest does not record the project-scoped Codex config; "
            "rerun runtime setup"
        )
    elif runtime_config["minimum_max_threads"] != MIN_AGENT_THREADS:
        problems.append(
            "runtime manifest records a different minimum thread limit; "
            "rerun runtime setup"
        )
    if problems:
        raise RuntimeErrorWithContext("Runtime check failed:\n- " + "\n- ".join(problems))
    print(
        f"RUNTIME_OK: project_root={project_root} plugin_version={version} "
        f"agents={len(expected_files)} max_threads={thread_limit} "
        f"manifest={manifest_path}"
    )
    return 0


def uninstall(project_root: Path) -> int:
    manifest_path = project_root / MANIFEST_RELATIVE
    if not manifest_path.exists():
        print(f"NOT_INSTALLED: {manifest_path}")
        return 0
    manifest = load_json(manifest_path)
    validate_existing_manifest(manifest, manifest_path)
    managed = manifest_files(manifest)
    runtime_config = manifest_runtime_config(manifest)
    targets: list[Path] = []
    for relative, installed_hash in managed.items():
        destination = project_root / relative
        if not destination.exists():
            continue
        if sha256(destination) != installed_hash:
            raise RuntimeErrorWithContext(
                f"Managed agent was modified locally; refusing to remove: {destination}"
            )
        targets.append(destination)
    config_path = project_root / CONFIG_RELATIVE
    remove_config = False
    if runtime_config and runtime_config["created_by_plugin"] and config_path.exists():
        remove_config = sha256(config_path) == runtime_config["sha256"]
    backup_targets = targets + ([config_path] if remove_config else [])
    backup = make_backup(project_root, manifest_path, backup_targets)
    for destination in targets:
        destination.unlink()
        print(f"REMOVED: {destination}")
    if remove_config:
        config_path.unlink()
        print(f"REMOVED: {config_path}")
    elif config_path.exists():
        print(f"RETAINED_CONFIG: {config_path}")
    manifest_path.unlink()
    print(f"UNINSTALLED: project_root={project_root} agents={len(targets)}")
    if backup:
        print(f"BACKUP: {backup}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace that should receive .codex/agents (default: current directory)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview install/update")
    mode.add_argument("--check", action="store_true", help="Verify installed runtime")
    mode.add_argument("--uninstall", action="store_true", help="Remove managed runtime files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()
    if not project_root.is_dir():
        raise RuntimeErrorWithContext(f"Project root is not a directory: {project_root}")
    plugin_root = Path(__file__).resolve().parents[3]
    if args.check:
        return check(project_root, plugin_root)
    if args.uninstall:
        return uninstall(project_root)
    return install(project_root, plugin_root, args.dry_run)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeErrorWithContext as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
