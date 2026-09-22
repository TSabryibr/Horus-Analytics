from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class BackupInfo:
    path: Path
    modified: datetime
    size_bytes: int


def directory_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


def format_bytes(value: int) -> str:
    size = float(value)
    for suffix in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or suffix == "TB":
            return f"{size:.1f} {suffix}" if suffix != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


def find_backups(root: Path) -> list[BackupInfo]:
    backups: list[BackupInfo] = []
    for item in root.iterdir():
        if not item.is_dir() or not item.name.startswith("runtime_backup_"):
            continue
        try:
            stat = item.stat()
        except OSError:
            continue
        backups.append(
            BackupInfo(
                path=item,
                modified=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=directory_size(item),
            )
        )
    return sorted(backups, key=lambda info: info.modified, reverse=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List or delete old Horus runtime backup folders.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root to scan.")
    parser.add_argument("--keep", type=int, default=3, help="Always keep the newest N runtime backups.")
    parser.add_argument("--older-than-days", type=int, default=None, help="Only clean backups older than this many days.")
    parser.add_argument("--delete", action="store_true", help="Actually remove eligible backups. Default is dry-run.")
    return parser.parse_args()


def is_safe_backup_path(path: Path, root: Path) -> bool:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    return (
        resolved_path.parent == resolved_root
        and resolved_path.name.startswith("runtime_backup_")
        and resolved_path.is_dir()
    )


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    backups = find_backups(root)
    cutoff = None
    if args.older_than_days is not None:
        cutoff = datetime.now() - timedelta(days=max(0, args.older_than_days))

    kept = backups[: max(0, args.keep)]
    eligible = backups[max(0, args.keep) :]
    if cutoff is not None:
        eligible = [info for info in eligible if info.modified < cutoff]

    kept_paths = {info.path.resolve() for info in kept}
    eligible_paths = {info.path.resolve() for info in eligible}
    total_eligible_size = sum(info.size_bytes for info in eligible)

    print(f"Runtime backups found: {len(backups)}")
    print(f"Newest backups kept: {len(kept)}")
    print(f"Eligible for cleanup: {len(eligible)} ({format_bytes(total_eligible_size)})")
    print()

    for info in backups:
        resolved = info.path.resolve()
        if resolved in eligible_paths:
            action = "DELETE" if args.delete else "DRY-RUN"
        elif resolved in kept_paths:
            action = "KEEP"
        else:
            action = "SKIP"
        print(f"{action:7} {info.modified:%Y-%m-%d %H:%M:%S} {format_bytes(info.size_bytes):>10} {info.path.name}")

    if not args.delete:
        print("\nNo files were deleted. Re-run with --delete to remove eligible backups.")
        return 0

    for info in eligible:
        if not is_safe_backup_path(info.path, root):
            print(f"Refusing unsafe path: {info.path}", file=sys.stderr)
            return 2
        shutil.rmtree(info.path)

    print(f"\nDeleted {len(eligible)} runtime backup folder(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
