#!/usr/bin/env python
"""
Render PyVista example datasets as Looking Glass holograms.

Companion to ``render_museum_hologram.py`` / ``render_still_life_hologram.py``,
which drive the POV-Ray backend. This one drives the PyVista path instead:
each subject below is a real terrain or volumetric scan pulled straight from
``pyvista.examples`` (or, for the mouse brain, the Allen Institute's own
download server), fed through the same off-axis quilt sweep the museum uses.

See ``docs/pyvista-datasets.md`` for how these subjects were chosen and
where to find more like them.

Each subject picks a view *direction* (a generic 3/4 orbit, or an explicit
camera position where one is documented, as for Damavand); ``_frame_and_focus()``
then does what the POV-Ray scripts do by hand -- fit tightly to the scene and
place the focal plane at the harmonic mean of the near/far depths -- except
measured from exact PyVista geometry (a bounding sphere) rather than a
rendered plane-sweep probe. The printed depth budget is the same
adjacent-view-disparity check ``docs/povray.md`` describes; if a result still
ghosts, narrow ``--view-cone``.

Usage::

    python scripts/render_pyvista_hologram.py st-helens --preview
    python scripts/render_pyvista_hologram.py mouse-brain --resolution 50
    python scripts/render_pyvista_hologram.py brain --device portrait --cast
    python scripts/render_pyvista_hologram.py damavand --still

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import math
import sys
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path

import numpy as np

from quiltwright.cache import dataset_cache_dir
from quiltwright.lfd import (
    QUILT_PRESETS,
    QuiltSpec,
    focal_distance_for_range,
    render_quilt,
    save_quilt,
    view_disparity,
)

try:
    import pyvista as pv
    from pyvista import examples
except ImportError:
    print(
        "error: this script requires pyvista.\nInstall with:  poetry install --with viz",
        file=sys.stderr,
    )
    raise SystemExit(1) from None

#: Allen Institute Mouse Brain Common Coordinate Framework (CCFv3) average
#: template -- a real volumetric atlas built from 1,675 C57BL/6J mice. Plain
#: NRRD over HTTP, no API key or AllenSDK dependency. See
#: docs/pyvista-datasets.md for the annotation (region-labeled) variant.
ALLEN_CCF_TEMPLATE_URL = (
    "http://download.alleninstitute.org/informatics-archive/current-release/"
    "mouse_ccf/average_template/average_template_{resolution}.nrrd"
)
#: Where the downloaded volumes live.  Platform-native (``~/Library/Caches``
#: on macOS, not ``~/.cache``), shared with the other Quiltwright downloaders,
#: and relocatable with ``$QUILTWRIGHT_ALLEN_CACHE`` -- these volumes run from
#: ~60 MB at 100 µm to ~1.5 GB at 10 µm, so putting them on another disk is a
#: reasonable thing to want.
ALLEN_CCF_CACHE = dataset_cache_dir("allen_ccf", env_var="QUILTWRIGHT_ALLEN_CACHE")

#: Pre-0.3.0 location, before the cache moved to a platform-native root.  An
#: existing download here is adopted rather than silently re-fetched.
_LEGACY_ALLEN_CCF_CACHE = Path.home() / ".cache" / "quiltwright" / "allen_ccf"


def _download_allen_template(resolution: int) -> Path:
    """Fetch (and cache) an Allen CCFv3 average-template volume.

    :param resolution: Isotropic voxel size in micrometres: 10, 25, 50, or 100.
        Finer resolutions are dramatically larger; 50 is a reasonable default.
    :return: Local path to the cached ``.nrrd`` file.
    """
    if resolution not in (10, 25, 50, 100):
        raise ValueError(f"resolution must be one of 10/25/50/100, got {resolution}")

    filename = f"average_template_{resolution}.nrrd"

    legacy = _LEGACY_ALLEN_CCF_CACHE / filename
    if legacy.exists() and legacy.parent != ALLEN_CCF_CACHE:
        print(f"  using existing download {legacy}")
        return legacy

    ALLEN_CCF_CACHE.mkdir(parents=True, exist_ok=True)
    dest = ALLEN_CCF_CACHE / filename
    if not dest.exists():
        url = ALLEN_CCF_TEMPLATE_URL.format(resolution=resolution)
        print(f"  downloading {url}")
        urllib.request.urlretrieve(url, dest)  # noqa: S310  (fixed http, trusted host)
    return dest


def _orbit_camera(p: pv.Plotter, *, elevation: float = -25.0, azimuth: float = 35.0) -> None:
    """Fit the scene, then tilt to a generic 3/4 view so depth reads clearly.

    ``reset_camera()`` alone tends to frame terrain and volumes dead-on,
    which is exactly the view with the least parallax to show off.

    :param p: The plotter, with data already added.
    :param elevation: Vertical tilt in degrees (negative looks down).
    :param azimuth: Horizontal rotation in degrees.
    """
    p.reset_camera()
    p.camera.elevation = elevation
    p.camera.azimuth = azimuth


#: Vertical FOV the final camera is locked to before framing/focus, matching
#: render_quilt()'s own default -- computing the depth budget at any other
#: FOV would not describe the render that actually happens.
RENDER_FOV = 14.0

#: Widest sweep used by default. Nothing bounds these subjects the way the
#: museum's walls do, and the tight bounding-box framing that fixes "the
#: subject reads too small" also raises disparity, so a device's native cone
#: (up to 50 deg) routinely overruns the ~4-5px ceiling. Same cap and
#: rationale as render_still_life_hologram.py's STANDARD_VIEW_CONE.
STANDARD_VIEW_CONE = 35.0


def _frame_and_focus(
    p: pv.Plotter, *, fov: float = RENDER_FOV, margin: float = 1.15
) -> tuple[float, float, float]:
    """Tightly frame the scene and place the focal plane by measured depth.

    ``reset_camera()`` fits the *un-tilted* bounds; once ``_orbit_camera()``
    (or an explicit ``camera_position``) tilts the view, that framing is too
    loose and the subject reads as small with a lot of empty margin -- ask
    for a mountain hologram and get a speck. This re-fits from scratch at the
    final view direction: the 8 bounding-box corners are projected onto the
    camera's own right/up/forward axes (accounting for foreshortening -- a
    flat, elongated DEM viewed obliquely needs far less distance than its
    bounding *sphere* would suggest), which gives the tightest distance that
    still keeps every corner in frame at the target FOV and window aspect.
    The focal plane then goes at the harmonic mean of the resulting near/far
    depths -- the same balance ``focal_distance_for_range()`` gives the
    POV-Ray scripts, just measured from exact PyVista geometry instead of a
    rendered plane-sweep probe.

    :param p: Plotter with data added, ``window_size`` already set to the
        final render resolution (aspect matters here), and the camera
        already pointed in the desired direction (position/focal_point set
        by the caller; only the *direction* survives -- position, view angle
        and focal distance are all overwritten here).
    :param fov: Vertical field of view to lock the camera to, in degrees.
        Must match what the render actually uses (``render_quilt``'s own
        default) or the printed depth budget describes a different camera
        than the one that renders.
    :param margin: Headroom beyond the tight corner-projected fit, as a
        fraction (1.15 = 15% clearance), so the subject doesn't touch the
        frame edges.
    :return: ``(near, far, focal_distance)`` in scene units, all measured
        from the final camera position -- the numbers `view_disparity()`
        expects.
    """
    camera = p.camera
    position = np.asarray(camera.position, dtype="d")
    focal = np.asarray(camera.focal_point, dtype="d")
    up = np.asarray(camera.up, dtype="d")
    forward = focal - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, forward)

    bounds = p.bounds
    lo = np.array([bounds.x_min, bounds.y_min, bounds.z_min])
    hi = np.array([bounds.x_max, bounds.y_max, bounds.z_max])
    center = (lo + hi) / 2.0
    corners = np.array(list(product(*zip(lo, hi, strict=True))))
    offsets = corners - center
    f = offsets @ forward  # signed depth of each corner relative to center
    r = offsets @ right
    u = offsets @ true_up

    win_w, win_h = p.window_size
    half_v = math.tan(math.radians(fov) / 2.0)
    half_h = half_v * (win_w / win_h)

    # Smallest distance-from-center D such that every corner's angular
    # extent |u_i|/(D+f_i) (resp. |r_i|/half_h) still fits inside the FOV.
    d_needed = np.concatenate([np.abs(u) / half_v - f, np.abs(r) / half_h - f])
    distance = margin * max(float(d_needed.max()), 1.0)

    camera.position = tuple(center - forward * distance)
    camera.view_angle = fov
    depths = distance + f  # each corner's actual distance from the new camera
    near = float(depths.min())
    far = float(depths.max())

    focal_distance = focal_distance_for_range(near, far)
    camera.focal_point = tuple(np.asarray(camera.position) + forward * focal_distance)
    return near, far, focal_distance


def _load_st_helens(p: pv.Plotter) -> None:
    """Mt. St. Helens post-eruption DEM, warped into 3-D relief."""
    dem = examples.download_st_helens()
    surf = dem.warp_by_scalar("Elevation", factor=2.0)
    p.add_mesh(surf, cmap="gist_earth", show_scalar_bar=False)
    _orbit_camera(p)


def _load_damavand(p: pv.Plotter) -> None:
    """Mt. Damavand (Iran) magnetotelluric resistivity-anomaly probability volume.

    Not topography -- a 0-100 subsurface probability field (~7% NaN outside
    the region of interest), so a generic 3/4 orbit renders it as a
    near-uniform slab. Follows PyVista's own docstring recipe for this
    dataset instead: downsampled, ``reds`` colormap, default opacity, and
    the camera position from its own example.
    """
    vol = examples.download_damavand_volcano().resample(0.5)
    p.add_volume(vol, cmap="reds", show_scalar_bar=False)
    p.camera_position = pv.CameraPosition(
        position=(4.66316700e04, 4.32796241e06, -3.82467050e05),
        focal_point=(5.52532740e05, 3.98017300e06, -2.47450000e04),
        viewup=(4.10000000e-01, -2.90000000e-01, -8.60000000e-01),
    )


def _load_brain(p: pv.Plotter) -> None:
    """Human head MRI (classic VTK ``brain.vtk``)."""
    vol = examples.download_brain()
    p.add_volume(vol, cmap="bone", opacity="sigmoid", show_scalar_bar=False)
    _orbit_camera(p)


def _load_mouse_brain(resolution: int) -> Callable[[pv.Plotter], None]:
    """Allen CCFv3 mouse brain average template at the given resolution."""

    def load(p: pv.Plotter) -> None:
        path = _download_allen_template(resolution)
        vol = pv.read(path)
        p.add_volume(vol, cmap="bone", opacity="sigmoid", show_scalar_bar=False)
        _orbit_camera(p)

    return load


@dataclass(frozen=True)
class Subject:
    """A PyVista dataset staged for a quilt render.

    :param load: Adds the dataset to a fresh off-screen plotter and frames
        the camera. Takes no return value.
    :param about: One-line description printed before rendering.
    :param device: Suggested default device preset.
    """

    load: Callable[[pv.Plotter], None]
    about: str
    device: str = "16-landscape"


SUBJECTS: dict[str, Subject] = {
    "st-helens": Subject(
        _load_st_helens,
        "Mt. St. Helens post-eruption DEM (examples.download_st_helens)",
    ),
    "damavand": Subject(
        _load_damavand,
        "Mt. Damavand magnetotelluric anomaly-probability volume "
        "(examples.download_damavand_volcano)",
    ),
    "brain": Subject(
        _load_brain,
        "Human head MRI, classic VTK brain.vtk (examples.download_brain)",
    ),
    "mouse-brain": Subject(
        _load_mouse_brain(50),
        "Allen Institute mouse brain CCFv3 average template, {resolution}um",
        device="portrait",
    ),
}


def main() -> int:
    """Render (and optionally cast) one PyVista-dataset quilt.

    :return: Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subject", choices=sorted(SUBJECTS), help="which dataset")
    parser.add_argument(
        "--device", default=None, choices=sorted(QUILT_PRESETS), help="target display"
    )
    parser.add_argument(
        "--view-cone",
        type=float,
        default=None,
        help="camera sweep in degrees; defaults to the device's own cone",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=50,
        choices=(10, 25, 50, 100),
        help="mouse-brain only: Allen CCFv3 voxel size in micrometres",
    )
    parser.add_argument("--preview", action="store_true", help="quarter-size quilt, for iterating")
    parser.add_argument(
        "--still",
        action="store_true",
        help="single centre-view screenshot instead of a quilt, saved to "
        "renders/gallery/ -- the diffable reference for what the scene looks "
        "like, same convention as the POV-Ray scenes",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="output stem; defaults to renders/quilts/<subject> "
        "(renders/gallery/<subject> with --still)",
    )
    parser.add_argument("--cast", action="store_true", help="send to Looking Glass Bridge")
    args = parser.parse_args()

    subject = SUBJECTS[args.subject]
    if args.subject == "mouse-brain" and args.resolution != 50:
        subject = replace(subject, load=_load_mouse_brain(args.resolution))
    about = subject.about.format(resolution=args.resolution)

    device = args.device or subject.device
    spec: QuiltSpec = QUILT_PRESETS[device]
    if args.view_cone is not None:
        spec = replace(spec, view_cone=args.view_cone)
    elif spec.view_cone > STANDARD_VIEW_CONE:
        print(
            f"  view cone        {spec.view_cone:.0f} deg native -> "
            f"{STANDARD_VIEW_CONE:.0f} to keep the budget in range "
            f"(--view-cone {spec.view_cone:.0f} to override)"
        )
        spec = replace(spec, view_cone=STANDARD_VIEW_CONE)
    if args.preview:
        spec = replace(spec, quilt_width=spec.quilt_width // 4, quilt_height=spec.quilt_height // 4)

    print(f"{args.subject} hologram -> {device}{' (preview)' if args.preview else ''}")
    print(f"  {about}")
    print(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}, cone {spec.view_cone:.0f} deg"
    )

    if args.still:
        # A fixed-resolution single frame at the device's aspect, independent
        # of quilt tiling -- long edge 1920 landscape / 1600 portrait, in the
        # same size class as the POV-Ray stills (renders/gallery/).
        if spec.aspect >= 1:
            still_h, still_w = 1080, round(1080 * spec.aspect)
        else:
            still_w, still_h = 1200, round(1200 / spec.aspect)
    else:
        # Matches render_quilt()'s own internal window sizing exactly, so the
        # framing computed below is the framing the actual sweep renders at.
        still_h = spec.tile_height
        still_w = round(still_h * spec.aspect)

    p = pv.Plotter(off_screen=True)
    p.window_size = (still_w, still_h)
    subject.load(p)
    near, far, focal_distance = _frame_and_focus(p)
    print(
        f"  depth budget     near {near:.0f}, focal {focal_distance:.0f}, far {far:.0f} (scene units)"
    )
    print(
        f"  disparity        near {view_disparity(spec, RENDER_FOV, focal_distance, near):.1f} px, "
        f"far {view_disparity(spec, RENDER_FOV, focal_distance, far):.1f} px "
        "(adjacent-view shift; ~4-5px is the practical ceiling)"
    )

    if args.still:
        p.render()
        stem = args.out or f"renders/gallery/{args.subject.replace('-', '_')}"
        out = Path(f"{stem}.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        p.screenshot(str(out))
        p.close()
        print(f"  wrote {out}  ({still_w}x{still_h})")
        return 0

    started = time.time()
    # fov=None: _frame_and_focus() already locked the exact FOV/distance/focal
    # plane render_quilt would otherwise try to recompute from scratch.
    quilt = render_quilt(p, spec, fov=None)
    p.close()
    elapsed = time.time() - started

    stem = args.out or f"renders/quilts/{args.subject}"
    out = save_quilt(quilt, f"{stem}-preview" if args.preview else stem, spec)
    print(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if args.cast:
        from quiltwright.lfd import cast_quilt

        cast_quilt(out, spec)
        print("  cast to Looking Glass Bridge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
