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

Camera framing here is a generic 3/4 orbit (``reset_camera()`` then a fixed
elevation/azimuth nudge) rather than the measured depth budget the POV-Ray
scripts use — these are exploratory renders, not tuned deliverables. If a
result ghosts, narrow ``--view-cone`` or check the disparity formula in
``docs/povray.md``.

Usage::

    python scripts/render_pyvista_hologram.py st-helens --preview
    python scripts/render_pyvista_hologram.py mouse-brain --resolution 50
    python scripts/render_pyvista_hologram.py brain --device portrait --cast

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from quiltwright.lfd import QUILT_PRESETS, QuiltSpec, render_quilt, save_quilt

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
#: template — a real volumetric atlas built from 1,675 C57BL/6J mice. Plain
#: NRRD over HTTP, no API key or AllenSDK dependency. See
#: docs/pyvista-datasets.md for the annotation (region-labeled) variant.
ALLEN_CCF_TEMPLATE_URL = (
    "http://download.alleninstitute.org/informatics-archive/current-release/"
    "mouse_ccf/average_template/average_template_{resolution}.nrrd"
)
ALLEN_CCF_CACHE = Path.home() / ".cache" / "quiltwright" / "allen_ccf"


def _download_allen_template(resolution: int) -> Path:
    """Fetch (and cache) an Allen CCFv3 average-template volume.

    :param resolution: Isotropic voxel size in micrometres: 10, 25, 50, or 100.
        Finer resolutions are dramatically larger; 50 is a reasonable default.
    :return: Local path to the cached ``.nrrd`` file.
    """
    if resolution not in (10, 25, 50, 100):
        raise ValueError(f"resolution must be one of 10/25/50/100, got {resolution}")
    ALLEN_CCF_CACHE.mkdir(parents=True, exist_ok=True)
    dest = ALLEN_CCF_CACHE / f"average_template_{resolution}.nrrd"
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


def _load_st_helens(p: pv.Plotter) -> None:
    """Mt. St. Helens post-eruption DEM, warped into 3-D relief."""
    dem = examples.download_st_helens()
    surf = dem.warp_by_scalar("Elevation", factor=2.0)
    p.add_mesh(surf, cmap="gist_earth", show_scalar_bar=False)
    _orbit_camera(p)


def _load_damavand(p: pv.Plotter) -> None:
    """Mt. Damavand (Iran) volumetric geophysical data."""
    vol = examples.download_damavand_volcano()
    p.add_volume(vol, cmap="viridis", opacity="sigmoid", show_scalar_bar=False)
    _orbit_camera(p)


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
        "Mt. Damavand volumetric geophysical data (examples.download_damavand_volcano)",
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
        "--out", default=None, help="output stem; defaults to renders/quilts/<subject>"
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
    if args.preview:
        spec = replace(spec, quilt_width=spec.quilt_width // 4, quilt_height=spec.quilt_height // 4)

    print(f"{args.subject} hologram -> {device}{' (preview)' if args.preview else ''}")
    print(f"  {about}")
    print(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}, cone {spec.view_cone:.0f} deg"
    )

    p = pv.Plotter(off_screen=True)
    subject.load(p)

    started = time.time()
    quilt = render_quilt(p, spec)
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
