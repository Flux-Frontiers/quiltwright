"""
Download cache locations
========================

Quiltwright fetches a few large assets at runtime rather than shipping them:
The Virtual Brain's demonstration datasets (:mod:`quiltwright.tvb_data`) and
the Allen Institute mouse brain atlas (``scripts/render_pyvista_hologram.py``).
Both are hundreds of megabytes, and both need somewhere sensible to live.

This module decides where.  It exists so that every downloader agrees on one
answer, and so that answer is the one the *platform* expects rather than the
one that happens to be right on Linux::

    macOS    ~/Library/Caches/quiltwright/<name>
    Linux    $XDG_CACHE_HOME/quiltwright/<name>, default ~/.cache/quiltwright/<name>
    Windows  %LOCALAPPDATA%\\quiltwright\\Cache\\<name>

This matches PyVista, which caches its own downloads through
``pooch.os_cache`` — so on macOS its data sits in ``~/Library/Caches``, and a
hard-coded ``~/.cache`` would scatter our assets somewhere macOS itself never
looks.

:func:`dataset_cache_dir` is the entry point; each caller passes its own
environment variable so a user can relocate one dataset without moving the
rest.

Part of Quiltwright — https://github.com/suchanek/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["cache_root", "dataset_cache_dir"]

#: Application name used for the per-user cache directory.
_APP_NAME = "quiltwright"


def cache_root() -> Path:
    """Return the per-user cache root for Quiltwright on this platform.

    Uses :mod:`platformdirs` when it is available — it arrives transitively
    with the ``viz`` extra (pyvista → pooch) — and falls back to the
    XDG layout otherwise, which is correct on Linux and a reasonable guess
    anywhere else.  No directory is created.

    :return: Path to the cache root (not guaranteed to exist).
    """
    try:
        from platformdirs import user_cache_dir

        return Path(user_cache_dir(_APP_NAME))
    except ImportError:
        xdg = os.environ.get("XDG_CACHE_HOME")
        base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
        return base / _APP_NAME


def dataset_cache_dir(name: str, *, env_var: str | None = None, create: bool = False) -> Path:
    """Return the cache directory for one downloaded dataset.

    :param name: Short dataset name, used as the directory under
        :func:`cache_root` — e.g. ``"tvb"`` or ``"allen_ccf"``.
    :param env_var: Optional environment variable that, when set, overrides
        the location entirely.  Use this to put a large download on another
        volume, share one copy between checkouts, or pin it for CI.
    :param create: Create the directory (and parents) before returning.
    :return: Path to the dataset's cache directory.
    """
    override = os.environ.get(env_var) if env_var else None
    path = Path(override).expanduser() if override else cache_root() / name
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path
