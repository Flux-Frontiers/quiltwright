"""
ParaView state files, via headless pvpython
============================================

A scene composed in `ParaView <https://www.paraview.org/>`_ -- the filter
pipeline, the colour maps, the opacity transfer functions, the representation
settings, the camera -- lives in a ``.pvsm`` state file.  None of that
survives exporting the data to a ``.vtm`` and reading it back into PyVista:
the geometry comes across and everything the user spent the afternoon on
does not.  This module takes the other route.  It hands the state file back
to ParaView's own Python interpreter, ``pvpython``, and sweeps the camera of
the render view *in place*, so the frames are of the session the user
actually built.

**The sweep is the same one every backend makes.**  For each view the camera
position and focal point translate together along the camera's right vector,
no rotation, and ``vtkCamera.SetWindowCenter`` shears the frustum back so the
original focal point stays centred -- the off-axis recipe of
:func:`~quiltwright.lfd.render_quilt`, applied to the vtkCamera ParaView owns
instead of the one PyVista owns.  The frames are then tiled by
:func:`~quiltwright.quilt.assemble_quilt`, as the POV-Ray and Cycles
frames are.

**ParaView is optional, and stays external.**  It is a 500 MB desktop
application with its own Python, not a package a virtualenv can import, so
this module drives it by subprocess only and finds the binary through
:func:`find_pvpython`.  Everything that can be done in a normal interpreter
is done here, where it is tested without ParaView present; the script that
runs inside ``pvpython`` is short and does nothing it does not have to.

**What has been verified, and what has not.**  ``SetWindowCenter`` survives
ParaView's ``Render()`` in the default *builtin* server mode, which is what
``pvpython`` runs and what a laptop session is.  Whether the shear reaches
the render side in client-server or MPI mode has not been tested; ParaView
syncs camera position, focal point, view-up and view angle to a remote server
through named proxy properties, and ``WindowCenter`` is not among them.

Typical use::

    from quiltwright import QUILT_PRESETS, save_quilt
    from quiltwright.paraview import render_paraview_quilt

    spec = QUILT_PRESETS["portrait"]
    quilt = render_paraview_quilt("session.pvsm", spec)
    save_quilt(quilt, "session", spec)

Part of Quiltwright -- https://github.com/Flux-Frontiers/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from .quilt import QuiltSpec, assemble_quilt

__all__ = [
    "PARAVIEW_ENV",
    "ParaViewCamera",
    "ParaViewNotAvailable",
    "available",
    "depth_report",
    "find_pvpython",
    "probe_paraview_state",
    "render_paraview_quilt",
    "render_paraview_views",
]

#: Environment variable naming the ``pvpython`` executable, checked before
#: ``PATH``.  The macOS application bundle does not put it on ``PATH``.
PARAVIEW_ENV = "PARAVIEW_BINARY"

#: Where the macOS cask leaves the bundle.  Globbed newest-last so a machine
#: with two versions installed gets the later one.
_MAC_BUNDLES = "/Applications/ParaView*.app/Contents/bin/pvpython"

#: Depth labels, matching :data:`quiltwright.lfd.DEPTH_LABELS`.
DEPTH_LABELS = ("near", "focal", "far")


class ParaViewNotAvailable(RuntimeError):
    """Raised when no ``pvpython`` can be found."""


def find_pvpython(binary: str | None = None) -> str:
    """Locate the ``pvpython`` executable.

    :param binary: Explicit path or command name; falls back to the
        :data:`PARAVIEW_ENV` environment variable, then ``pvpython`` on
        ``PATH``, then the macOS application bundle.
    :return: Path to the executable.
    :raises ParaViewNotAvailable: If none of those turn one up.
    """
    candidate = binary or os.environ.get(PARAVIEW_ENV)
    if candidate:
        found = shutil.which(candidate)
        if found:
            return found
        raise ParaViewNotAvailable(f"pvpython {candidate!r} not found or not executable.")
    found = shutil.which("pvpython")
    if found:
        return found
    bundles = sorted(glob.glob(_MAC_BUNDLES))
    if bundles:
        return bundles[-1]
    raise ParaViewNotAvailable(
        "ParaView's pvpython is not on PATH and no /Applications/ParaView*.app was found.\n"
        "  brew install --cask paraview                # macOS\n"
        "  https://www.paraview.org/download/          # binaries for every platform\n"
        f"or set {PARAVIEW_ENV} to the full path of pvpython."
    )


def available() -> str | None:
    """Path to ``pvpython`` if one can be found, else ``None``."""
    try:
        return find_pvpython()
    except ParaViewNotAvailable:
        return None


@dataclass(frozen=True)
class ParaViewCamera:
    """The render view's camera, as the sweep will use it.

    What :func:`probe_paraview_state` reads back out of the state after the
    same framing :func:`render_paraview_views` applies -- the FOV narrowed
    and the camera dollied back, then the zoom dolly -- so the numbers
    describe the render about to be made, not the session as saved.
    Satisfies :class:`~quiltwright.quilt.HasLens`, so it goes straight to
    :func:`~quiltwright.povray.format_depth_budget`.

    :param view: Name of the render view swept.  A state can hold several;
        the active one is used if it is a render view, else the first.
    :param position: Eye, in scene units, after framing.
    :param focal_point: Look-at point, which becomes the holographic focal
        plane.
    :param view_up: Camera up vector.
    :param fov: Vertical field of view in degrees, after framing.
    :param focal_distance: Eye to focal plane, in scene units, after framing.
    :param depths: Labelled near / focal / far distances along the view
        axis, from the bounds of every visible source.  Near and far are
        ``None`` when nothing visible reports bounds.
    """

    view: str
    position: tuple[float, float, float]
    focal_point: tuple[float, float, float]
    view_up: tuple[float, float, float]
    fov: float
    focal_distance: float
    depths: Mapping[str, float | None]

    @classmethod
    def _from_meta(cls, meta: Mapping[str, Any]) -> ParaViewCamera:
        """Build from the JSON the sweep script writes."""
        return cls(
            view=str(meta["view"]),
            position=tuple(meta["position"]),
            focal_point=tuple(meta["focal_point"]),
            view_up=tuple(meta["view_up"]),
            fov=float(meta["fov"]),
            focal_distance=float(meta["focal_distance"]),
            depths=dict(meta["depths"]),
        )


# ---------------------------------------------------------------------------
# The ParaView side
# ---------------------------------------------------------------------------

#: The sweep geometry, inlined because the script cannot import quiltwright
#: from ParaView's interpreter.  Kept as its own block so a test can exec it
#: and check it against :func:`~quiltwright.quilt.view_offsets` and
#: :func:`~quiltwright.quilt.window_shear`, which are the source of truth.
_SWEEP_MATH = '''
import math


def sweep_offsets(n_views, view_cone, distance):
    """Lateral eye offsets along the right vector, view 0 leftmost."""
    if n_views == 1:
        return [0.0]
    half = math.radians(view_cone) / 2.0
    step = 2.0 * half / (n_views - 1)
    return [distance * math.tan(-half + i * step) for i in range(n_views)]


def window_shear(offset, focal_distance, fov, aspect):
    """vtkCamera WindowCenter x that pins the look-at point for this offset."""
    return -offset / (focal_distance * math.tan(math.radians(fov) / 2.0) * aspect)
'''

#: Script run inside pvpython.  Upper-case names are bound as literals in
#: front of it by :func:`_literals`.  It loads the state, frames the camera
#: the way ``render_quilt`` does, measures the visible bounds for the depth
#: budget, writes META_OUT, and -- unless PROBE_ONLY -- sweeps the camera
#: and writes one PNG per view into WORKDIR.  Progress goes to stdout as
#: ``QW_VIEW i/n`` lines, which the caller streams.
_SWEEP_SCRIPT = """
import json
import os
import sys

import paraview.simple as ps
from paraview.simple import (
    GetActiveView, GetDisplayProperties, GetRenderViews, GetSources,
    LoadState, Render, SaveScreenshot, SetActiveView,
)

# Otherwise the first Render() resets the camera and the state's own framing
# -- the one thing this script exists to preserve -- is thrown away.
ps._DisableFirstRenderCameraReset()

LoadState(STATE)
views = GetRenderViews()
if not views:
    sys.exit("state file contains no render view")
active = GetActiveView()
view = active if active in views else views[0]
SetActiveView(view)
view.ViewSize = [RENDER_W, RENDER_H]
if HIDE_ORIENTATION_AXES:
    # A screen-pinned widget lands at the same tile position in every view,
    # so it would float exactly on the glass in every hologram.
    view.OrientationAxesVisibility = 0

cam = view.GetActiveCamera()
pos = list(cam.GetPosition())
focal = list(cam.GetFocalPoint())
up = list(cam.GetViewUp())


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _norm(v):
    return math.sqrt(sum(c * c for c in v))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


forward = _sub(focal, pos)
distance = _norm(forward)
forward = [c / distance for c in forward]
right = _cross(forward, up)
right = [c / _norm(right) for c in right]
true_up = _cross(right, forward)

# Mirror render_quilt's framing: narrow the FOV and dolly back so the focal
# plane keeps its size in frame, then the zoom dolly.
fov = cam.GetViewAngle()
if FOV is not None:
    half_height = distance * math.tan(math.radians(fov) / 2.0)
    distance = half_height / math.tan(math.radians(FOV) / 2.0)
    fov = FOV
if ZOOM is not None and ZOOM != 1.0:
    distance /= ZOOM
pos = [f - fw * distance for f, fw in zip(focal, forward)]

# Depth budget: the bounds of everything visible, projected on the view axis.
near = far = None
for src in GetSources().values():
    try:
        if not GetDisplayProperties(src, view).Visibility:
            continue
        # Nothing has rendered yet, so nothing has executed: without this the
        # data information is empty and the bounds come back inverted.
        src.UpdatePipeline()
        b = src.GetDataInformation().GetBounds()
    except Exception:
        continue
    if b[0] > b[1]:
        continue  # empty dataset
    for x in (b[0], b[1]):
        for y in (b[2], b[3]):
            for z in (b[4], b[5]):
                d = sum(c * f for c, f in zip(_sub([x, y, z], pos), forward))
                near = d if near is None else min(near, d)
                far = d if far is None else max(far, d)

try:
    view_name = ps.servermanager.ProxyManager().GetProxyName("views", view.SMProxy)
except Exception:
    view_name = "RenderView"

with open(META_OUT, "w") as fh:
    json.dump({
        "view": view_name,
        "position": pos,
        "focal_point": focal,
        "view_up": true_up,
        "fov": fov,
        "focal_distance": distance,
        "depths": {LABELS[0]: near, LABELS[1]: distance, LABELS[2]: far},
    }, fh)

if PROBE_ONLY:
    sys.exit(0)

cam.SetViewAngle(fov)
offsets = sweep_offsets(N_VIEWS, VIEW_CONE, distance)
for i, off in enumerate(offsets):
    cam.SetPosition(*[p + r * off for p, r in zip(pos, right)])
    cam.SetFocalPoint(*[f + r * off for f, r in zip(focal, right)])
    cam.SetViewUp(*true_up)
    cam.SetWindowCenter(window_shear(off, distance, fov, ASPECT), 0.0)
    Render(view)
    SaveScreenshot(
        os.path.join(WORKDIR, "view%03d.png" % i), view, ImageResolution=[RENDER_W, RENDER_H]
    )
    print("QW_VIEW %d/%d" % (i + 1, N_VIEWS), flush=True)
"""


def _literals(**values: object) -> str:
    """Bind the script's upper-case names as Python literals.

    Paths go in as repr'd literals rather than pasted text, so a path with a
    quote in it cannot end the string and run as code.
    """
    return "".join(f"{k} = {v!r}\n" for k, v in values.items())


def _script(
    state: Path,
    spec: QuiltSpec,
    workdir: Path,
    meta_out: Path,
    *,
    fov: float | None,
    zoom: float | None,
    hide_orientation_axes: bool,
    probe_only: bool,
) -> str:
    """Assemble the pvpython script for one sweep (or probe)."""
    render_h = spec.tile_height
    render_w = round(render_h * spec.aspect)
    return (
        _literals(
            STATE=str(state),
            WORKDIR=str(workdir),
            META_OUT=str(meta_out),
            RENDER_W=render_w,
            RENDER_H=render_h,
            ASPECT=render_w / render_h,
            N_VIEWS=spec.n_views,
            VIEW_CONE=float(spec.view_cone),
            FOV=fov,
            ZOOM=zoom,
            HIDE_ORIENTATION_AXES=hide_orientation_axes,
            PROBE_ONLY=probe_only,
            LABELS=tuple(DEPTH_LABELS),
        )
        + _SWEEP_MATH
        + _SWEEP_SCRIPT
    )


def _quiet(text: str) -> str:
    """Drop the OSPRay/OpenVKL module noise pvpython prints at startup."""
    return "\n".join(line for line in text.splitlines() if "[openvkl]" not in line)


def _run_pvpython(
    pvpython: str, script: str, *, n_views: int, progress: bool
) -> tuple[int, str, str]:
    """Run *script* under *pvpython*, streaming ``QW_VIEW`` lines as progress.

    :return: ``(returncode, stdout, stderr)`` with the progress lines removed
        from stdout.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(script)
        path = fh.name
    out_lines: list[str] = []
    try:
        proc = subprocess.Popen(
            [pvpython, "--force-offscreen-rendering", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            if line.startswith("QW_VIEW "):
                if progress:
                    print(f"\r  pv view {line.split()[1]}", end="", flush=True)
            else:
                out_lines.append(line.rstrip("\n"))
        _, stderr = proc.communicate()
        if progress and n_views:
            print()
    finally:
        Path(path).unlink(missing_ok=True)
    return proc.returncode, "\n".join(out_lines), _quiet(stderr)


def _check(state: str | Path) -> Path:
    path = Path(state).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"ParaView state file not found: {path}")
    return path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def probe_paraview_state(
    state: str | Path,
    spec: QuiltSpec,
    *,
    fov: float | None = 14.0,
    zoom: float | None = None,
    binary: str | None = None,
) -> ParaViewCamera:
    """Read the camera and depth range a sweep of *state* would use.

    Loads the state in ``pvpython`` without rendering a frame, applies the
    same framing :func:`render_paraview_views` will, and reports the result.
    Print :func:`depth_report` from it before paying for the sweep; a
    ParaView startup costs a few seconds, a 48-view sweep of a large dataset
    costs a good deal more.

    :param state: The ``.pvsm`` file.  Not modified.
    :param spec: Quilt specification; only its aspect matters here.
    :param fov: Vertical FOV the sweep will use, with the
        :func:`~quiltwright.lfd.render_quilt` dolly-back convention.
        ``None`` keeps the state's own.
    :param zoom: Zoom the sweep will use.
    :param binary: ``pvpython`` executable; see :func:`find_pvpython`.
    :return: The framed camera and its depth range.
    """
    pvpython = find_pvpython(binary)
    path = _check(state)
    with tempfile.TemporaryDirectory(prefix="paraview_probe_") as tmp:
        meta_out = Path(tmp) / "camera.json"
        script = _script(
            path,
            spec,
            Path(tmp),
            meta_out,
            fov=fov,
            zoom=zoom,
            hide_orientation_axes=True,
            probe_only=True,
        )
        code, out, err = _run_pvpython(pvpython, script, n_views=0, progress=False)
        if code != 0 or not meta_out.exists():
            reason = f"exited {code}" if code != 0 else "did not write the camera probe"
            raise RuntimeError(f"pvpython {reason}\n{out}\n{err}")
        return ParaViewCamera._from_meta(json.loads(meta_out.read_text()))


def depth_report(camera: ParaViewCamera, spec: QuiltSpec, *, soft_px: float = 5.5) -> str:
    """Depth budget for a probed state, as a report to print before rendering.

    The ParaView counterpart to :func:`quiltwright.lfd.depth_report`.

    :param camera: From :func:`probe_paraview_state`, with the same *fov* and
        *zoom* the render will use.
    :param spec: Quilt specification.
    :param soft_px: Disparity above which a row is flagged as soft.
    :return: Multi-line report.
    """
    from .povray import format_depth_budget

    depths = {k: v for k, v in camera.depths.items() if v is not None}
    return format_depth_budget(spec, camera, depths, soft_px=soft_px)


def render_paraview_views(
    state: str | Path,
    spec: QuiltSpec,
    out_dir: str | Path,
    *,
    fov: float | None = 14.0,
    zoom: float | None = None,
    view_cone: float | None = None,
    hide_orientation_axes: bool = True,
    binary: str | None = None,
    progress: bool = True,
) -> tuple[list[Path], ParaViewCamera]:
    """Sweep the state's render view and write one PNG per view.

    The per-view half of :func:`render_paraview_quilt`, for a hologram
    printer's sweep or for inspecting the frames.

    :param state: The ``.pvsm`` file.  Not modified.
    :param spec: Quilt specification (grid, size, aspect, cone).
    :param out_dir: Directory to write ``view000.png`` ... into; created if
        absent.
    :param fov: Vertical field of view in degrees, with the
        :func:`~quiltwright.lfd.render_quilt` dolly-back convention;
        ``None`` keeps the state's own FOV and distance.
    :param zoom: Optional dolly factor applied after framing.
    :param view_cone: Override the spec's view cone in degrees.
    :param hide_orientation_axes: Turn off ParaView's corner axes widget.  It
        is pinned to the screen, so it would sit on the glass in every view.
    :param binary: ``pvpython`` executable; see :func:`find_pvpython`.
    :param progress: Print a progress line while rendering.
    :return: The PNG paths in view order (view 0 leftmost), and the framed
        camera the sweep used.
    """
    pvpython = find_pvpython(binary)
    path = _check(state)
    if view_cone is not None:
        spec = replace(spec, view_cone=view_cone)
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    meta_out = out / "camera.json"
    script = _script(
        path,
        spec,
        out,
        meta_out,
        fov=fov,
        zoom=zoom,
        hide_orientation_axes=hide_orientation_axes,
        probe_only=False,
    )
    code, stdout, stderr = _run_pvpython(pvpython, script, n_views=spec.n_views, progress=progress)
    views = [out / f"view{i:03d}.png" for i in range(spec.n_views)]
    missing = [p.name for p in views if not p.exists()]
    if code != 0 or missing or not meta_out.exists():
        # pvpython can exit 0 with nothing written -- a bad state path is
        # logged, not raised -- so the frames are the real success signal.
        reason = f"exited {code}" if code != 0 else f"did not write {missing or [meta_out.name]}"
        raise RuntimeError(f"pvpython {reason}\n{stdout}\n{stderr}")
    camera = ParaViewCamera._from_meta(json.loads(meta_out.read_text()))
    return views, camera


def render_paraview_quilt(
    state: str | Path,
    spec: QuiltSpec,
    *,
    fov: float | None = 14.0,
    zoom: float | None = None,
    view_cone: float | None = None,
    hide_orientation_axes: bool = True,
    binary: str | None = None,
    keep_views: str | Path | None = None,
    progress: bool = True,
) -> np.ndarray:
    """Render a ParaView state file into a Looking Glass quilt.

    Loads the ``.pvsm`` in ``pvpython``, sweeps the render view's camera
    across the display's view cone with off-axis projections, and tiles the
    frames with :func:`~quiltwright.quilt.assemble_quilt`.  The whole sweep
    runs in one ParaView process, so the state is loaded once.

    :param state: The ``.pvsm`` file.  Not modified.
    :param spec: Quilt specification (grid, size, aspect, cone).
    :param fov: Vertical field of view in degrees; see
        :func:`render_paraview_views`.
    :param zoom: Optional dolly factor applied after framing.
    :param view_cone: Override the spec's view cone in degrees.
    :param hide_orientation_axes: Turn off ParaView's corner axes widget.
    :param binary: ``pvpython`` executable; see :func:`find_pvpython`.
    :param keep_views: Directory to retain the per-view PNGs and the
        ``camera.json`` probe in.  Discarded if ``None``.
    :param progress: Print a progress line while rendering.
    :return: ``uint8`` RGB array of shape ``(quilt_height, quilt_width, 3)``.
    """
    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="paraview_quilt_") as tmp:
        workdir = Path(keep_views).expanduser() if keep_views is not None else Path(tmp)
        views, _camera = render_paraview_views(
            state,
            spec,
            workdir,
            fov=fov,
            zoom=zoom,
            view_cone=view_cone,
            hide_orientation_axes=hide_orientation_axes,
            binary=binary,
            progress=progress,
        )
        return assemble_quilt((np.asarray(Image.open(png).convert("RGB")) for png in views), spec)
