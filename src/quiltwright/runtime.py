"""Process-level defaults shared by more than one backend.

Nothing here knows about quilts, cameras, or a renderer.  The courtesy
core cap is the one constant both POV-Ray and Cycles need so a quilt
does not take every core on the machine; the ffmpeg lookup is shared by
the quilt-video encoder and the HLD encoder.

Part of Quiltwright -- https://github.com/suchanek/quiltwright
Author: Eric G. Suchanek, PhD
"""

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
