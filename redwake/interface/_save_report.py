"""Save redwake report artifacts to a user-specified path after scan completion.

Used by `--save-report PATH` CLI flag to copy key output files when the TUI
mouse-copy workaround is not practical.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path


logger = logging.getLogger(__name__)

_ARTIFACT_FILES = (
    "penetration_test_report.md",
    "findings.sarif",
    "run.json",
    "redwake.log",
)


def save_report_artifacts(target_path: str | Path, run_dir: Path) -> list[Path]:
    """Copy key report files from run_dir to target_path.

    target_path:
        - If a directory (exists or ends with '/'): files copied inside it.
        - If a file path (no parent dir or no '/' extension): treated as the
          destination path for `penetration_test_report.md`; other artifacts
          are copied next to it with `_findings.sarif`, `_run.json` suffixes.

    Returns: list of successfully copied destination paths (empty on failure).
    """
    if not run_dir.exists() or not run_dir.is_dir():
        logger.warning("save_report: run_dir %s does not exist", run_dir)
        return []

    target = Path(target_path).expanduser().resolve()

    # Decide: directory or file destination
    if target.suffix == "" or str(target).endswith("/") or target.is_dir():
        target_dir = target
        target_dir.mkdir(parents=True, exist_ok=True)
        file_dest_prefix = target_dir
        is_dir_dest = True
    else:
        # File destination: write penetration_test_report.md to target,
        # siblings for other artifacts
        target.parent.mkdir(parents=True, exist_ok=True)
        file_dest_prefix = target.parent
        is_dir_dest = False

    copied: list[Path] = []
    for fname in _ARTIFACT_FILES:
        src = run_dir / fname
        if not src.exists() or not src.is_file():
            logger.debug("save_report: skipping %s (not found)", src)
            continue

        if is_dir_dest:
            dest = target_dir / fname
        elif fname == "penetration_test_report.md":
            dest = target
        else:
            stem = target.stem
            suffix = target.suffix.lstrip(".")
            dest = file_dest_prefix / f"{stem}_{fname}" if suffix != ".md" else f"{stem}_{fname}"

        try:
            shutil.copy2(src, dest)
            copied.append(dest)
            logger.info("save_report: copied %s -> %s", src.name, dest)
        except OSError as exc:
            logger.warning("save_report: failed to copy %s: %s", src.name, exc)

    return copied
