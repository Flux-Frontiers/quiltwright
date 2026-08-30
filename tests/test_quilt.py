"""Tests for the renderer-agnostic quilt core (quiltwright.quilt)."""

import sys

from quiltwright import bridge, lfd, povray, quilt


def test_lfd_reexports_the_same_objects() -> None:
    """The lfd shim is an alias, not a copy -- fleet imports must not drift."""
    assert lfd.QuiltSpec is quilt.QuiltSpec
    assert lfd.QUILT_PRESETS is quilt.QUILT_PRESETS
    assert lfd.assemble_quilt is quilt.assemble_quilt
    assert lfd.save_quilt is quilt.save_quilt
    assert lfd.view_offsets is quilt.view_offsets
    assert lfd.view_disparity is quilt.view_disparity
    assert lfd.focal_distance_for_range is quilt.focal_distance_for_range
    assert lfd.sweep_spec is quilt.sweep_spec
    assert lfd.LITIHOLO_SWEEP is quilt.LITIHOLO_SWEEP
    assert lfd.cast_quilt is bridge.cast_quilt
    assert lfd.save_and_cast_quilt is bridge.save_and_cast_quilt
    assert lfd.pause_quilt is bridge.pause_quilt
    assert lfd.resume_quilt is bridge.resume_quilt
    assert lfd.stop_quilt is bridge.stop_quilt
    assert lfd.BRIDGE_URL == bridge.BRIDGE_URL
    assert povray.sweep_extent is quilt.sweep_extent


def test_importing_quilt_does_not_load_pyvista() -> None:
    """Core quilt geometry must stay importable without the viz extra."""
    sys.modules.pop("quiltwright.quilt", None)
    sys.modules.pop("pyvista", None)
    import quiltwright.quilt as q  # noqa: F401

    assert "pyvista" not in sys.modules


def test_importing_bridge_does_not_load_pyvista() -> None:
    """Bridge HTTP is stdlib; a core install must be able to cast a file."""
    sys.modules.pop("quiltwright.bridge", None)
    sys.modules.pop("pyvista", None)
    import quiltwright.bridge as b  # noqa: F401

    assert "pyvista" not in sys.modules


def test_package_lazy_map_points_at_the_new_homes() -> None:
    """from quiltwright import QuiltSpec must resolve quilt, not the PyVista backend."""
    import quiltwright

    assert quiltwright._LAZY["QuiltSpec"] == "quilt"
    assert quiltwright._LAZY["assemble_quilt"] == "quilt"
    assert quiltwright._LAZY["save_quilt"] == "quilt"
    assert quiltwright._LAZY["cast_quilt"] == "bridge"
    assert quiltwright._LAZY["save_and_cast_quilt"] == "bridge"
    assert quiltwright._LAZY["render_quilt"] == "lfd"
    assert quiltwright._LAZY["sweep_extent"] == "quilt"
    assert quiltwright._LAZY["window_shear"] == "quilt"
