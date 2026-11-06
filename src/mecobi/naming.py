"""Output filename conventions.

Charge suffix encodes total charge so it can be read back when invoking xtb:
    +1 -> ``c1``   0 -> ``c0``   -1 -> ``cm1``   (negative uses ``cm`` prefix)

Isomer suffix is numeric: ``iso01``, ``iso02`` ...

NOTE — the pre-release prototype encoded negative charge as ``m1`` (no ``c``);
MeCoBi uses ``cm1``. Flagged so the choice is explicit, not silent.
"""

from __future__ import annotations

import re
from pathlib import Path

# Characters illegal in a Windows filename (and control chars); also unsafe as a
# path component on POSIX for `/`. Replaced with `_`.
_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Windows reserved device names (case-insensitive, with or without an extension).
_WINDOWS_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def sanitize_component(name: str, *, fallback: str = "complex") -> str:
    """Turn an untrusted string into ONE safe filename component (never a path).

    Defends against path traversal in output filenames: strips any
    directory part (so absolute, drive-qualified ``C:\\..``, UNC ``\\\\srv\\share``
    and ``../`` inputs collapse to their final component), replaces characters that
    are invalid on Windows or act as separators, trims trailing spaces/dots (also
    illegal on Windows), guards reserved device names, and falls back to
    ``fallback`` when nothing usable remains. Ordinary chemical names are preserved
    (brackets and most punctuation are kept; only genuinely illegal chars change).
    """
    # Keep only the final path component: defeats absolute/drive/UNC/.. inputs.
    name = str(name).replace("\\", "/").rsplit("/", 1)[-1]
    name = _INVALID_CHARS.sub("_", name)
    name = name.strip(" .")  # Windows forbids trailing spaces/dots
    if not name or name in {".", ".."}:
        return fallback
    if name.upper().split(".", 1)[0] in _WINDOWS_RESERVED:
        name = f"_{name}"
    return name


def unique_output_path(output_dir: str | Path, stem: str, ext: str = ".xyz") -> Path:
    """Return a collision-free path ``<output_dir>/<stem><ext>`` inside output_dir.

    Verifies (defence in depth, on top of :func:`sanitize_component`) that the
    resolved destination stays *directly* within the resolved ``output_dir``, then
    appends ``_2``, ``_3`` … if a file already exists, so repeated or
    post-sanitization-identical names never silently overwrite an earlier result.
    """
    out = Path(output_dir).resolve()
    candidate = out / f"{stem}{ext}"
    if candidate.resolve().parent != out:
        raise ValueError(f"refusing unsafe output path for stem {stem!r}")
    i = 2
    while candidate.exists():
        candidate = out / f"{stem}_{i}{ext}"
        i += 1
    return candidate


def format_charge(charge: int) -> str:
    """Return the filename charge token, e.g. ``c1``, ``c0``, ``cm1``."""
    if charge < 0:
        return f"cm{abs(charge)}"
    return f"c{charge}"


def isomer_suffix(index: int) -> str:
    """Zero-padded numeric isomer token, e.g. ``iso01``."""
    return f"iso{index:02d}"


def make_stem(
    base: str,
    charge: int,
    *,
    isomer_index: int | None = None,
    isomer_label: str | None = None,
) -> str:
    """Assemble the output file stem.

    ``base`` is the per-complex base name (source deferred).
    Prefer ``isomer_label`` when a human-readable label exists (e.g. ``trans_AC``);
    otherwise fall back to the numeric ``isomer_index``.
    """
    parts = [sanitize_component(base)]
    if isomer_label:
        parts.append(sanitize_component(isomer_label))
    elif isomer_index is not None:
        parts.append(isomer_suffix(isomer_index))
    parts.append(format_charge(charge))
    return "_".join(parts)
