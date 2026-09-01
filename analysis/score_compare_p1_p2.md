# Score comparison: before vs after Priority 1 + light Priority 2

| | Before (`d0b1e0e`) | After (`444c9b7`) | Delta |
|--|-------------------:|------------------:|------:|
| **Quality grade** | A | A | -- |
| **Quality score** | **98.2** | **100.0** | **+1.8** |
| Docstring coverage pts | 40.0 / 40 | 40.0 / 40 | 0 |
| Dead-code pts | 23.2 / 25 | **25.0 / 25** | **+1.8** |
| High fan-out pts | 20.0 / 20 | 20.0 / 20 | 0 |
| Circular-deps pts | 15.0 / 15 | 15.0 / 15 | 0 |

Reports: `quiltwright_analysis_20260901.md` (before) vs
`quiltwright_analysis_after_p1_p2.md` (after, rebuilt graph).

## What moved the needle

The entire +1.8 came from clearing the false orphan on `_HasLens`:

| Signal | Before | After |
|--------|--------|-------|
| Dead-code candidates | 1 (`povray._HasLens`) | **0** |
| Docstring coverage | 94.1% | **94.4%** |
| Module docstring coverage | 96.2% (25/26) | **100%** (26/26) |
| `quilt.py` cohesion | 0.80 | **0.89** |
| `povray.py` def count (warn) | 36 | 32 |
| Functions in graph | 192 | 189 |

Promoting `HasLens` into `quilt` (where it belongs next to `QuiltCamera`)
and documenting `cli/__init__.py` did the rest of the coverage bump.
Deduplicating `require_pyvista` / `triple` shrank the function count without
changing behaviour.

## What did not move (expected)

| Still flagged | Why we left it |
|---------------|----------------|
| `povgen.py` size warn (61 defs) | Full module split deferred (option B) |
| `povray.py` size warn (32 defs) | Same |
| 10 test-only "orphans" (`aimed`, etc.) | Intentional public/tested API |

## Bottom line

Perfect score on the current rubric. Further structural splits would be
cosmetic relative to this grade -- the remaining WARNs are size heuristics,
not health failures.
