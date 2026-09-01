"""Process-level defaults shared by more than one backend.

Nothing here knows about quilts, cameras, or a renderer.  The courtesy
core cap is the one constant both POV-Ray and Cycles need so a quilt
does not take every core on the machine; the ffmpeg lookup is shared by
the quilt-video encoder and the HLD encoder; ``require_pyvista`` and
``triple`` are the small helpers more than one module used to copy.

Part of Quiltwright -- https://github.com/Flux-Frontiers/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from collections.abc import Iterable

#: Cores held back from a render by default, so a multi-minute quilt does
#: not make the rest of the machine unusable.  POV-Ray's own default is
#: every core it can see; Blender's ``-t 0`` is the same.
COURTESY_CORES_HELD_BACK = 2


def find_ffmpeg() -> str:
    """Locate an ffmpeg binary: system PATH first, then imageio-ffmpeg's.

    :return: Path to an ffmpeg executable.
    :raises RuntimeError: If no ffmpeg can be found.
    """
    import shutil

    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise RuntimeError(
            "Quilt video encoding requires ffmpeg.\n"
            "Install it system-wide, or:  pip install imageio-ffmpeg"
        ) from exc


def require_pyvista(fn_name: str) -> None:
    """Raise a clear ImportError if pyvista is not installed.

    :param fn_name: Public function name used in the error message.
    :raises ImportError: If the ``viz`` extra (pyvista) is not installed.
    """
    try:
        import pyvista  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            f"{fn_name}() requires pyvista.\nInstall with:  poetry install --with viz"
        ) from exc


def triple(v: Iterable[float]) -> tuple[float, float, float]:
    """Coerce a 3-vector -- list, tuple, NumPy array -- to a float 3-tuple.

    ``tuple(v)`` types as ``tuple[float, ...]``, which is not a camera
    coordinate.  Unpacking states the arity and rejects a wrong-length
    vector here rather than later.

    :param v: Any iterable of three reals.
    :return: ``(x, y, z)`` as plain floats.
    :raises ValueError: If *v* does not have exactly three components.
    """
    x, y, z = (float(c) for c in v)
    return (x, y, z)
