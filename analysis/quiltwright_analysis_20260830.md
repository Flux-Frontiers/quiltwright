> **Analysis Report Metadata**  
> - **Generated:** 2026-08-30T02:37:32Z  
> - **Version:** pycode-kg 0.21.4  
> - **Commit:** f1d3cf7 (develop)  
> - **Platform:** macOS 27.0 | arm64 (arm) | turing | Python 3.12.8  
> - **Graph:** 3974 nodes · 3523 edges (279 meaningful)  
> - **Included directories:** src  
> - **Excluded directories:** tests  
> - **Elapsed time:** 2s  

# quiltwright Analysis

**Generated:** 2026-08-30 02:37:32 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **quiltwright** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| [A] **Excellent** | **A** | 100 / 100 |

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 3974 |
| **Total Edges** | 3523 |
| **Modules** | 24 (of 24 total) |
| **Functions** | 172 |
| **Classes** | 27 |
| **Methods** | 56 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 1391 |
| CONTAINS | 255 |
| IMPORTS | 221 |
| ATTR_ACCESS | 969 |
| INHERITS | 11 |

---

## Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `to_pov()` | src/quiltwright/povgen.py | **9** |
| 2 | `_texture_suffix()` | src/quiltwright/povgen.py | **7** |
| 3 | `_vec()` | src/quiltwright/povgen.py | **7** |
| 4 | `sdl()` | src/quiltwright/povgen.py | **7** |
| 5 | `bridge_post()` | src/quiltwright/bridge.py | **6** |
| 6 | `focal_distance()` | src/quiltwright/povray.py | **6** |
| 7 | `focal_distance()` | src/quiltwright/povray.py | **6** |
| 8 | `enter_orchestration()` | src/quiltwright/bridge.py | **5** |
| 9 | `render()` | src/quiltwright/runreport.py | **5** |
| 10 | `parse_color()` | src/quiltwright/povgen.py | **4** |
| 11 | `n_views()` | src/quiltwright/quilt.py | **4** |
| 12 | `_read_member()` | src/quiltwright/tvb_data.py | **4** |
| 13 | `_resolve()` | src/quiltwright/tvb_data.py | **4** |
| 14 | `_require_pyvista()` | src/quiltwright/hld.py | **4** |
| 15 | `_require_pyvista()` | src/quiltwright/lfd.py | **4** |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

No extreme high fan-out functions detected. Well-balanced architecture.

---

## Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
| `src/quiltwright/povgen.py` | 29 | 12 | 1 | 1 | 0.33 |
| `src/quiltwright/povray.py` | 17 | 3 | 0 | 2 | 0.00 |
| `src/quiltwright/tvb_data.py` | 24 | 2 | 0 | 1 | 0.00 |
| `src/quiltwright/cycles.py` | 18 | 1 | 1 | 2 | 0.25 |
| `src/quiltwright/quilt.py` | 9 | 2 | 8 | 1 | 0.80 |
| `src/quiltwright/pymol.py` | 13 | 3 | 5 | 1 | 0.71 |
| `src/quiltwright/runreport.py` | 7 | 1 | 0 | 0 | 0.00 |
| `src/quiltwright/lfd.py` | 10 | 1 | 0 | 4 | 0.00 |
| `src/quiltwright/weave.py` | 3 | 2 | 1 | 1 | 0.33 |
| `src/quiltwright/hld.py` | 8 | 0 | 0 | 1 | 0.00 |

---

## Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 4)

```
sdl → _texture_suffix → sdl → _vec
```

**Chain 2** (depth: 3)

```
enter_orchestration → bridge_post → read
```

---

## Public API Surface

Identified public APIs (module-level functions with high usage).

| Function | Module | Fan-In | Type |
|----------|--------|--------|------|
| `get()` | src/quiltwright/weave.py | 15 | function |
| `run()` | src/quiltwright/povray.py | 11 | function |
| `to_pov()` | src/quiltwright/povgen.py | 9 | function |
| `replace()` | src/quiltwright/pymol.py | 8 | function |
| `read()` | src/quiltwright/tvb_data.py | 8 | function |
| `bridge_post()` | src/quiltwright/bridge.py | 6 | function |
| `enter_orchestration()` | src/quiltwright/bridge.py | 5 | function |
| `available()` | src/quiltwright/pymol.py | 4 | function |
| `parse_color()` | src/quiltwright/povgen.py | 4 | function |
| `Sphere()` | src/quiltwright/povgen.py | 3 | class |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 159 | 172 | [OK] 92.4% |
| `method` | 52 | 56 | [OK] 92.9% |
| `class` | 27 | 27 | [OK] 100.0% |
| `module` | 23 | 24 | [OK] 95.8% |
| **total** | **261** | **279** | **[OK] 93.5%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.253692 | 62 | `src/quiltwright/povgen.py` |
| 2 | 0.118877 | 32 | `src/quiltwright/povray.py` |
| 3 | 0.100768 | 29 | `src/quiltwright/tvb_data.py` |
| 4 | 0.092152 | 22 | `src/quiltwright/quilt.py` |
| 5 | 0.068758 | 23 | `src/quiltwright/cycles.py` |
| 6 | 0.066283 | 15 | `src/quiltwright/runreport.py` |
| 7 | 0.065851 | 10 | `src/quiltwright/weave.py` |
| 8 | 0.052951 | 17 | `src/quiltwright/pymol.py` |
| 9 | 0.030767 | 8 | `src/quiltwright/bridge.py` |
| 10 | 0.029243 | 12 | `src/quiltwright/lfd.py` |
| 11 | 0.022072 | 9 | `src/quiltwright/hld.py` |
| 12 | 0.017609 | 6 | `src/quiltwright/cli/cmd_wallpaper.py` |
| 13 | 0.016200 | 7 | `src/quiltwright/cli/cmd_bridge.py` |
| 14 | 0.015700 | 4 | `src/quiltwright/cli/options.py` |
| 15 | 0.015457 | 3 | `src/quiltwright/cache.py` |



---

## Code Quality Issues

- [WARN] `povgen.py` has 61 functions/methods/classes -- consider splitting into focused submodules
- [WARN] `povray.py` has 31 functions/methods/classes -- consider splitting into focused submodules

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- No god objects or god functions detected
- Good docstring coverage: 93.5% of functions/methods/classes/modules documented

---

## Recommendations

### Medium-term Refactoring
1. **Harden high fan-in functions** — `to_pov`, `_texture_suffix`, `_vec` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `get`, `run`, `to_pov`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## Inheritance Hierarchy

**11** INHERITS edges across **12** classes. Max depth: **1**.

| Class | Module | Depth | Parents | Children |
|-------|--------|-------|---------|----------|
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
|---|-----------|--------|---------|-------|-------|----------|---------|---------|------------|
| 1 | 2026-08-30 02:30:36 | develop | 0.21.4 | 3975 | 3522 | 93.5% | — | — | — |


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

No orphaned functions detected.
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000830 | function | `bridge_post` | src/quiltwright/bridge.py |
| 2 | 0.000671 | function | `to_pov` | src/quiltwright/povgen.py |
| 3 | 0.000619 | function | `enter_orchestration` | src/quiltwright/bridge.py |
| 4 | 0.000528 | function | `cache_dir` | src/quiltwright/tvb_data.py |
| 5 | 0.000525 | function | `_texture_suffix` | src/quiltwright/povgen.py |
| 6 | 0.000520 | function | `_vec` | src/quiltwright/povgen.py |
| 7 | 0.000474 | method | `RunReport.section` | src/quiltwright/runreport.py |
| 8 | 0.000454 | method | `Clearance.half_width` | src/quiltwright/povray.py |
| 9 | 0.000447 | function | `parse_color` | src/quiltwright/povgen.py |
| 10 | 0.000445 | method | `QuiltSpec.n_views` | src/quiltwright/quilt.py |
| 11 | 0.000445 | method | `_HasLens.fov` | src/quiltwright/povray.py |
| 12 | 0.000443 | method | `PovCamera.focal_distance` | src/quiltwright/povray.py |
| 13 | 0.000443 | method | `_HasLens.focal_distance` | src/quiltwright/povray.py |
| 14 | 0.000435 | function | `_osascript` | src/quiltwright/cli/cmd_wallpaper.py |
| 15 | 0.000430 | function | `_read_member` | src/quiltwright/tvb_data.py |
| 16 | 0.000430 | function | `_resolve` | src/quiltwright/tvb_data.py |
| 17 | 0.000421 | function | `_triple` | src/quiltwright/cycles.py |
| 18 | 0.000395 | function | `_matching_brace` | src/quiltwright/povgen.py |
| 19 | 0.000391 | function | `_run` | src/quiltwright/runreport.py |
| 20 | 0.000384 | function | `_require_pyvista` | src/quiltwright/hld.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7349 | method | `Mesh2.__post_init__` | src/quiltwright/povgen.py |
| 2 | 0.7326 | method | `Clearance.__post_init__` | src/quiltwright/povray.py |
| 3 | 0.7295 | function | `load_connectivity` | src/quiltwright/tvb_data.py |
| 4 | 0.7268 | function | `src/quiltwright/povgen.py.coalesce_mesh2.intern` | src/quiltwright/povgen.py |
| 5 | 0.7266 | method | `Calibration.load` | src/quiltwright/weave.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7601 | function | `fetch_archive` | src/quiltwright/tvb_data.py |
| 2 | 0.7589 | function | `cache_dir` | src/quiltwright/tvb_data.py |
| 3 | 0.75 | function | `_read_member` | src/quiltwright/tvb_data.py |
| 4 | 0.7404 | function | `dataset_cache_dir` | src/quiltwright/cache.py |
| 5 | 0.7395 | function | `archive_path` | src/quiltwright/tvb_data.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.77 | method | `QuiltSpec.n_views` | src/quiltwright/quilt.py |
| 2 | 0.7519 | function | `_loadtxt` | src/quiltwright/tvb_data.py |
| 3 | 0.7481 | function | `src/quiltwright/lfd.py.render_quilt.views` | src/quiltwright/lfd.py |
| 4 | 0.7461 | function | `_named_list` | src/quiltwright/povgen.py |
| 5 | 0.7458 | function | `src/quiltwright/povgen.py.PovScene.bounds.visit` | src/quiltwright/povgen.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7595 | function | `_matching_brace` | src/quiltwright/povgen.py |
| 2 | 0.7513 | function | `sphere_sweeps_from_paths` | src/quiltwright/povgen.py |
| 3 | 0.7494 | method | `Mesh2.sdl` | src/quiltwright/povgen.py |
| 4 | 0.7459 | function | `src/quiltwright/povgen.py.coalesce_mesh2.block` | src/quiltwright/povgen.py |
| 5 | 0.7443 | function | `src/quiltwright/povgen.py.Mesh2.sdl.block` | src/quiltwright/povgen.py |



---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 2.4s*
