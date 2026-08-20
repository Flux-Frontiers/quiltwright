"""
Molecular cartoons and surfaces, via headless PyMOL
===================================================

The representation :mod:`pypdb2pov` cannot write.  ``pdb2pov`` has emitted
atoms and bonds since 1993 -- spheres at van der Waals, covalent or CPK radii,
optionally with bond cylinders -- and nothing else.  There is no ribbon in it
and never was.

Yet ``pov-scenes/porin/3porin.inc`` is a Richardson cartoon, because it was
never ``pdb2pov`` output: its header says ``converted to POVRay V2.2 by
WCVT2POV V2.7``, so the ribbons came from some 1993-94 mesh exporter whose
output survives in no repository.  The most striking image in the archive is
therefore the one representation the pipeline could not regenerate.  This
module regenerates it, from a PDB ID and a command line.

**The contract is ``pdb2pov -o``'s, deliberately.**  What comes out is an
object-only ``.inc``: geometry centred on the origin, a
``#declare <name>_enclosing_radius`` beside it, no camera and no lights.  That
is the same shape :mod:`pypdb2pov` writes, which is what makes a cartoon drop
into an existing scene unchanged::

    #include "ompf_cartoon.inc"
    Vitrine_Mount(ompf_cartoon, ompf_cartoon_enclosing_radius)

``Vitrine_Mount`` asks nothing about how the geometry was produced, and
neither :func:`~quiltwright.povray.render_pov_quilt` nor
:class:`~quiltwright.povray.PovCamera` needs any change to render it.

**Why the export needs post-processing.**  ``cmd.get_povray()`` emits one
``mesh2`` object per triangle, each carrying its own three-entry vertex,
normal and texture list.  Nothing is shared.  A GFP cartoon arrives as 17,140
single-face meshes and 9.3 MB; an OmpF porin trimer as 75,792 and 41.3 MB; an
alpha-hemolysin heptamer as 152,596 and 83.1 MB -- and a quilt re-parses that
48 times.  :func:`~quiltwright.povgen.coalesce_mesh2` merges them into one
mesh with shared lists, which is most of what this module does with what
PyMOL hands it.

**PyMOL is optional, and stays optional.**  Open-source PyMOL is not
OSI-licensed -- Homebrew declares it ``LicenseRef-Homebrew-cannot-represent``
-- while quiltwright is BSD-3, so it can never be a hard dependency.  It is
also awkward to reach: PyPI has only ever published alphas of
``pymol-open-source``, and the Homebrew build bundles its own interpreter that
no project virtualenv can import from.  So this module drives PyMOL
**in-process when it can import it and by subprocess when it cannot**, chooses
automatically, and reports which through :func:`available`.

Typical use::

    from quiltwright.pymol import cartoon_inc

    result = cartoon_inc("2omf.cif.gz", "ompf_cartoon.inc")
    print(result.enclosing_radius, result.faces)
"""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .povgen import coalesce_mesh2

__all__ = [
    "REPRESENTATIONS",
    "CartoonResult",
    "PyMolNotAvailable",
    "available",
    "cartoon_inc",
    "pov_identifier",
]

#: Representations worth asking for.  ``sticks`` and ``spheres`` duplicate
#: ``pdb2pov -b`` and ``-v`` and are here for completeness rather than because
#: they are the better route -- the bundled ``atoms2.inc`` textures are the
#: house look, and PyMOL silently drops sphere transparency on export.
REPRESENTATIONS = ("cartoon", "surface", "ribbon", "sticks", "spheres")

#: Distance PyMOL is asked to stand the camera back before exporting.  Any
#: value works; the geometry is recentred afterwards regardless.  It only has
#: to clear the structure so nothing lands behind the eye.
_PULL_BACK = 500.0


class PyMolNotAvailable(RuntimeError):
    """Raised when neither an importable PyMOL nor a ``pymol`` binary exists."""


@dataclass(frozen=True)
class CartoonResult:
    """What :func:`cartoon_inc` wrote.

    :param path: The ``.inc`` written.
    :param identifier: The POV-Ray identifier declared in it.
    :param enclosing_radius: Radius of the sphere about the origin that
        contains the geometry, in angstroms.  Also declared in the file as
        ``<identifier>_enclosing_radius``, which is what a host scene should
        read rather than this.
    :param centre: The model-space point moved to the origin, in angstroms.
    :param vertices: Vertices in the emitted mesh, after deduplication.
    :param faces: Triangles in the emitted mesh.
    :param rep: The representation exported.
    :param backend: ``"module"`` or ``"subprocess"``.
    """

    path: Path
    identifier: str
    enclosing_radius: float
    centre: tuple[float, float, float]
    vertices: int
    faces: int
    rep: str
    backend: str


def pov_identifier(stem: str, fallback: str = "molecule") -> str:
    """Derive a legal POV-Ray identifier from an output path.

    POV identifiers are alphanumerics and underscores and may not begin with a
    digit, so ``2omf`` -- the obvious name for a structure -- becomes
    ``_2omf``.  Kept deliberately identical to ``pypdb2pov``'s function of the
    same name, so a cartoon and an atom scene of the same structure declare
    the same identifier and a host scene can swap one for the other.

    :param stem: Output path or bare stem.
    :param fallback: Used when *stem* has no usable characters.
    :return: A legal identifier.
    """
    base = Path(stem).name
    for suffix in (".pov", ".inc"):
        if base.lower().endswith(suffix):
            base = base[: -len(suffix)]
            break
    if not base:
        base = fallback
    if base[0].isdigit():
        base = "_" + base
    return "".join(ch if (ch.isalnum() and ch.isascii()) or ch == "_" else "_" for ch in base)


def available() -> str | None:
    """How PyMOL can be reached from here, if at all.

    :return: ``"module"`` if ``import pymol`` works in this interpreter,
        ``"subprocess"`` if only a ``pymol`` binary is on ``PATH``, else
        ``None``.  The distinction matters because the common install --
        Homebrew -- bundles its own interpreter, so the binary exists while
        the import does not.
    """
    try:
        import pymol  # noqa: F401  # ty: ignore[unresolved-import]
    except ImportError:
        pass
    else:
        return "module"
    return "subprocess" if shutil.which("pymol") else None


# ---------------------------------------------------------------------------
# The PyMOL side
# ---------------------------------------------------------------------------

#: Script run inside PyMOL.  It writes the raw export to one file and its
#: metadata to another, and does no post-processing: everything that can be
#: done in a normal interpreter is done there, where it can be tested without
#: PyMOL present.
_EXPORT_SCRIPT = """
import json
from pymol import cmd

cmd.set("assembly", ASSEMBLY)
cmd.load(SOURCE, "subject")
cmd.hide("everything")
sel = SELECTION if SELECTION else "subject"
cmd.show(REP, sel)
if COLOR == "spectrum":
    cmd.spectrum("count", "rainbow", sel + " and name CA")
elif COLOR:
    cmd.color(COLOR, sel)
if SURFACE_QUALITY is not None:
    cmd.set("surface_quality", SURFACE_QUALITY)
if TRANSPARENCY:
    cmd.set("cartoon_transparency", TRANSPARENCY)
    cmd.set("transparency", TRANSPARENCY)

# Normalise the view before exporting.  get_povray() writes vertices in
# *camera* space, so with an arbitrary view the geometry arrives rotated and
# offset by a matrix that then has to be inverted.  Forcing identity rotation
# and a pure z pull-back makes camera space a plain translation of the model,
# which the caller undoes with one subtraction -- no matrix inversion, and no
# opportunity to get the chirality wrong.
lo, hi = cmd.get_extent(sel)
centre = [(a + b) / 2.0 for a, b in zip(lo, hi)]
cmd.set_view((
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0,
    0.0, 0.0, -PULL_BACK,
    centre[0], centre[1], centre[2],
    1.0, PULL_BACK * 2.0, 0.0,
))

header, body = cmd.get_povray()
with open(BODY_OUT, "w") as fh:
    fh.write(body)
with open(META_OUT, "w") as fh:
    json.dump({
        "centre": centre,
        "extent": [list(lo), list(hi)],
        "atoms": cmd.count_atoms(sel),
        "pull_back": PULL_BACK,
    }, fh)
"""


def _literals(**values: object) -> str:
    """Bind the script's upper-case names as Python literals."""
    return "".join(f"{k} = {v!r}\n" for k, v in values.items())


def _run_export(script: str) -> None:
    """Run *script* inside PyMOL, in-process if possible."""
    backend = available()
    if backend is None:
        raise PyMolNotAvailable(
            "PyMOL is not importable and no `pymol` binary is on PATH.\n"
            "  brew install pymol                          # macOS, stable\n"
            "  conda install -c conda-forge pymol-open-source\n"
            "  pip install --pre pymol-open-source         # alphas only"
        )
    if backend == "module":
        # A fresh namespace, so a caller's globals cannot leak into the script
        # and the script's names cannot leak back out.
        exec(compile(script, "<pymol-export>", "exec"), {})
        return

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(script)
        path = fh.name
    try:
        proc = subprocess.run(
            ["pymol", "-cq", path],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"pymol exited {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
    finally:
        Path(path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# The POV-Ray side
# ---------------------------------------------------------------------------

_VERTEX_BLOCK = re.compile(r"vertex_vectors\s*\{\s*\d+\s*,(.*?)\}", re.S)
_VEC = re.compile(r"<\s*(-?[\d.eE+-]+)\s*,\s*(-?[\d.eE+-]+)\s*,\s*(-?[\d.eE+-]+)\s*>")


def _measure(mesh: str, z_shift: float) -> tuple[tuple[float, float, float], float, int]:
    """Centre and enclosing radius of a coalesced mesh, after the z shift.

    Measured from the emitted vertices rather than from PyMOL's atom extents:
    a cartoon's ribbon reaches beyond the atoms it was built from, and a
    surface reaches further still, so atom extents would under-report the
    radius a host scene uses to frame the object.

    :param mesh: The mesh text.
    :param z_shift: Added to every *z* before measuring, undoing the camera
        pull-back.
    :return: ``(centre, radius, vertex_count)`` in model space.
    """
    # Every block, not just the first.  Coalesced output has exactly one, but
    # with coalesce=False this is PyMOL's one-mesh-per-triangle export, and
    # measuring only the first block reports the radius of a single triangle
    # -- a wrong answer that looks plausible and frames the object at a
    # fraction of its size.
    points = [
        (float(x), float(y), float(z) + z_shift)
        for block in _VERTEX_BLOCK.finditer(mesh)
        for x, y, z in _VEC.findall(block.group(1))
    ]
    if not points:
        raise ValueError("no vertices found in the exported mesh")

    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    centre = ((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, (lo[2] + hi[2]) / 2.0)
    radius = max(math.dist(p, centre) for p in points)
    return centre, radius, len(points)


def cartoon_inc(
    source: str | Path,
    out: str | Path,
    *,
    rep: str = "cartoon",
    color: str | None = "spectrum",
    selection: str = "polymer",
    assembly: str = "1",
    transparency: float = 0.0,
    surface_quality: int | None = None,
    coalesce: bool = True,
    name: str | None = None,
) -> CartoonResult:
    """Export a structure as a POV-Ray object-only include.

    :param source: Anything PyMOL can load -- ``.pdb``, ``.cif``, ``.cif.gz``.
    :param out: Path of the ``.inc`` to write.
    :param rep: One of :data:`REPRESENTATIONS`.
    :param color: ``"spectrum"`` for a rainbow ramp along the chain, any
        PyMOL colour name for a flat colour, or ``None`` to keep PyMOL's
        default colouring.
    :param selection: PyMOL selection to show; ``"polymer"`` drops waters and
        ligands, which is almost always what a cartoon wants.
    :param assembly: Biological assembly to load.  ``"1"`` is the biological
        unit -- ferritin arrives as a 24-mer rather than as a 24th of itself.
        Pass ``""`` for the asymmetric unit.
    :param transparency: 0 to 1.  Exports as POV-Ray ``transmit``, which is
        flat see-through rather than refractive.
    :param surface_quality: PyMOL's ``surface_quality``; lower is coarser.
        Worth setting negative for a large ``rep="surface"``, which otherwise
        runs to millions of triangles.
    :param coalesce: Merge the per-triangle meshes.  Leave it on unless you
        are comparing against the raw export.
    :param name: POV-Ray identifier to declare.  Defaults to *out*'s stem, put
        through :func:`pov_identifier`.
    :return: A :class:`CartoonResult`.
    :raises PyMolNotAvailable: If PyMOL cannot be reached at all.
    :raises ValueError: If *rep* is not a known representation.
    """
    if rep not in REPRESENTATIONS:
        raise ValueError(f"rep must be one of {REPRESENTATIONS}, got {rep!r}")

    out = Path(out)
    identifier = pov_identifier(name if name is not None else out.stem)

    with tempfile.TemporaryDirectory() as work:
        body_out = str(Path(work) / "body.pov")
        meta_out = str(Path(work) / "meta.json")
        script = (
            _literals(
                SOURCE=str(Path(source).resolve()),
                REP=rep,
                COLOR=color,
                SELECTION=selection,
                ASSEMBLY=assembly,
                TRANSPARENCY=float(transparency),
                SURFACE_QUALITY=surface_quality,
                PULL_BACK=_PULL_BACK,
                BODY_OUT=body_out,
                META_OUT=meta_out,
            )
            + _EXPORT_SCRIPT
        )
        _run_export(script)
        body = Path(body_out).read_text()
        meta = json.loads(Path(meta_out).read_text())

    backend = available() or "subprocess"
    mesh = coalesce_mesh2(body) if coalesce else body

    if "mesh2" in mesh:
        centre, radius, vertices = _measure(mesh, meta["pull_back"])
        faces = _count_faces(mesh)
    else:
        # sticks and spheres export as native primitives, which carry no
        # vertex list to measure.  Fall back to the atom extents, which are
        # exact for those since a sphere's extent is its centre plus radius.
        lo, hi = meta["extent"]
        centre = tuple((a + b) / 2.0 for a, b in zip(lo, hi, strict=True))
        radius = max(math.dist(corner, centre) for corner in (lo, hi))
        vertices = faces = 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        _wrap(
            mesh,
            identifier=identifier,
            centre=centre,
            radius=radius,
            z_shift=meta["pull_back"],
            meta=meta,
            rep=rep,
            source=Path(source).name,
            faces=faces,
        )
    )
    return CartoonResult(
        path=out,
        identifier=identifier,
        enclosing_radius=radius,
        centre=centre,
        vertices=vertices,
        faces=faces,
        rep=rep,
        backend=backend,
    )


def _count_faces(mesh: str) -> int:
    """Faces declared across every ``face_indices`` block in *mesh*."""
    return sum(int(n) for n in re.findall(r"face_indices\s*\{\s*(\d+)\s*,", mesh))


def _wrap(
    mesh: str,
    *,
    identifier: str,
    centre: tuple[float, float, float],
    radius: float,
    z_shift: float,
    meta: dict,
    rep: str,
    source: str,
    faces: int,
) -> str:
    """Wrap the geometry as an object-only include.

    The recentring is a POV-Ray ``translate`` rather than a rewrite of every
    vertex: it says what happened where a reader can see it, and moving 38,000
    vertices in Python to save the ray-tracer one matrix would be a poor
    trade.
    """
    cx, cy, cz = centre
    return f"""//
// Prepared by quiltwright.pymol from {source} -- {rep}
//
//\tAtoms: {meta["atoms"]}
//\tFaces: {faces}
//\tEnclosing Sphere: {radius:.3f}
//
// Object only: no camera, no lights, centred on the origin -- the same
// contract `pdb2pov -o` writes, so this drops into a scene beside one.
//

#declare {identifier}_pov_version = version;
#version 3.7;

#declare {identifier}_enclosing_radius = {radius:.3f};

#declare {identifier}_obj = union {{
{mesh}
  // Undo PyMOL's camera pull-back, then centre the geometry on the origin.
  translate <0, 0, {z_shift:.6g}>
  translate <{-cx:.6g}, {-cy:.6g}, {-cz:.6g}>
}}

#declare {identifier} = object {{ {identifier}_obj }}

#version {identifier}_pov_version;
"""
