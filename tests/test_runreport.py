"""
Tests for :mod:`quiltwright.runreport`.

The point of a run report is that it is *evidence*, so the properties worth
pinning are the ones that would make it lie: a digest that does not match the
file, a provenance header that silently drops to ``unknown`` without saying
so, or a dirty tree reported as clean.

The environment-probing helpers are exercised against whatever box the suite
runs on rather than mocked. That is deliberate -- their contract is "never
raise, always return something printable", and the way they break is by
raising on a machine that lacks `sysctl`, `git` or POV-Ray, which a mock
cannot catch.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import hashlib
import subprocess

import pytest

from quiltwright.runreport import (
    RunReport,
    git_info,
    machine_description,
    povray_version,
    sha256,
)

# ---------------------------------------------------------------------------
# Probes: never raise, always printable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("probe", [machine_description, povray_version])
def test_probes_return_a_nonempty_string(probe):
    """Every provenance probe degrades to a value rather than raising."""
    value = probe()
    assert isinstance(value, str)
    assert value


def test_povray_version_of_a_missing_binary_is_unknown():
    """A binary that is not on PATH reports ``unknown``, not a traceback."""
    assert povray_version("definitely-not-a-real-povray-binary") == "unknown"


def test_git_info_has_every_key_populated():
    """All five fields are present and non-empty, even outside a repo."""
    info = git_info()
    assert set(info) == {"hash", "branch", "date", "subject", "dirty"}
    assert all(info.values())
    assert info["dirty"] in {"yes", "no"}


def test_git_info_outside_a_repository_is_unknown(tmp_path):
    """Off a working copy the fields fall back rather than blowing up."""
    info = git_info(tmp_path)
    assert info["hash"] == "unknown"
    assert info["dirty"] == "no"


def test_git_info_reports_a_dirty_tree(tmp_path):
    """An uncommitted change is reported, because it changes what a render saw."""
    run = lambda *a: subprocess.run(a, cwd=tmp_path, capture_output=True, check=True)  # noqa: E731
    try:
        run("git", "init", "-q")
    except (subprocess.SubprocessError, OSError):
        pytest.skip("git unavailable")
    run("git", "config", "user.email", "t@example.com")
    run("git", "config", "user.name", "t")
    (tmp_path / "a.txt").write_text("one")
    run("git", "add", "a.txt")
    run("git", "commit", "-qm", "first")
    assert git_info(tmp_path)["dirty"] == "no"

    (tmp_path / "a.txt").write_text("two")
    assert git_info(tmp_path)["dirty"] == "yes"


# ---------------------------------------------------------------------------
# Digest
# ---------------------------------------------------------------------------


def test_sha256_matches_hashlib(tmp_path):
    """The chunked read agrees with a one-shot digest."""
    blob = b"\x00\x01" * 100_000
    f = tmp_path / "q.png"
    f.write_bytes(blob)
    assert sha256(f) == hashlib.sha256(blob).hexdigest()


def test_sha256_of_a_missing_file_is_unknown(tmp_path):
    """An unreadable output does not abort a render that already succeeded."""
    assert sha256(tmp_path / "nope.png") == "unknown"


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------


def test_header_carries_the_provenance_block():
    """Every field the fleet convention calls for is present."""
    text = RunReport("Test render", povray=None).render()
    for field in (
        "# Test render",
        "**Generated:**",
        "**Machine:**",
        "**Repository:** quiltwright @",
        "**Commit:**",
        "**Python:**",
        "**Host:**",
        "**Command:**",
    ):
        assert field in text


def test_povray_none_omits_the_povray_line():
    """A render that never shells out does not claim a POV-Ray version."""
    assert "**POV-Ray:**" not in RunReport("T", povray=None).render()


def test_scene_is_hashed_into_the_header(tmp_path):
    """The scene's own digest appears -- the repo commit alone is not enough."""
    scene = tmp_path / "s.pov"
    scene.write_text("camera {}")
    text = RunReport("T", scene=scene, povray=None).render()
    assert f"sha256 `{sha256(scene)[:16]}`" in text


def test_sections_appear_in_order():
    """Sections render in the order they were added."""
    text = (
        RunReport("T", povray=None)
        .table("First", [("a", 1)])
        .pre("Second", "  indented\n  block")
        .section("Third", "prose")
        .render()
    )
    assert text.index("## First") < text.index("## Second") < text.index("## Third")
    assert "| a | 1 |" in text


def test_pre_preserves_leading_indentation():
    """The depth budget's first line is indented like the rest of its block.

    A bare ``strip()`` eats only that first line's indent, which leaves the
    fenced block visibly misaligned against every line beneath it.
    """
    text = RunReport("T", povray=None).pre("Budget", "  focal plane 92.4\n  cone 35.0\n").render()
    assert "```\n  focal plane 92.4\n  cone 35.0\n```" in text


def test_output_section_records_size_and_digest(tmp_path):
    """The report is tied to one file, not to a filename."""
    out = tmp_path / "quilt.png"
    out.write_bytes(b"x" * 2048)
    text = RunReport("T", povray=None).render(output=out)
    assert "## Output" in text
    assert sha256(out) in text


def test_write_creates_parent_directories(tmp_path):
    """``renders/reports/`` need not exist beforehand."""
    dest = tmp_path / "deep" / "er" / "r.md"
    written = RunReport("T", povray=None).write(dest)
    assert written == dest
    assert dest.read_text().startswith("# T")


def test_report_ends_with_exactly_one_newline():
    """No trailing blank-line drift between runs, so diffs stay meaningful."""
    text = RunReport("T", povray=None).table("S", [("a", 1)]).render()
    assert text.endswith("|\n")
    assert not text.endswith("\n\n")
