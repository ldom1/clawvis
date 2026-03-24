"""Resolve which on-disk memory tree powers the Hub Brain (projects/*.md, Quartz)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


def active_brain_memory_root(
    *,
    memory_root: Path,
    linked_instances: Sequence[str] | None,
) -> Path:
    """Pick the Brain memory directory from linked instances vs runtime MEMORY_ROOT.

    - Collects ``<instance>/memory`` for each path in ``linked_instances`` that exists.
    - If ``memory_root`` (resolved) equals one of those, returns it.
    - Else returns the first candidate (paths sorted lexicographically).
    - If no valid linked memory dirs, returns ``memory_root`` (unchanged default).
    """
    runtime_mem = memory_root.expanduser().resolve()
    candidates: list[Path] = []
    seen: set[str] = set()
    for path_str in linked_instances or []:
        inst = Path(str(path_str).strip()).expanduser().resolve()
        if not inst.is_dir():
            continue
        mem = inst / "memory"
        if not mem.is_dir():
            continue
        key = str(mem.resolve())
        if key in seen:
            continue
        seen.add(key)
        candidates.append(mem.resolve())
    candidates.sort(key=lambda p: p.as_posix().lower())
    for mem in candidates:
        if mem.resolve() == runtime_mem:
            return mem
    if candidates:
        return candidates[0]
    return runtime_mem
