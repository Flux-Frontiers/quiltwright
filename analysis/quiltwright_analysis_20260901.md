> **Analysis Report Metadata**  
> - **Generated:** 2026-09-01T00:41:42Z  
> - **Version:** pycode-kg 0.24.1  
> - **Commit:** d0b1e0e (develop)  
> - **Index freshness:** [WARN] 1 uncommitted change(s) — the index may not reflect current file contents; line numbers and edge counts can drift. Re-run `pycodekg build` before trusting them.  
> - **Platform:** macOS 27.0 | arm64 (arm) | turing | Python 3.12.13  
> - **Graph:** 4301 nodes · 3797 edges (306 meaningful)  
> - **Included directories:** src  
> - **Excluded directories:** tests  
> - **Elapsed time:** 3s  

# quiltwright Analysis

**Generated:** 2026-09-01 00:41:42 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **quiltwright** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
| :--- | :--- | :--- |
| [A] **Excellent** | **A** | 98.2 / 100 |

Score components:

| Component | Points | Max | Basis |
| :--- | ---: | ---: | :--- |
| Docstring coverage | 40.0 | 40 | 94.1% documented (full marks at 90%) |
| Dead code | 23.2 | 25 | 1 candidates / 280 definitions scanned (0.4%; zero points at 5%) |
| High fan-out | 20.0 | 20 | 0 orchestrator(s); −4 pts each |
| Circular dependencies | 15.0 | 15 | 0 cycle(s); −5 pts each |

---

## Baseline Metrics

| Metric | Value |
| :--- | :--- |
| **Total Nodes** | 4301 |
| **Total Edges** | 3797 |
| **Modules** | 26 (of 26 total) |
| **Functions** | 192 |
| **Classes** | 31 |
| **Methods** | 57 |

### Edge Distribution

| Relationship Type | Count |
| :--- | ---: |
| CALLS | 1507 |
| CONTAINS | 280 |
| IMPORTS | 239 |
| ATTR_ACCESS | 1047 |
| INHERITS | 11 |

_Excludes 713 `RESOLVES_TO` edges: internal symbol-stub resolutions, not relationships between two pieces of code. This table therefore does not sum to Total Edges._

---

## Fan-In Ranking

Most-called functions and methods — potential bottlenecks or core functionality.  Classes are omitted: instantiation counts are not architectural fan-in.

| # | Kind | Function | Module | Callers |
| ---: | :--- | :--- | ---: | :--- |
| 1 | function | `to_pov()` | src/quiltwright/povgen.py | **9** |
| 2 | function | `_texture_suffix()` | src/quiltwright/povgen.py | **7** |
| 3 | function | `_vec()` | src/quiltwright/povgen.py | **7** |
| 4 | method | `focal_distance()` | src/quiltwright/povray.py | **7** |
| 5 | method | `focal_distance()` | src/quiltwright/povray.py | **7** |
| 6 | function | `bridge_post()` | src/quiltwright/bridge.py | **6** |
| 7 | method | `sdl()` | src/quiltwright/povgen.py | **6** |
| 8 | function | `enter_orchestration()` | src/quiltwright/bridge.py | **5** |
| 9 | method | `render()` | src/quiltwright/runreport.py | **5** |
| 10 | function | `parse_color()` | src/quiltwright/povgen.py | **4** |
| 11 | method | `n_views()` | src/quiltwright/quilt.py | **4** |
| 12 | function | `_read_member()` | src/quiltwright/tvb_data.py | **4** |
| 13 | function | `_resolve()` | src/quiltwright/tvb_data.py | **4** |
| 14 | function | `_require_pyvista()` | src/quiltwright/hld.py | **4** |
| 15 | function | `_require_pyvista()` | src/quiltwright/lfd.py | **4** |

**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:

- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.  Only repo-internal callees are counted — stdlib and third-party calls are not orchestration.

No extreme high fan-out functions detected. Well-balanced architecture.

---

## Module Architecture

Top modules by dependency coupling and cohesion (showing 10 of 26 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.  Modules with no in-repo callers are externally driven (MCP router, CLI, GUI event loop) — their 0.00 cohesion is expected, not a coupling problem.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion | Note |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `src/quiltwright/povgen.py` | 29 | 12 | 1 | 1 | 0.33 |  |
| `src/quiltwright/povray.py` | 22 | 3 | 0 | 2 | 0.00 | externally driven |
| `src/quiltwright/tvb_data.py` | 24 | 2 | 0 | 1 | 0.00 | externally driven |
| `src/quiltwright/cycles.py` | 18 | 1 | 1 | 2 | 0.25 |  |
| `src/quiltwright/quilt.py` | 9 | 2 | 8 | 1 | 0.80 |  |
| `src/quiltwright/dynamic.py` | 14 | 4 | 1 | 0 | 0.50 |  |
| `src/quiltwright/pymol.py` | 13 | 3 | 5 | 1 | 0.71 |  |
| `src/quiltwright/runreport.py` | 7 | 1 | 0 | 0 | 0.00 | externally driven |
| `src/quiltwright/lfd.py` | 10 | 1 | 0 | 4 | 0.00 | externally driven |
| `src/quiltwright/weave.py` | 3 | 2 | 1 | 1 | 0.33 |  |

---

## Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 4)

```
povgen.py:sdl → povgen.py:_texture_suffix → povgen.py:sdl → povgen.py:_vec
```

---

## Public API Surface

Definitions re-exported from an `__init__.py` or otherwise reachable as public entry points, ranked by fan-in.  Top 10 of 112 shown.

| Name | Module | Fan-In | Kind |
| :--- | :--- | ---: | :--- |
| `to_pov()` | src/quiltwright/povgen.py | 9 | function |
| `bridge_post()` | src/quiltwright/bridge.py | 6 | function |
| `enter_orchestration()` | src/quiltwright/bridge.py | 5 | function |
| `available()` | src/quiltwright/pymol.py | 4 | function |
| `parse_color()` | src/quiltwright/povgen.py | 4 | function |
| `AppearanceMap` | src/quiltwright/dynamic.py | 3 | class |
| `PovCamera` | src/quiltwright/povray.py | 3 | class |
| `QuiltSpec` | src/quiltwright/quilt.py | 3 | class |
| `Sphere` | src/quiltwright/povgen.py | 3 | class |
| `assemble_quilt()` | src/quiltwright/quilt.py | 3 | function |

---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where keyword search is as effective as vector embeddings. The semantic model earns its value only when a docstring is present.

| Kind | Documented | Total | Coverage |
| :--- | ---: | ---: | :--- |
| `function` | 179 | 192 | [OK] 93.2% |
| `method` | 53 | 57 | [OK] 93.0% |
| `class` | 31 | 31 | [OK] 100.0% |
| `module` | 25 | 26 | [OK] 96.2% |
| **total** | **288** | **306** | **[OK] 94.1%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
| ---: | ---: | ---: | :--- |
| 1 | 0.234731 | 62 | `src/quiltwright/povgen.py` |
| 2 | 0.123127 | 37 | `src/quiltwright/povray.py` |
| 3 | 0.093234 | 29 | `src/quiltwright/tvb_data.py` |
| 4 | 0.085367 | 22 | `src/quiltwright/quilt.py` |
| 5 | 0.063728 | 23 | `src/quiltwright/cycles.py` |
| 6 | 0.062695 | 10 | `src/quiltwright/weave.py` |
| 7 | 0.061329 | 15 | `src/quiltwright/runreport.py` |
| 8 | 0.058418 | 20 | `src/quiltwright/dynamic.py` |
| 9 | 0.048968 | 17 | `src/quiltwright/pymol.py` |
| 10 | 0.028466 | 8 | `src/quiltwright/bridge.py` |
| 11 | 0.027057 | 12 | `src/quiltwright/lfd.py` |
| 12 | 0.020423 | 9 | `src/quiltwright/hld.py` |
| 13 | 0.016249 | 6 | `src/quiltwright/cli/cmd_wallpaper.py` |
| 14 | 0.014949 | 7 | `src/quiltwright/cli/cmd_bridge.py` |
| 15 | 0.014503 | 4 | `src/quiltwright/cli/options.py` |

---

## Code Quality Issues

- [WARN] 1 dead-code candidates found (`povray.py:_HasLens`) -- no callers in code or tests; verify against downstream consumers, then remove or archive
- [INFO] 7 definitions are unused in production code but exercised by tests -- likely public API for downstream packages; not counted against the quality grade
- [WARN] `povgen.py` has 61 functions/methods/classes -- consider splitting into focused submodules
- [WARN] `povray.py` has 36 functions/methods/classes -- consider splitting into focused submodules

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No god objects or god functions detected
- Good docstring coverage: 94.1% of functions/methods/classes/modules documented

---

## Recommendations

### Immediate Actions
1. **Triage dead-code candidates** — `_HasLens` have zero callers in code and tests; confirm no downstream package consumes them, then remove

### Medium-term Refactoring
1. **Harden high fan-in functions** — `to_pov`, `_texture_suffix`, `_vec` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `to_pov`, `bridge_post`, `enter_orchestration`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## Inheritance Hierarchy

**11** INHERITS edges across **12** classes. Max depth: **1**.

| Class | Module | Depth | Parents | Children |
| :--- | :--- | ---: | ---: | ---: |
| `Box` | src/quiltwright/povgen.py | 1 | 1 | 0 |
| `Cylinder` | src/quiltwright/povgen.py | 1 | 1 | 0 |
| `Instance` | src/quiltwright/povgen.py | 1 | 1 | 0 |
| `Mesh2` | src/quiltwright/povgen.py | 1 | 1 | 0 |
| `Sphere` | src/quiltwright/povgen.py | 1 | 1 | 0 |
| `SphereSweep` | src/quiltwright/povgen.py | 1 | 1 | 0 |
| `Union` | src/quiltwright/povgen.py | 1 | 1 | 0 |
| `Primitive` | src/quiltwright/povgen.py | 0 | 0 | 7 |
| `_HasLens` | src/quiltwright/povray.py | 0 | 1 | 0 |
| `PyMolNotAvailable` | src/quiltwright/pymol.py | 0 | 1 | 0 |
| `QuiltCamera` | src/quiltwright/quilt.py | 0 | 1 | 0 |
| `Connectome` | src/quiltwright/tvb_data.py | 0 | 1 | 0 |

---

## Snapshot History

Recent snapshots in reverse chronological order. Δ columns show change vs. the immediately preceding snapshot.

| # | Timestamp | Branch | Version | Nodes | Edges | Coverage | Δ Nodes | Δ Edges | Δ Coverage |
| ---: | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2026-08-30 02:30:36 | develop | 0.21.4 | 3975 | 3522 | 93.5% | — | — | — |

---

## Orphaned Code

1 definitions have no callers in code or tests (dead-code candidates).  Framework-dispatched entry points — dunder/protocol methods, properties, Click commands, MCP tools, `ast.NodeVisitor` dispatch, SDK protocol overrides, console scripts, `__main__` guards — are already excluded.

| Name | Kind | Module | Lines |
| :--- | :--- | :--- | ---: |
| `_HasLens` | class | src/quiltwright/povray.py | 13 |

7 further definitions are unused in production code but exercised by tests — likely public API consumed by downstream packages.  Not counted against the quality grade; review for intentional export.

| Name | Kind | Module | Lines |
| :--- | :--- | :--- | ---: |
| `aimed()` | method | src/quiltwright/povray.py | 50 |
| `aimed()` | method | src/quiltwright/cycles.py | 43 |
| `cone()` | method | src/quiltwright/povray.py | 21 |
| `from_appearance()` | method | src/quiltwright/dynamic.py | 18 |
| `pre()` | method | src/quiltwright/runreport.py | 14 |
| `with_grid()` | method | src/quiltwright/quilt.py | 12 |
| `table()` | method | src/quiltwright/runreport.py | 12 |

---

## CodeRank — Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds fan-in discovery and the concern queries below.  Top 20 of 25 shown.

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.000766 | function | `bridge_post()` | src/quiltwright/bridge.py |
| 2 | 0.000620 | function | `to_pov()` | src/quiltwright/povgen.py |
| 3 | 0.000572 | function | `enter_orchestration()` | src/quiltwright/bridge.py |
| 4 | 0.000488 | function | `cache_dir()` | src/quiltwright/tvb_data.py |
| 5 | 0.000485 | function | `_texture_suffix()` | src/quiltwright/povgen.py |
| 6 | 0.000484 | function | `camera_block()` | src/quiltwright/povray.py |
| 7 | 0.000480 | function | `_vec()` | src/quiltwright/povgen.py |
| 8 | 0.000462 | method | `PovCamera.focal_distance()` | src/quiltwright/povray.py |
| 9 | 0.000462 | method | `_HasLens.focal_distance()` | src/quiltwright/povray.py |
| 10 | 0.000438 | method | `RunReport.section()` | src/quiltwright/runreport.py |
| 11 | 0.000435 | method | `_HasLens.fov()` | src/quiltwright/povray.py |
| 12 | 0.000419 | method | `Clearance.half_width()` | src/quiltwright/povray.py |
| 13 | 0.000413 | function | `parse_color()` | src/quiltwright/povgen.py |
| 14 | 0.000411 | method | `QuiltSpec.n_views()` | src/quiltwright/quilt.py |
| 15 | 0.000402 | function | `_osascript()` | src/quiltwright/cli/cmd_wallpaper.py |
| 16 | 0.000397 | function | `_read_member()` | src/quiltwright/tvb_data.py |
| 17 | 0.000397 | function | `_resolve()` | src/quiltwright/tvb_data.py |
| 18 | 0.000389 | function | `_triple()` | src/quiltwright/cycles.py |
| 19 | 0.000365 | function | `_matching_brace()` | src/quiltwright/povgen.py |
| 20 | 0.000361 | function | `_run()` | src/quiltwright/runreport.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7349 | method | `Mesh2.__post_init__()` | src/quiltwright/povgen.py |
| 2 | 0.7325 | method | `Clearance.__post_init__()` | src/quiltwright/povray.py |
| 3 | 0.7292 | function | `load_connectivity()` | src/quiltwright/tvb_data.py |
| 4 | 0.7268 | function | `src/quiltwright/povgen.py.coalesce_mesh2.intern()` | src/quiltwright/povgen.py |
| 5 | 0.6717 | class | `DynamicSpec` | src/quiltwright/dynamic.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7587 | function | `fetch_archive()` | src/quiltwright/tvb_data.py |
| 2 | 0.755 | function | `cache_dir()` | src/quiltwright/tvb_data.py |
| 3 | 0.7475 | function | `_read_member()` | src/quiltwright/tvb_data.py |
| 4 | 0.7404 | function | `dataset_cache_dir()` | src/quiltwright/cache.py |
| 5 | 0.7381 | function | `archive_path()` | src/quiltwright/tvb_data.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7673 | method | `QuiltSpec.n_views()` | src/quiltwright/quilt.py |
| 2 | 0.7629 | method | `_HasLens.focal_distance()` | src/quiltwright/povray.py |
| 3 | 0.7504 | function | `_loadtxt()` | src/quiltwright/tvb_data.py |
| 4 | 0.7481 | function | `src/quiltwright/lfd.py.render_quilt.views()` | src/quiltwright/lfd.py |
| 5 | 0.7459 | function | `_named_list()` | src/quiltwright/povgen.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7574 | function | `_matching_brace()` | src/quiltwright/povgen.py |
| 2 | 0.7511 | function | `sphere_sweeps_from_paths()` | src/quiltwright/povgen.py |
| 3 | 0.7494 | method | `Mesh2.sdl()` | src/quiltwright/povgen.py |
| 4 | 0.7459 | function | `src/quiltwright/povgen.py.coalesce_mesh2.block()` | src/quiltwright/povgen.py |
| 5 | 0.7443 | function | `src/quiltwright/povgen.py.Mesh2.sdl.block()` | src/quiltwright/povgen.py |

---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 3.8s*
