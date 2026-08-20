"""Tests for the PyMOL bridge (quiltwright.pymol).

Most of this module is testable without PyMOL, and deliberately so: the
export is a short script handed to PyMOL, while everything done to what comes
back -- measuring it, recentring it, wrapping it in the ``pdb2pov -o``
contract -- is ordinary Python. Only the tests that need a real export are
gated on PyMOL being reachable.
"""

from __future__ import annotations

import math
import shutil

import pytest

from quiltwright.pymol import (
    REPRESENTATIONS,
    CartoonResult,
    PyMolNotAvailable,
    _count_faces,
    _literals,
    _measure,
    _wrap,
    available,
    cartoon_inc,
    pov_identifier,
)

# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stem, expected",
    [
        ("2omf", "_2omf"),
        ("2omf.inc", "_2omf"),
        ("out/1ema.pov", "_1ema"),
        ("hemoglobin", "hemoglobin"),
        ("4-hydroxy", "_4_hydroxy"),
        ("", "molecule"),
    ],
)
def test_identifiers_are_legal_povray(stem, expected):
    """POV-Ray identifiers may not begin with a digit, and most PDB IDs do.
    Kept byte-compatible with pypdb2pov's function of the same name so a
    cartoon and an atom scene of one structure declare the same name.
    """
    assert pov_identifier(stem) == expected


def test_no_declared_identifier_can_start_with_a_digit():
    text = _wrap(
        "mesh2 { }",
        identifier=pov_identifier("2omf"),
        centre=(0.0, 0.0, 0.0),
        radius=1.0,
        z_shift=0.0,
        meta={"atoms": 1},
        rep="cartoon",
        source="2omf.cif",
        faces=0,
    )
    for declared in text.split("#declare ")[1:]:
        assert not declared[0].isdigit(), declared[:20]


# ---------------------------------------------------------------------------
# Measuring what came back
# ---------------------------------------------------------------------------

MESH = """mesh2 {
  vertex_vectors { 4,
    <0, 0, -10>,
    <2, 0, -10>,
    <0, 2, -10>,
    <2, 2, -14>
  }
  face_indices { 2,
    <0, 1, 2>,
    <1, 3, 2>
  }
}"""


def test_the_camera_pull_back_is_undone_before_measuring():
    """PyMOL exports in camera space, so the geometry arrives pushed down -z
    by the pull-back distance.  Measuring without undoing it puts the centre
    hundreds of angstroms from where the object actually is.
    """
    centre, radius, count = _measure(MESH, z_shift=12.0)
    assert count == 4
    assert centre == pytest.approx((1.0, 1.0, 0.0))
    assert radius == pytest.approx(math.dist((0, 0, 2), (1, 1, 0)))


def test_measuring_uses_the_mesh_not_the_atoms():
    """A ribbon reaches beyond the atoms it was built from and a surface
    further still, so the radius has to come from the emitted vertices or a
    host scene frames the object too tightly.
    """
    centre, radius, _ = _measure(MESH, z_shift=12.0)
    corner = (2.0, 2.0, -2.0)
    assert radius >= math.dist(corner, centre) - 1e-9


@pytest.mark.parametrize("text", ["mesh2 { }", "sphere { <0,0,0>, 1 }"])
def test_a_mesh_with_no_vertices_is_an_error_not_a_silent_zero(text):
    with pytest.raises(ValueError):
        _measure(text, z_shift=0.0)


def test_faces_are_counted_across_every_block():
    assert _count_faces(MESH) == 2
    assert _count_faces(MESH + MESH) == 4
    assert _count_faces("sphere { <0,0,0>, 1 }") == 0


# ---------------------------------------------------------------------------
# The pdb2pov -o contract
# ---------------------------------------------------------------------------


def wrapped(**over):
    kwargs = dict(
        identifier="ompf_cartoon",
        centre=(3.0, -4.0, 5.0),
        radius=46.97,
        z_shift=500.0,
        meta={"atoms": 8481},
        rep="cartoon",
        source="2omf.cif.gz",
        faces=75792,
    )
    kwargs.update(over)
    return _wrap(MESH, **kwargs)


def test_the_include_declares_what_a_host_scene_reads():
    """`Vitrine_Mount(obj, obj_enclosing_radius)` is the whole interface, and
    it is pypdb2pov's, so a cartoon substitutes for an atom scene untouched.
    """
    text = wrapped()
    assert "#declare ompf_cartoon_enclosing_radius = 46.970;" in text
    assert "#declare ompf_cartoon_obj = union {" in text
    assert "#declare ompf_cartoon = object { ompf_cartoon_obj }" in text


def test_the_include_carries_no_camera_and_no_lights():
    """Object-only.  A camera here would be silently overridden by the one
    render_pov_quilt appends per view, with a warning nobody reads.
    """
    text = wrapped()
    # Statements, not the word: the header comment says "no camera, no
    # lights", which is the file explaining itself rather than declaring one.
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))
    for forbidden in ("camera", "light_source", "global_settings", "background"):
        assert forbidden not in code


def test_the_language_version_is_left_as_it_was_found():
    """An include that switches the host scene to 3.7 and does not switch it
    back changes how the rest of that scene parses.
    """
    text = wrapped()
    assert "#declare ompf_cartoon_pov_version = version;" in text
    assert text.rstrip().endswith("#version ompf_cartoon_pov_version;")


def test_the_geometry_is_recentred_by_translation():
    """Two translations, in order: undo the pull-back, then move the measured
    centre to the origin.  Rewriting 38,000 vertices in Python to save the
    ray-tracer one matrix would be a poor trade.
    """
    text = wrapped()
    assert "translate <0, 0, 500>" in text
    assert "translate <-3, 4, -5>" in text


# ---------------------------------------------------------------------------
# Argument handling
# ---------------------------------------------------------------------------


def test_an_unknown_representation_is_refused_before_pymol_is_started():
    """Cheap to check, and starting PyMOL to find out costs seconds."""
    with pytest.raises(ValueError, match="rep must be one of"):
        cartoon_inc("nowhere.pdb", "out.inc", rep="ballandstick")


def test_every_advertised_representation_is_accepted():
    assert set(REPRESENTATIONS) >= {"cartoon", "surface", "sticks", "spheres"}


def test_available_reports_how_pymol_can_be_reached():
    """The Homebrew build bundles its own interpreter, so the binary can
    exist while the import does not -- which is the whole reason the
    subprocess path exists.
    """
    got = available()
    assert got in {"module", "subprocess", None}
    if shutil.which("pymol") is None:
        try:
            import pymol  # noqa: F401
        except ImportError:
            assert got is None


def test_script_bindings_are_literals_not_interpolation():
    """The source path goes into a generated script, so it is bound as a
    repr'd literal rather than pasted in -- a path with a quote in it would
    otherwise end the string and run as code.
    """
    text = _literals(SOURCE="/tmp/it's here.cif", PULL_BACK=500.0, COLOR=None)
    assert "SOURCE = " in text
    assert "PULL_BACK = 500.0" in text
    assert "COLOR = None" in text
    namespace: dict = {}
    exec(compile(text, "<t>", "exec"), namespace)
    assert namespace["SOURCE"] == "/tmp/it's here.cif"


# ---------------------------------------------------------------------------
# With a real PyMOL
# ---------------------------------------------------------------------------

CRAMBIN = "/Users/egs/repos/pdb2pov/1CRN.pdb"

pymol_only = pytest.mark.skipif(
    available() is None, reason="no importable PyMOL and no pymol binary on PATH"
)


@pytest.mark.slow
@pymol_only
def test_a_real_export_honours_the_contract(tmp_path):
    """The end-to-end claim: a structure in, an include a vitrine can mount."""
    if not __import__("os").path.exists(CRAMBIN):
        pytest.skip("crambin not available on this machine")
    out = tmp_path / "crambin_cartoon.inc"
    result = cartoon_inc(CRAMBIN, out, assembly="")

    assert isinstance(result, CartoonResult)
    assert result.path == out
    assert result.faces > 0
    assert result.vertices > 0
    # Crambin is 46 residues; its cartoon fits comfortably inside 30 A.
    assert 5.0 < result.enclosing_radius < 30.0

    text = out.read_text()
    assert f"#declare {result.identifier}_enclosing_radius" in text
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))
    assert "camera" not in code


@pytest.mark.slow
@pymol_only
def test_coalescing_is_what_makes_the_export_usable(tmp_path):
    """Off, the export is PyMOL's one-mesh-per-triangle; on, it is one mesh.
    The difference is a factor of several in file size, re-parsed once per
    view.
    """
    if not __import__("os").path.exists(CRAMBIN):
        pytest.skip("crambin not available on this machine")
    plain = cartoon_inc(CRAMBIN, tmp_path / "plain.inc", assembly="", coalesce=False)
    merged = cartoon_inc(CRAMBIN, tmp_path / "merged.inc", assembly="", coalesce=True)

    assert plain.path.stat().st_size > merged.path.stat().st_size * 2
    assert merged.path.read_text().count("mesh2 {") == 1
    assert plain.path.read_text().count("mesh2 {") > 100
    # Same object either way.
    assert merged.enclosing_radius == pytest.approx(plain.enclosing_radius, rel=1e-6)


def test_a_missing_pymol_says_how_to_get_one(monkeypatch, tmp_path):
    """The failure a first-time user hits, so it has to carry the fix."""
    import quiltwright.pymol as mod

    monkeypatch.setattr(mod, "available", lambda: None)
    with pytest.raises(PyMolNotAvailable, match="brew install pymol"):
        mod._run_export("pass")
