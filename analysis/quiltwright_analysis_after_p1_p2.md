> **Analysis Report Metadata**  
> - **Generated:** 2026-09-01T01:21:03Z  
> - **Version:** pycode-kg 0.24.1  
> - **Commit:** 444c9b7 (develop)  
> - **Index freshness:** [WARN] 1 uncommitted change(s) — the index may not reflect current file contents; line numbers and edge counts can drift. Re-run `pycodekg build` before trusting them.  
> - **Platform:** macOS 27.0 | arm64 (arm) | turing | Python 3.12.13  
> - **Graph:** 4295 nodes · 3697 edges (303 meaningful)  
> - **Included directories:** src  
> - **Excluded directories:** tests  
> - **Elapsed time:** 2s  

# quiltwright Analysis

**Generated:** 2026-09-01 01:21:03 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **quiltwright** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
| :--- | :--- | :--- |
| [A] **Excellent** | **A** | 100.0 / 100 |

Score components:

| Component | Points | Max | Basis |
| :--- | ---: | ---: | :--- |
| Docstring coverage | 40.0 | 40 | 94.4% documented (full marks at 90%) |
| Dead code | 25.0 | 25 | 0 candidates / 277 definitions scanned (0.0%; zero points at 5%) |
| High fan-out | 20.0 | 20 | 0 orchestrator(s); −4 pts each |
| Circular dependencies | 15.0 | 15 | 0 cycle(s); −5 pts each |

---

## Baseline Metrics

| Metric | Value |
| :--- | :--- |
| **Total Nodes** | 4295 |
| **Total Edges** | 3697 |
| **Modules** | 26 (of 26 total) |
| **Functions** | 189 |
| **Classes** | 31 |
| **Methods** | 57 |

### Edge Distribution

| Relationship Type | Count |
| :--- | ---: |
| CALLS | 1494 |
| CONTAINS | 277 |
| IMPORTS | 246 |
| ATTR_ACCESS | 1047 |
| INHERITS | 11 |

_Excludes 622 `RESOLVES_TO` edges: internal symbol-stub resolutions, not relationships between two pieces of code. This table therefore does not sum to Total Edges._

---

## Fan-In Ranking

Most-called functions and methods — potential bottlenecks or core functionality.  Classes are omitted: instantiation counts are not architectural fan-in.

| # | Kind | Function | Module | Callers |
| ---: | :--- | :--- | ---: | :--- |
| 1 | function | `to_pov()` | src/quiltwright/povgen.py | **9** |
| 2 | method | `focal_distance()` | src/quiltwright/povray.py | **7** |
| 3 | function | `_texture_suffix()` | src/quiltwright/povgen.py | **7** |
| 4 | function | `_vec()` | src/quiltwright/povgen.py | **7** |
| 5 | function | `bridge_post()` | src/quiltwright/bridge.py | **6** |
| 6 | function | `enter_orchestration()` | src/quiltwright/bridge.py | **5** |
| 7 | method | `render()` | src/quiltwright/runreport.py | **5** |
| 8 | function | `parse_color()` | src/quiltwright/povgen.py | **4** |
| 9 | method | `n_views()` | src/quiltwright/quilt.py | **4** |
| 10 | function | `_read_member()` | src/quiltwright/tvb_data.py | **4** |
| 11 | function | `_resolve()` | src/quiltwright/tvb_data.py | **4** |
| 12 | function | `available()` | src/quiltwright/pymol.py | **4** |
| 13 | function | `resolve_work_threads()` | src/quiltwright/povray.py | **4** |
| 14 | method | `half_width()` | src/quiltwright/povray.py | **3** |
| 15 | method | `tile_height()` | src/quiltwright/quilt.py | **3** |

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
| `src/quiltwright/povgen.py` | 29 | 12 | 1 | 0 | 0.50 |  |
| `src/quiltwright/povray.py` | 21 | 2 | 0 | 2 | 0.00 | externally driven |
| `src/quiltwright/tvb_data.py` | 23 | 2 | 0 | 2 | 0.00 | externally driven |
| `src/quiltwright/quilt.py` | 9 | 3 | 8 | 0 | 0.89 |  |
| `src/quiltwright/cycles.py` | 17 | 1 | 1 | 2 | 0.25 |  |
| `src/quiltwright/dynamic.py` | 14 | 4 | 1 | 0 | 0.50 |  |
| `src/quiltwright/pymol.py` | 13 | 3 | 0 | 1 | 0.00 | externally driven |
| `src/quiltwright/runreport.py` | 7 | 1 | 0 | 0 | 0.00 | externally driven |
| `src/quiltwright/lfd.py` | 9 | 1 | 0 | 3 | 0.00 | externally driven |
| `src/quiltwright/weave.py` | 3 | 2 | 1 | 1 | 0.33 |  |

---

## Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 4)

```
povgen.py:sdl → povgen.py:_texture_suffix → povgen.py:sdl → povgen.py:parse_color
```

**Chain 2** (depth: 3)

```
bridge.py:enter_orchestration → bridge.py:bridge_post → tvb_data.py:read
```

---

## Public API Surface

Definitions re-exported from an `__init__.py` or otherwise reachable as public entry points, ranked by fan-in.  Top 10 of 114 shown.

| Name | Module | Fan-In | Kind |
| :--- | :--- | ---: | :--- |
| `to_pov()` | src/quiltwright/povgen.py | 9 | function |
| `bridge_post()` | src/quiltwright/bridge.py | 6 | function |
| `enter_orchestration()` | src/quiltwright/bridge.py | 5 | function |
| `available()` | src/quiltwright/pymol.py | 4 | function |
| `parse_color()` | src/quiltwright/povgen.py | 4 | function |
| `resolve_work_threads()` | src/quiltwright/povray.py | 4 | function |
| `AppearanceMap` | src/quiltwright/dynamic.py | 3 | class |
| `PovCamera` | src/quiltwright/povray.py | 3 | class |
| `QuiltSpec` | src/quiltwright/quilt.py | 3 | class |
| `Sphere` | src/quiltwright/povgen.py | 3 | class |

---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where keyword search is as effective as vector embeddings. The semantic model earns its value only when a docstring is present.

| Kind | Documented | Total | Coverage |
| :--- | ---: | ---: | :--- |
| `function` | 176 | 189 | [OK] 93.1% |
| `method` | 53 | 57 | [OK] 93.0% |
| `class` | 31 | 31 | [OK] 100.0% |
| `module` | 26 | 26 | [OK] 100.0% |
| **total** | **286** | **303** | **[OK] 94.4%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
| ---: | ---: | ---: | :--- |
| 1 | 0.238281 | 62 | `src/quiltwright/povgen.py` |
| 2 | 0.102480 | 28 | `src/quiltwright/tvb_data.py` |
| 3 | 0.101613 | 25 | `src/quiltwright/quilt.py` |
| 4 | 0.098886 | 33 | `src/quiltwright/povray.py` |
| 5 | 0.064325 | 20 | `src/quiltwright/dynamic.py` |
| 6 | 0.063748 | 22 | `src/quiltwright/cycles.py` |
| 7 | 0.054660 | 15 | `src/quiltwright/runreport.py` |
| 8 | 0.043438 | 17 | `src/quiltwright/pymol.py` |
| 9 | 0.034532 | 10 | `src/quiltwright/weave.py` |
| 10 | 0.034490 | 8 | `src/quiltwright/bridge.py` |
| 11 | 0.025307 | 11 | `src/quiltwright/lfd.py` |
| 12 | 0.024212 | 4 | `src/quiltwright/runtime.py` |
| 13 | 0.019788 | 3 | `src/quiltwright/cache.py` |
| 14 | 0.017362 | 6 | `src/quiltwright/cli/cmd_wallpaper.py` |
| 15 | 0.017271 | 7 | `src/quiltwright/cli/cmd_bridge.py` |

---

## Code Quality Issues

- [INFO] 10 definitions are unused in production code but exercised by tests -- likely public API for downstream packages; not counted against the quality grade
- [WARN] `povgen.py` has 61 functions/methods/classes -- consider splitting into focused submodules
- [WARN] `povray.py` has 32 functions/methods/classes -- consider splitting into focused submodules

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- No god objects or god functions detected
- Good docstring coverage: 94.4% of functions/methods/classes/modules documented

---

## Recommendations

### Medium-term Refactoring
1. **Harden high fan-in functions** — `to_pov`, `focal_distance`, `_texture_suffix` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
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
| `PyMolNotAvailable` | src/quiltwright/pymol.py | 0 | 1 | 0 |
| `HasLens` | src/quiltwright/quilt.py | 0 | 1 | 0 |
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

No dead-code candidates detected.

10 further definitions are unused in production code but exercised by tests — likely public API consumed by downstream packages.  Not counted against the quality grade; review for intentional export.

| Name | Kind | Module | Lines |
| :--- | :--- | :--- | ---: |
| `aimed()` | method | src/quiltwright/povray.py | 50 |
| `aimed()` | method | src/quiltwright/cycles.py | 43 |
| `cone()` | method | src/quiltwright/povray.py | 21 |
| `from_appearance()` | method | src/quiltwright/dynamic.py | 18 |
| `pre()` | method | src/quiltwright/runreport.py | 14 |
| `with_grid()` | method | src/quiltwright/quilt.py | 12 |
| `table()` | method | src/quiltwright/runreport.py | 12 |
| `add()` | method | src/quiltwright/povgen.py | 10 |
| `write()` | method | src/quiltwright/runreport.py | 10 |
| `write()` | method | src/quiltwright/povgen.py | 9 |

---

## CodeRank — Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds fan-in discovery and the concern queries below.  Top 20 of 25 shown.

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.000767 | function | `bridge_post()` | src/quiltwright/bridge.py |
| 2 | 0.000621 | function | `to_pov()` | src/quiltwright/povgen.py |
| 3 | 0.000578 | method | `PovCamera.focal_distance()` | src/quiltwright/povray.py |
| 4 | 0.000573 | function | `enter_orchestration()` | src/quiltwright/bridge.py |
| 5 | 0.000489 | function | `cache_dir()` | src/quiltwright/tvb_data.py |
| 6 | 0.000486 | function | `_texture_suffix()` | src/quiltwright/povgen.py |
| 7 | 0.000485 | function | `camera_block()` | src/quiltwright/povray.py |
| 8 | 0.000481 | function | `_vec()` | src/quiltwright/povgen.py |
| 9 | 0.000439 | method | `RunReport.section()` | src/quiltwright/runreport.py |
| 10 | 0.000426 | method | `Clearance.half_width()` | src/quiltwright/povray.py |
| 11 | 0.000414 | function | `parse_color()` | src/quiltwright/povgen.py |
| 12 | 0.000412 | method | `QuiltSpec.n_views()` | src/quiltwright/quilt.py |
| 13 | 0.000402 | function | `_osascript()` | src/quiltwright/cli/cmd_wallpaper.py |
| 14 | 0.000398 | function | `_read_member()` | src/quiltwright/tvb_data.py |
| 15 | 0.000398 | function | `_resolve()` | src/quiltwright/tvb_data.py |
| 16 | 0.000365 | function | `_matching_brace()` | src/quiltwright/povgen.py |
| 17 | 0.000361 | function | `_run()` | src/quiltwright/runreport.py |
| 18 | 0.000356 | function | `_vec()` | src/quiltwright/povray.py |
| 19 | 0.000355 | method | `CyclesCamera.focal_distance()` | src/quiltwright/cycles.py |
| 20 | 0.000349 | method | `QuiltSpec.tile_height()` | src/quiltwright/quilt.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7417 | method | `Mesh2.__post_init__()` | src/quiltwright/povgen.py |
| 2 | 0.7397 | method | `Clearance.__post_init__()` | src/quiltwright/povray.py |
| 3 | 0.7363 | function | `load_connectivity()` | src/quiltwright/tvb_data.py |
| 4 | 0.7336 | function | `src/quiltwright/povgen.py.coalesce_mesh2.intern()` | src/quiltwright/povgen.py |
| 5 | 0.7333 | method | `Calibration.load()` | src/quiltwright/weave.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7597 | function | `fetch_archive()` | src/quiltwright/tvb_data.py |
| 2 | 0.7588 | function | `cache_dir()` | src/quiltwright/tvb_data.py |
| 3 | 0.7483 | function | `_read_member()` | src/quiltwright/tvb_data.py |
| 4 | 0.7408 | function | `dataset_cache_dir()` | src/quiltwright/cache.py |
| 5 | 0.7401 | function | `archive_path()` | src/quiltwright/tvb_data.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7693 | method | `QuiltSpec.n_views()` | src/quiltwright/quilt.py |
| 2 | 0.7514 | function | `_loadtxt()` | src/quiltwright/tvb_data.py |
| 3 | 0.7474 | function | `src/quiltwright/lfd.py.render_quilt.views()` | src/quiltwright/lfd.py |
| 4 | 0.746 | function | `_named_list()` | src/quiltwright/povgen.py |
| 5 | 0.7458 | function | `src/quiltwright/povgen.py.PovScene.bounds.visit()` | src/quiltwright/povgen.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7589 | function | `_matching_brace()` | src/quiltwright/povgen.py |
| 2 | 0.7512 | function | `sphere_sweeps_from_paths()` | src/quiltwright/povgen.py |
| 3 | 0.7494 | method | `Mesh2.sdl()` | src/quiltwright/povgen.py |
| 4 | 0.7459 | function | `src/quiltwright/povgen.py.coalesce_mesh2.block()` | src/quiltwright/povgen.py |
| 5 | 0.7443 | function | `src/quiltwright/povgen.py.Mesh2.sdl.block()` | src/quiltwright/povgen.py |

---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 2.8s*
