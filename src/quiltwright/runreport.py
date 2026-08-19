"""
Run reports -- a Markdown summary of one render, with full provenance.

A quilt is a 25-40 MB PNG with nothing inside it that says where it came
from. Six months on, the questions that matter are not answerable from the
file: which scene file, at which commit, through which camera, with which
POV-Ray, at what focal plane -- and whether the disparity figures anyone
quoted at the time were measured or guessed. This module writes that down
beside the render.

The header follows the fleet's convention (see
``_waverider/benchmarks/canonical_tests/``): generated-at, machine, repo and
commit, interpreter and tool versions, host and OS. Everything in it is
*detected*, never hardcoded, so a report copied off another box is still
true about the box that made it.

Two things here are specific to rendering rather than to benchmarking:

*The scene's blob hash, not just the repo's commit.* A render usually
happens with the scene edited and uncommitted -- that is what iterating on a
composition looks like -- so the repo hash alone can describe a tree the
render never saw. Hashing the scene file itself pins the actual input, and
the report says plainly whether the tree was dirty.

*The output's SHA-256.* The report is only evidence if it can be tied to a
particular file, and quilts are regenerated often enough that filename and
mtime are not enough.

Usage::

    report = RunReport("Bell jar hologram")
    report.table("Run configuration", [("device", "16-landscape")])
    report.pre("Depth budget", format_depth_budget(spec, camera, depths))
    report.write("renders/reports/bell-jar-holo.md", output=quilt_path)

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import hashlib
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

__all__ = [
    "RunReport",
    "git_info",
    "machine_description",
    "povray_parallelism",
    "povray_version",
    "sha256",
]

#: Repository root, used for the provenance header's git lookups.
_REPO_ROOT = Path(__file__).resolve().parents[2]

_UNKNOWN = "unknown"


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    """Capture a command's stdout, or ``""`` if it cannot be run.

    Provenance is best-effort by design: a report is worth writing on a box
    with no git and no POV-Ray on ``PATH``, it just has less in it.

    :param cmd: Command and arguments.
    :param cwd: Working directory.
    :return: Stripped stdout, or the empty string on any failure.
    """
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=10, check=True).stdout
    except (subprocess.SubprocessError, OSError):
        return ""
    return out.decode("utf-8", "replace").strip()


def machine_description() -> str:
    """CPU brand and installed RAM.

    Detected rather than hardcoded -- these reports are compared across
    machines, and a stale constant is worse than no line at all.

    :return: e.g. ``"Apple M5 Max, 64 GB RAM"``, or a coarser fallback.
    """
    brand = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
    memsize = _run(["sysctl", "-n", "hw.memsize"])
    if brand and memsize.isdigit():
        return f"{brand}, {round(int(memsize) / 1024**3)} GB RAM"
    return brand or platform.processor() or platform.machine() or _UNKNOWN


def git_info(path: Path | None = None) -> dict[str, str]:
    """Commit identity of the working copy, and whether it is dirty.

    :param path: Any path inside the repository; defaults to this package's.
    :return: ``hash``, ``branch``, ``date``, ``subject`` and ``dirty``, each
        falling back to ``"unknown"``.  ``dirty`` is ``"yes"``/``"no"``.
    """
    cwd = (path or _REPO_ROOT).resolve()
    if cwd.is_file():
        cwd = cwd.parent
    info = {
        "hash": _run(["git", "rev-parse", "--short", "HEAD"], cwd),
        "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd),
        "date": _run(["git", "log", "-1", "--format=%ci"], cwd),
        "subject": _run(["git", "log", "-1", "--format=%s"], cwd),
    }
    status = _run(["git", "status", "--porcelain"], cwd)
    info["dirty"] = "yes" if status else "no"
    return {k: v or _UNKNOWN for k, v in info.items()}


def povray_version(binary: str | None = None) -> str:
    """The POV-Ray build actually on ``PATH``.

    POV-Ray writes its banner to stderr and exits non-zero for
    ``--version``, so this reads the first line of the combined output
    rather than trusting the exit status.

    :param binary: Explicit executable; defaults to ``povray`` on ``PATH``.
    :return: e.g. ``"POV-Ray 3.7.0.10.unofficial"``, or ``"unknown"``.
    """
    exe = shutil.which(binary or "povray")
    if not exe:
        return _UNKNOWN
    try:
        proc = subprocess.run([exe, "--version"], capture_output=True, timeout=10, check=False)
    except (subprocess.SubprocessError, OSError):
        return _UNKNOWN
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return _UNKNOWN


def povray_parallelism(jobs: int, threads: int | None = None) -> list[tuple[str, object]]:
    """How the render was actually parallelised, resolved not assumed.

    Two independent knobs decide this and neither is visible in the command
    line, which is exactly why a report that omits them cannot explain its
    own timings.

    ``jobs`` is POV-Ray *processes*. Threads *per* process come from
    somewhere else: above one job :func:`~quiltwright.povray.render_pov_quilt`
    appends ``+WT<cores/jobs>`` so the processes split the machine rather
    than each claiming all of it; at one job it appends nothing, and POV-Ray
    falls back to the ``Work_Threads`` in whatever INI ``POVINI`` names --
    which is where this repo's Makefile puts its cap. With neither, POV-Ray
    takes every core.

    :param jobs: Concurrent POV-Ray processes the run used.
    :param threads: The run's ``--threads``, or ``None`` for the default.
    :return: ``(name, value)`` rows for :meth:`RunReport.table`.
    """
    import os

    cores = os.cpu_count() or 0
    ini = os.environ.get("POVINI", "")
    ini_threads = ""
    if ini:
        try:
            for line in Path(ini).read_text(errors="replace").splitlines():
                key, _, val = line.partition("=")
                if key.strip().lower() == "work_threads" and val.strip().isdigit():
                    ini_threads = val.strip()  # later keys win, so keep scanning
        except OSError:
            ini_threads = "unreadable"

    from quiltwright.povray import resolve_work_threads

    if jobs > 1:
        per = str(max(1, cores // jobs)) if cores else "cores/jobs"
        source = "+WT, derived from cores/jobs"
    else:
        capped = resolve_work_threads(threads)
        if capped is not None:
            per = str(capped)
            source = "+WT courtesy cap" if threads is None else "+WT, --threads"
        elif ini_threads.isdigit():
            per, source = ini_threads, f"Work_Threads in {ini}"
        else:
            per, source = str(cores) if cores else _UNKNOWN, "POV-Ray default (all cores)"

    rows: list[tuple[str, object]] = [
        ("CPU cores", cores or _UNKNOWN),
        ("POV-Ray processes (--jobs)", jobs),
        ("threads per process", per),
        ("thread count set by", source),
    ]
    if per.isdigit() and cores:
        total = int(per) * jobs
        rows.append(
            ("cores in use", f"{total} of {cores}" + (" (oversubscribed)" if total > cores else ""))
        )
    return rows


def sha256(path: Path | str) -> str:
    """SHA-256 of a file, read in chunks.

    :param path: File to digest.
    :return: Lowercase hex digest, or ``"unknown"`` if unreadable.
    """
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return _UNKNOWN
    return h.hexdigest()


def _pkg_version(name: str) -> str:
    """Installed version of a distribution, or ``"not installed"``."""
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


@dataclass
class RunReport:
    """A Markdown run report, built section by section.

    :param title: Report heading, without the leading ``#``.
    :param scene: Scene file the run consumed.  Hashed into the provenance
        header, because a render normally happens against an edited working
        copy and the repo commit alone would not identify it.
    :param povray: POV-Ray executable to report the version of.  ``None``
        omits the line, which is right for renders that never shell out.
    """

    title: str
    scene: Path | None = None
    povray: str | None = "povray"
    _sections: list[str] = field(default_factory=list, repr=False)

    def section(self, heading: str, body: str = "") -> RunReport:
        """Append a free-form section.

        :param heading: Section heading, without the leading ``##``.
        :param body: Markdown body.
        :return: ``self``, for chaining.
        """
        self._sections.append(f"## {heading}\n\n{body}".rstrip() + "\n")
        return self

    def table(
        self, heading: str, rows: list[tuple[str, object]], *, columns=("Parameter", "Value")
    ) -> RunReport:
        """Append a two-column table.

        :param heading: Section heading.
        :param rows: ``(name, value)`` pairs; values are stringified.
        :param columns: Column headings.
        :return: ``self``, for chaining.
        """
        lines = [f"| {columns[0]} | {columns[1]} |", "|---|---|"]
        lines += [f"| {name} | {value} |" for name, value in rows]
        return self.section(heading, "\n".join(lines))

    def pre(self, heading: str, text: str) -> RunReport:
        """Append a section holding preformatted text.

        Used for output a script already formats for the terminal -- the
        depth budget above all -- so the report and the console agree
        character for character rather than paraphrasing each other.

        :param heading: Section heading.
        :param text: Text to fence.
        :return: ``self``, for chaining.
        """
        # strip("\n") rather than strip(): the budget's first line is indented
        # like the rest of the block, and a bare strip() eats only that one,
        # leaving the fence misaligned against every line under it.
        return self.section(heading, f"```\n{text.strip(chr(10))}\n```")

    def _header(self) -> list[str]:
        """The provenance block."""
        git = git_info()
        dirty = "" if git["dirty"] == "no" else " **+ uncommitted changes**"
        lines = [
            f"# {self.title}",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Machine:** {machine_description()}  ",
            f"**Repository:** quiltwright @ `{git['hash']}` ({git['branch']}){dirty}  ",
            f"**Commit:** {git['date']} -- {git['subject']}  ",
        ]
        if self.scene is not None:
            scene = Path(self.scene)
            rel = scene.resolve()
            try:
                rel = rel.relative_to(_REPO_ROOT)
            except ValueError:
                pass
            lines.append(f"**Scene:** `{rel}` sha256 `{sha256(scene)[:16]}`  ")
        tools = [
            f"**Python:** {platform.python_version()}",
            f"**quiltwright:** {_pkg_version('quiltwright')}",
            f"**numpy:** {_pkg_version('numpy')}",
        ]
        if self.povray is not None:
            tools.append(f"**POV-Ray:** {povray_version(self.povray)}")
        lines.append("  |  ".join(tools) + "  ")
        lines.append(f"**Host:** {socket.gethostname()}  |  **OS:** {platform.platform()}  ")
        lines.append(f"**Command:** `{' '.join(sys.argv)}`")
        lines += ["", "---", ""]
        return lines

    def render(self, output: Path | str | None = None) -> str:
        """Assemble the report.

        :param output: Rendered artifact to record, if any.  Its size and
            SHA-256 are appended, which is what ties the report to one
            specific file rather than to a filename.
        :return: The Markdown document.
        """
        parts = self._header() + self._sections
        if output is not None:
            out = Path(output)
            size = out.stat().st_size if out.is_file() else 0
            rows = [
                ("File", f"`{out}`"),
                ("Size", f"{size / 1024**2:.1f} MB" if size else _UNKNOWN),
                ("SHA-256", f"`{sha256(out)}`"),
            ]
            body = "\n".join(
                ["| Field | Value |", "|---|---|", *(f"| {k} | {v} |" for k, v in rows)]
            )
            parts.append(f"## Output\n\n{body}\n")
        return "\n".join(parts).rstrip() + "\n"

    def write(self, path: Path | str, *, output: Path | str | None = None) -> Path:
        """Write the report, creating parent directories.

        :param path: Destination ``.md`` file.
        :param output: Rendered artifact to record; see :meth:`render`.
        :return: The path written.
        """
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(self.render(output), encoding="utf-8")
        return dest
