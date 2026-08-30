"""Compare CPython versions on quiltwright's actual workloads.

Run it under one interpreter to get a table, or hand it two or more
interpreters and it re-execs itself under each and prints the comparison:

    .venv/bin/python benchmarks/interpreter.py
    .venv/bin/python benchmarks/interpreter.py .venv/bin/python /tmp/qw313/bin/python

Workloads are split deliberately.  ``sdl`` and ``import`` are interpreter-bound
and are where a CPython version difference can show up at all; ``assemble`` and
``weave`` are numpy-bound and are here as the control -- if those move, the
cause is a different numpy build, not the interpreter.  Check the numpy versions
printed under the table before reading anything into a delta: two venvs built at
different times are not required to agree, and a numpy difference would swamp
everything the interpreter contributes.

This measures the Python slice in isolation, which is the smaller half of the
story.  For the end-to-end number, render the same scene under each interpreter
and diff the run reports -- they already carry both the interpreter version and
the timing::

    make quilt-porin PYTHON=/path/to/python   # -> renders/reports/porin_*.md
"""

import json
import subprocess
import sys
import timeit
from pathlib import Path

REPEAT = 5

# A real gen3 16" Landscape visual.json, trimmed to what Calibration reads.
CAL_RAW = {
    "configVersion": "3.0",
    "serial": "LKG-J00332",
    "pitch": {"value": 44.75058319896644},
    "slope": {"value": -6.874565686767793},
    "center": {"value": 0.16935753461833172},
    "viewCone": {"value": 50.0},
    "DPI": {"value": 283.0},
    "screenW": {"value": 3840.0},
    "screenH": {"value": 2160.0},
    "flipImageX": {"value": 0.0},
    "CellPatternMode": {"value": 2.0},
    "subpixelCells": [
        {
            "ROffsetX": -0.31,
            "ROffsetY": 0.25,
            "GOffsetX": 0.28,
            "GOffsetY": 0.25,
            "BOffsetX": 0.0,
            "BOffsetY": -0.25,
        },
        {
            "ROffsetX": -0.31,
            "ROffsetY": -0.25,
            "GOffsetX": 0.28,
            "GOffsetY": -0.25,
            "BOffsetX": 0.0,
            "BOffsetY": 0.25,
        },
    ],
}


def workloads():
    """:return: Mapping of name to a zero-argument callable to time."""
    import numpy as np

    from quiltwright.povgen import spheres_from_points
    from quiltwright.quilt import QUILT_PRESETS, assemble_quilt
    from quiltwright.weave import Calibration, weave_quilt

    rng = np.random.default_rng(0)

    # Interpreter-bound: 100k dataclasses, then 100k f-strings.  This is what a
    # large molecular scene does before povray ever starts.
    points = rng.normal(size=(100_000, 3))
    spheres = spheres_from_points(points, 0.4, "atom_C")

    # numpy-bound control 1: 48 views tiled into a 3360x3360 portrait quilt.
    spec = QUILT_PRESETS["portrait"]
    views = [
        rng.integers(0, 256, (spec.tile_height, spec.tile_width, 3), dtype=np.uint8)
        for _ in range(spec.n_views)
    ]

    # numpy-bound control 2: the lenticular interleave, 7680x4320 quilt onto a
    # 3840x2160 panel.  The heaviest array work in the package.
    wspec = QUILT_PRESETS["16-landscape"]
    cal = Calibration.from_dict(CAL_RAW)
    big = rng.integers(0, 256, (wspec.quilt_height, wspec.quilt_width, 3), dtype=np.uint8)

    return {
        "sdl (100k spheres to POV text)": lambda: [s.sdl() for s in spheres],
        "spheres_from_points (100k)": lambda: spheres_from_points(points, 0.4, "atom_C"),
        "assemble_quilt (48 x 420x560)": lambda: assemble_quilt(views, spec),
        "weave_quilt (7680x4320 -> 3840x2160)": lambda: weave_quilt(big, wspec, cal),
    }


def measure():
    """:return: Dict of environment info plus best-of-REPEAT seconds per workload."""
    import numpy as np

    results = {}
    for name, fn in workloads().items():
        # Best-of, not mean: the minimum is the run least disturbed by other
        # load on the box, and this machine renders while it benchmarks.
        results[name] = min(timeit.Timer(fn).repeat(repeat=REPEAT, number=1))
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "results": results,
    }


def import_time(exe):
    """:return: Best-of-REPEAT seconds for `import quiltwright` in a fresh process."""
    best = None
    for _ in range(REPEAT):
        t = timeit.default_timer()
        subprocess.run([exe, "-c", "import quiltwright"], check=True)
        dt = timeit.default_timer() - t
        best = dt if best is None else min(best, dt)
    return best


def main():
    exes = sys.argv[1:]
    if not exes:
        print(json.dumps(measure(), indent=2))
        return

    runs = []
    for exe in exes:
        out = subprocess.run(
            [exe, str(Path(__file__).resolve())], capture_output=True, text=True, check=True
        )
        run = json.loads(out.stdout)
        run["results"]["import quiltwright (cold process)"] = import_time(exe)
        run["exe"] = exe
        runs.append(run)

    names = list(runs[0]["results"])
    label_w = max(len(n) for n in names) + 2
    head = "".join(f"{r['python']:>14}" for r in runs)
    print(f"{'workload':<{label_w}}{head}{'   delta':>10}")
    print("-" * (label_w + 14 * len(runs) + 10))
    for name in names:
        cells = "".join(f"{r['results'][name] * 1e3:>13.1f}m" for r in runs)
        first, last = runs[0]["results"][name], runs[-1]["results"][name]
        print(f"{name:<{label_w}}{cells}{(last / first - 1) * 100:>+9.1f}%")
    print()
    for r in runs:
        print(f"  {r['python']:<8} numpy {r['numpy']:<10} {r['exe']}")
    print("\n  best of", REPEAT, "-- delta is the last column vs the first")


if __name__ == "__main__":
    main()
