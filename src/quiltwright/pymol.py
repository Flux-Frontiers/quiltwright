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

from .povgen import _named_list, _top_level_items, coalesce_mesh2, parse_color

__all__ = [
    "REPRESENTATIONS",
    "CartoonMeshResult",
    "CartoonResult",
    "PyMolNotAvailable",
    "available",
    "cartoon_inc",
    "cartoon_obj",
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

#: ``color="ss"`` colours: PyMOL-assigned secondary structure (``cmd.dss()``),
#: three flat colours -- helix, strand, everything else (loops and turns).
#: The RGBs matched back out of PyMOL's own POV-Ray export in
#: :func:`cartoon_obj` must land nearest to these three, so this is the
#: single source of truth for both the coloured-in structure and the labels
#: :func:`cartoon_obj` recovers afterwards.
SS_COLORS: dict[str, tuple[float, float, float]] = {
    "helix": (0.75, 0.25, 0.25),
    "strand": (0.85, 0.75, 0.15),
    "loop": (0.25, 0.55, 0.80),
}


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
elif COLOR == "ss":
    cmd.dss(sel)
    for _ss_name, _ss_rgb in SS_COLORS.items():
        cmd.set_color("qw_ss_" + _ss_name, list(_ss_rgb))
    cmd.color("qw_ss_helix", sel + " and ss H")
    cmd.color("qw_ss_strand", sel + " and ss S")
    cmd.color("qw_ss_loop", sel + " and not (ss H or ss S)")
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


def _run_export(script: str, *expected: str) -> None:
    """Run *script* inside PyMOL, in-process if possible.

    :param expected: Output paths the script is supposed to have written
        (``BODY_OUT``, ``META_OUT``).  Checked after the run because PyMOL's
        ``-cq`` batch mode logs a failed ``cmd.load``/``cmd.show``/etc. to
        stdout and keeps going rather than raising -- a bad path or selection
        exits ``0`` with nothing written, which without this check surfaces
        many lines away as a bare ``FileNotFoundError`` on the missing file.
    """
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
        missing = [p for p in expected if not Path(p).exists()]
        if missing:
            raise RuntimeError(f"pymol script ran but did not write {missing}")
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
        missing = [p for p in expected if not Path(p).exists()]
        if proc.returncode != 0 or missing:
            reason = (
                f"exited {proc.returncode}" if proc.returncode != 0 else f"did not write {missing}"
            )
            raise RuntimeError(f"pymol {reason}\n{proc.stdout}\n{proc.stderr}")
    finally:
        Path(path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# The POV-Ray side
# ---------------------------------------------------------------------------

_VERTEX_BLOCK = re.compile(r"vertex_vectors\s*\{\s*\d+\s*,(.*?)\}", re.S)
_VEC = re.compile(r"<\s*(-?[\d.eE+-]+)\s*,\s*(-?[\d.eE+-]+)\s*,\s*(-?[\d.eE+-]+)\s*>")
_FACE_BLOCK = re.compile(r"face_indices\s*\{\s*\d+\s*,(.*?)\}", re.S)
_PIGMENT_RGB = re.compile(r"rgb\s*<\s*([\d.eE+-]+)\s*,\s*([\d.eE+-]+)\s*,\s*([\d.eE+-]+)\s*>")
_FACE_TEXTURE_INDEX = re.compile(
    r"<\s*-?[\d.eE+-]+\s*,\s*-?[\d.eE+-]+\s*,\s*-?[\d.eE+-]+\s*>\s*,\s*(\d+)"
)


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


def _face_materials(
    mesh: str, color: str, n_faces: int
) -> tuple[list[str], dict[str, tuple[float, float, float]]]:
    """Recover per-face colour labels PyMOL baked into *mesh*'s ``texture_list``.

    :func:`cartoon_obj`'s only route to colour: PyMOL applied *color* before
    exporting (see ``_EXPORT_SCRIPT``), and ``cmd.get_povray()`` already
    baked the result into one POV-Ray texture per distinct colour plus one
    texture index per face -- this reads that back rather than recomputing
    anything, so it reports exactly what PyMOL applied.

    :param mesh: The coalesced mesh2 text.
    :param color: ``"ss"`` for :data:`SS_COLORS`, or any other flat PyMOL
        colour name / ``"#rrggbb"``.
    :param n_faces: Faces in the mesh, to size the fallback used when PyMOL
        omits per-face texture indices (only happens with a single baked
        colour, i.e. *color* was flat rather than ``"ss"``).
    :return: ``(labels, materials)`` -- one label per face in mesh order, and
        the label -> colour mapping actually used (only labels with at least
        one face are present, since e.g. an all-beta structure bakes no
        ``"helix"`` texture at all).
    """
    targets = SS_COLORS if color == "ss" else {"flat": parse_color(color)}
    names = list(targets)

    baked: list[tuple[float, float, float]] = []
    texture_list = _named_list(mesh, "texture_list")
    if texture_list is not None:
        for item in _top_level_items(texture_list)[1:]:  # [0] is the item count
            found = _PIGMENT_RGB.search(item)
            if found:
                r, g, b = (float(v) for v in found.groups())
                baked.append((r, g, b))
            else:
                baked.append((1.0, 1.0, 1.0))
    if not baked:
        baked = [next(iter(targets.values()))]

    def nearest(rgb: tuple[float, float, float]) -> str:
        return min(
            names, key=lambda n: sum((a - b) ** 2 for a, b in zip(rgb, targets[n], strict=True))
        )

    texture_labels = [nearest(rgb) for rgb in baked]

    face_block = _FACE_BLOCK.search(mesh)
    tex_idx = _FACE_TEXTURE_INDEX.findall(face_block.group(1)) if face_block else []
    if len(tex_idx) != n_faces:
        # A single baked texture: POV-Ray omits per-face indices entirely.
        tex_idx = ["0"] * n_faces

    labels = [texture_labels[int(i)] for i in tex_idx]
    used = {name: targets[name] for name in names if name in labels}
    return labels, used


#: ``finish="metallic"``.  The vitrine's own brass recipe
#: (``pov-scenes/vitrine/vitrine.inc``): low diffuse and high brilliance keep
#: the body dark so the highlights carry the form, ``metallic`` tints the
#: highlight and reflection with the pigment instead of leaving them white,
#: and the bump normal breaks up a flat face's highlight as the view sweeps
#: -- all three are what read as metal rather than as coloured plastic. The
#: pigment itself is whatever colour PyMOL already baked in (spectrum, ss,
#: or flat), unlike the vitrine's brass which is always yellow.
_METALLIC_FINISH = (
    "normal { bumps 0.018 scale 0.09 } "
    "finish { ambient 0.11 diffuse 0.44 brilliance 3.0 metallic "
    "specular 1.0 roughness 0.0035 phong 0.45 phong_size 55 "
    "reflection { 0.20, 0.64 metallic } }"
)

_MESH_TEXTURE = re.compile(
    r"texture\s*\{\s*pigment\s*\{\s*color\s+rgb\s*<\s*([^>]+?)\s*>\s*\}\s*\}"
)


def _retexture(mesh: str, finish: str) -> str:
    """Rewrite every baked ``texture { pigment{...} }`` in *mesh* for *finish*.

    PyMOL's export bakes one flat ``pigment { color rgb<r,g,b> }`` texture per
    distinct colour (see :func:`_face_materials`) with no ``finish`` of its
    own, so POV-Ray falls back to its plain default finish -- flat and
    plasticky next to the vitrine's own brass. This keeps each texture's
    baked hue and adds the finish on top, so ``color="ss"``'s three hues come
    back out as three metals rather than one shared material.

    :param mesh: The coalesced mesh2 text.
    :param finish: ``"metallic"``. ``"normal"`` is not accepted here --
        callers skip this function entirely for it.
    :return: The rewritten mesh.
    """
    if finish != "metallic":
        raise ValueError(f"finish must be 'metallic', got {finish!r}")

    def replace(match: re.Match[str]) -> str:
        return f"texture {{ pigment{{color rgb<{match.group(1)}>}} {_METALLIC_FINISH} }}"

    return _MESH_TEXTURE.sub(replace, mesh)


def cartoon_inc(
    source: str | Path,
    out: str | Path,
    *,
    rep: str = "cartoon",
    color: str | None = "spectrum",
    finish: str = "normal",
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
    :param color: ``"spectrum"`` for a rainbow ramp along the chain,
        ``"ss"`` for :data:`SS_COLORS` by secondary structure (``cmd.dss()``
        then one flat colour each for helix, strand and loop -- the
        conventional three-colour cartoon), any PyMOL colour name for a flat
        colour, or ``None`` to keep PyMOL's default colouring.
    :param finish: ``"normal"`` for whatever finish PyMOL's own baked
        pigments get by default (POV-Ray's plain default -- flat, no
        reflection), or ``"metallic"`` for the vitrine's own brass recipe
        kept but tinted with each baked colour instead of brass yellow.
        Applied per baked colour, so ``color="ss"`` comes out as three
        metals, not one shared material.
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
    :raises ValueError: If *rep* or *finish* is not a recognised value.
    """
    if rep not in REPRESENTATIONS:
        raise ValueError(f"rep must be one of {REPRESENTATIONS}, got {rep!r}")
    if finish not in ("normal", "metallic"):
        raise ValueError(f"finish must be 'normal' or 'metallic', got {finish!r}")

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
                SS_COLORS=SS_COLORS,
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
        _run_export(script, body_out, meta_out)
        body = Path(body_out).read_text()
        meta = json.loads(Path(meta_out).read_text())

    backend = available() or "subprocess"
    mesh = coalesce_mesh2(body) if coalesce else body

    if "mesh2" in mesh:
        centre, radius, vertices = _measure(mesh, meta["pull_back"])
        faces = _count_faces(mesh)
        if finish != "normal":
            mesh = _retexture(mesh, finish)
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


@dataclass(frozen=True)
class CartoonMeshResult:
    """What :func:`cartoon_obj` wrote.

    :param path: The ``.obj`` written.
    :param enclosing_radius: Radius of the sphere about the origin that
        contains the geometry, in angstroms -- identical to what
        :func:`cartoon_inc` would report for the same PyMOL export, since
        both are measured from the same mesh before either the POV
        ``translate`` trick or this function's coordinate flip is applied.
    :param vertices: Vertices in the emitted mesh, after deduplication.
    :param faces: Triangles in the emitted mesh.
    :param backend: ``"module"`` or ``"subprocess"``.
    """

    path: Path
    enclosing_radius: float
    vertices: int
    faces: int
    backend: str


def cartoon_obj(
    source: str | Path,
    out: str | Path,
    *,
    rep: str = "cartoon",
    color: str | None = None,
    roughness: float = 0.3,
    selection: str = "polymer",
    assembly: str = "1",
    surface_quality: int | None = None,
) -> CartoonMeshResult:
    """Export a structure as a Wavefront OBJ -- the mesh twin of :func:`cartoon_inc`.

    Runs the identical PyMOL export (same representation, selection and
    assembly) and coalesces it the same way, but writes the triangles as a
    plain ``.obj`` instead of a POV-Ray include, for feeding the same
    subject to :mod:`quiltwright.cycles` instead of :mod:`quiltwright.povray`.
    This is what makes a "which backend wins on a mesh this size" comparison
    honest: both start from the exact same PyMOL triangulation, not two
    independently-modelled scenes.

    Geometry is centred on the origin exactly as :func:`cartoon_inc` centres
    it (undoing PyMOL's camera pull-back, then the same bounding-box
    recentring), so the enclosing radius here matches what that function
    would report for the same export.

    **The coordinate flip.**  ``cmd.get_povray()`` emits directly in
    POV-Ray's left-handed convention -- :func:`cartoon_inc` passes it through
    unchanged, because POV-Ray is exactly where it is going.  An OBJ headed
    for :mod:`quiltwright.cycles` (right-handed, +z up, same as everything
    else in this package) needs the same reflection :func:`to_pov` applies in
    the other direction: negate *z*, and reverse each face's winding to
    compensate, or the mesh imports with its normals -- and every backface
    culling decision Cycles makes -- turned inside out.  This mirrors
    :class:`~quiltwright.povgen.Mesh2`'s own ``wind()`` step exactly, just
    run backwards.  Verified against a real PyMOL export: also see
    ``quiltwright.cycles``'s ``obj`` importer, which must be told the file is
    already in this package's +z-up convention, or Blender's default
    Y-up-to-Z-up remap for Wavefront files turns this mesh 90 degrees against
    a camera framed for it.

    **Colour.**  Plain OBJ carries none, so by default (``color=None``) this
    writes geometry only, exactly as before.  Passing a colour bakes it into
    a companion ``.mtl`` instead: ``color="ss"`` runs ``cmd.dss()`` and
    splits the mesh into the three flat colours of :data:`SS_COLORS` (helix,
    strand, loop -- the conventional three-colour cartoon), and any other
    PyMOL colour name or ``"#rrggbb"`` paints the whole thing one flat
    colour.  Either way the colour PyMOL baked into the raw mesh is read back
    out of its own texture list rather than recomputed, so it is exactly what
    PyMOL applied.  ``color="spectrum"`` is rejected: a rainbow ramp is one
    colour per residue, which would mean one OBJ material per residue --
    unworkable, and exactly the case :func:`cartoon_inc` and the POV-Ray
    backend exist for.

    :param source: Anything PyMOL can load -- ``.pdb``, ``.cif``, ``.cif.gz``.
    :param out: Path of the ``.obj`` to write.  A companion ``.mtl`` of the
        same stem is written alongside it when *color* is given.
    :param rep: One of :data:`REPRESENTATIONS`.  Only representations that
        export as mesh triangles are usable here; ``sticks`` and ``spheres``
        raise, since they carry no vertex list to convert (use
        :func:`cartoon_inc` and quiltwright's POV-Ray backend for those, or
        author them directly as :class:`~quiltwright.povgen.Sphere` /
        :class:`~quiltwright.povgen.Cylinder` primitives for either backend).
    :param color: ``None`` for a colourless mesh (default), ``"ss"`` for
        :data:`SS_COLORS` by secondary structure, or any flat PyMOL colour
        name / ``"#rrggbb"``.  ``"spectrum"`` raises -- see above.
    :param roughness: Blender ``Pr`` (roughness) written into the ``.mtl``
        for every material, when *color* is given.  Lower is glossier;
        Blender's own default is ``0.5``, which reads as flat and plasticky
        next to POV-Ray's finish -- this is what "more interesting material
        properties" means in practice for a Cycles render.
    :param selection: PyMOL selection to show; ``"polymer"`` drops waters and
        ligands.
    :param assembly: Biological assembly to load; ``"1"`` is the biological
        unit.
    :param surface_quality: PyMOL's ``surface_quality``, for ``rep="surface"``.
    :return: A :class:`CartoonMeshResult`.
    :raises PyMolNotAvailable: If PyMOL cannot be reached at all.
    :raises ValueError: If *rep* is not a known representation, *color* is
        ``"spectrum"``, or the export produces native POV-Ray primitives
        rather than mesh triangles.
    """
    if rep not in REPRESENTATIONS:
        raise ValueError(f"rep must be one of {REPRESENTATIONS}, got {rep!r}")
    if color == "spectrum":
        raise ValueError(
            "color='spectrum' is not supported by cartoon_obj() -- a rainbow "
            "ramp is one colour per residue, which OBJ has no reasonable way "
            "to carry as materials. Use color='ss', a flat colour, or "
            "cartoon_inc() with the POV-Ray backend for a spectrum."
        )

    out = Path(out)
    with tempfile.TemporaryDirectory() as work:
        body_out = str(Path(work) / "body.pov")
        meta_out = str(Path(work) / "meta.json")
        script = (
            _literals(
                SOURCE=str(Path(source).resolve()),
                REP=rep,
                COLOR=color,
                SS_COLORS=SS_COLORS,
                SELECTION=selection,
                ASSEMBLY=assembly,
                TRANSPARENCY=0.0,
                SURFACE_QUALITY=surface_quality,
                PULL_BACK=_PULL_BACK,
                BODY_OUT=body_out,
                META_OUT=meta_out,
            )
            + _EXPORT_SCRIPT
        )
        _run_export(script, body_out, meta_out)
        body = Path(body_out).read_text()
        meta = json.loads(Path(meta_out).read_text())

    mesh = coalesce_mesh2(body)
    if "mesh2" not in mesh:
        raise ValueError(
            f"rep={rep!r} exports as native POV-Ray primitives, not mesh "
            "triangles, so there is nothing for cartoon_obj() to convert -- "
            "use cartoon_inc() and the POV-Ray backend for this rep, or "
            "author the same primitives directly for either backend"
        )

    centre, radius, _ = _measure(mesh, meta["pull_back"])
    cx, cy, cz = centre
    vertices = [
        (float(x) - cx, float(y) - cy, -(float(z) + meta["pull_back"] - cz))
        for block in _VERTEX_BLOCK.finditer(mesh)
        for x, y, z in _VEC.findall(block.group(1))
    ]
    faces = [
        (int(a), int(c), int(b))  # winding reversed to match the z flip above
        for block in _FACE_BLOCK.finditer(mesh)
        for a, b, c in _VEC.findall(block.group(1))
    ]

    labels: list[str] = []
    materials: dict[str, tuple[float, float, float]] = {}
    if color is not None:
        labels, materials = _face_materials(mesh, color, len(faces))

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        fh.write(f"# {out.stem} -- {rep}, via quiltwright.pymol.cartoon_obj\n")
        fh.write(f"# {meta['atoms']} atoms, {len(vertices)} vertices, {len(faces)} faces\n")
        if materials:
            fh.write(f"mtllib {out.with_suffix('.mtl').name}\n")
        for x, y, z in vertices:
            fh.write(f"v {x:.6g} {y:.6g} {z:.6g}\n")
        if materials:
            for name in materials:
                fh.write(f"usemtl {name}\n")
                for (a, b, c), label in zip(faces, labels, strict=True):
                    if label == name:
                        fh.write(f"f {a + 1} {b + 1} {c + 1}\n")
        else:
            for a, b, c in faces:
                fh.write(f"f {a + 1} {b + 1} {c + 1}\n")

    if materials:
        with out.with_suffix(".mtl").open("w") as fh:
            for name, (r, g, b) in materials.items():
                fh.write(f"newmtl {name}\nKd {r:.4f} {g:.4f} {b:.4f}\nPr {roughness:.3f}\n\n")

    return CartoonMeshResult(
        path=out,
        enclosing_radius=radius,
        vertices=len(vertices),
        faces=len(faces),
        backend=available() or "subprocess",
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
