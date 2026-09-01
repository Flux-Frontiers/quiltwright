# quiltwright Improvement Suggestions

> **Source:** PyCodeKG `analyze_repo` + CodeRank / framework hubs / snippet packs  
> **Generated:** 2026-09-01  
> **Commit:** d0b1e0e (`develop`)  
> **Package:** quiltwright 0.10.1  
> **Graph:** 4,301 nodes · 3,797 edges · 306 meaningful · docstring coverage 94.1%  
> **Quality grade:** A (98.2 / 100)

Overall the codebase is in excellent shape: no circular dependencies, no god functions,
shallow inheritance (max depth 1), and strong documentation. The suggestions below are
incremental hardening and structural cleanup, not emergency fixes.

---

## Snapshot vs prior analysis (2026-08-30)

| Metric | 2026-08-30 | 2026-09-01 | Delta |
|--------|------------|------------|-------|
| Meaningful nodes | 279 | 306 | +27 |
| Functions | 172 | 192 | +20 |
| Modules | 24 | 26 | +2 |
| Docstring coverage | 93.5% | 94.1% | +0.6 pp |
| Quality score | 100 | 98.2 | Protocol orphan false-positive |

The score drop is almost entirely the new orphan warning on `_HasLens` (see below) --
not a real regression.

---

## Architectural spine (where risk concentrates)

**Framework hubs** (0.6×SIR + 0.4×connectivity):

| Rank | Module | Lines | Role |
|-----:|--------|------:|------|
| 1 | `povgen.py` | 1689 | SDL primitives, mesh coalesce, camera/lights helpers |
| 2 | `povray.py` | 1292 | POV-Ray quilt backend + depth budget |
| 3 | `tvb_data.py` | 842 | Zenodo fetch + surface/connectome loaders |
| 4 | `cycles.py` | 1422 | Blender Cycles quilt backend |
| 5 | `quilt.py` | 465 | QuiltSpec / presets / assembly (high cohesion 0.80) |

**Highest CodeRank nodes** (global structural importance):

1. `bridge_post` / `enter_orchestration` -- Looking Glass Bridge HTTP
2. `to_pov` / `_texture_suffix` / `_vec` -- POV coordinate and SDL emission core
3. `cache_dir` / `_read_member` / `_resolve` -- TVB data cache path
4. `camera_block` / `PovCamera.focal_distance` -- POV camera math
5. `QuiltSpec.n_views` -- quilt geometry contract

These are the symbols whose contracts should stay stable across releases.

---

## Priority 1 -- Quick wins (low risk, clear payoff)

> **Done** on `develop` (2026-09-01): `_HasLens` docstring clarified;
> `require_pyvista` and `triple` live in `runtime`; `cli/__init__.py` documented.

### 1.1 Do not delete `_HasLens` (false orphan)

PyCodeKG flags `povray._HasLens` as dead code (0 callers). It is a typing
`Protocol` used as the annotation on `depth_budget` and `format_depth_budget`.
Protocols never appear as CALLS targets, so the orphan detector misclassifies them.

`lfd._Lens` exists specifically to satisfy this protocol without constructing a
`PovCamera`. Keep `_HasLens`. Optional tidy-up: document the protocol explicitly
in a one-line `# typing: used by depth_budget` comment, or fold it into
`QuiltCamera` if you want a single lens protocol (see 2.2).

### 1.2 Deduplicate `_require_pyvista`

Identical copies live in:

- `lfd.py:122`
- `hld.py:62`
- `tvb_data.py:683`

Extract one helper (e.g. `quiltwright.runtime.require_pyvista(fn_name)`) and call
it from all three. `runtime.py` is already 37 lines and exists for light shared
machinery. Same pattern could absorb `dynamic._require_heif` later if a second
HEIF site appears.

### 1.3 Deduplicate `_triple`

Near-identical helpers:

- `povray._triple`
- `cycles._triple`

Both coerce an iterable of floats to `tuple[float, float, float]`. A single
private helper on `quilt` (or `runtime`) would remove a quiet drift risk --
especially since `PovCamera.aimed` and `CyclesCamera.aimed` already claim to
share a contract.

### 1.4 Fill the remaining docstring gaps

Coverage is already 94.1%. The undocumented nodes are mostly nested locals
inside `Mesh2.sdl`, `coalesce_mesh2`, `lights_from_bounds`, and
`PovScene.bounds` (`block`, `wind`, `intern`, `visit`, `place`). Those do not
need public docs, but the one missing **module** docstring
(`cli/__init__.py`, currently empty) is a free point and helps DocKG / agents.

---

## Priority 2 -- Structural cleanup (medium effort)

> **Light P2 done** (option B, 2026-09-01): `HasLens` lives in `quilt.py`;
> `_HasLens` removed from `povray`; `aimed` parity tests in `test_camera.py`.
> Module splits (2.1) deferred -- revisit only if a real edit fights a file.

### 2.1 Split the oversized hubs

PyCodeKG warns on module size. Suggested seams that match existing comments
and call patterns:

**`povgen.py` (1689 lines, 61 defs) -- highest priority**

| Proposed submodule | Contents |
|--------------------|----------|
| `povgen/primitives.py` | `Primitive`, `Sphere`, `Cylinder`, `Box`, `Union`, `Instance`, `Mesh2`, `SphereSweep`, textures/finishes |
| `povgen/mesh.py` | `coalesce_mesh2`, brace parsers, `_matching_brace`, `_named_list` |
| `povgen/scene.py` | `PovScene`, `swept_scene`, `ground_slab`, lights helpers |
| `povgen/coords.py` | `to_pov`, `_vec`, FOV converters, `pov_camera_from_*` |

Keep `povgen/__init__.py` as a thin re-export so `from quiltwright.povgen import Sphere`
and the lazy `__init__` map stay unbroken.

**`povray.py` (1292 lines) -- second priority**

Natural split already mirrored by section comments:

- camera + clearance + depth budget (`PovCamera`, `Clearance`, `_HasLens`, `depth_budget`, `format_depth_budget`)
- render orchestration (`render_pov_quilt`, wrapper writing, lighting append)
- subprocess / ini helpers

**`cycles.py` (1422 lines) -- watch list**

Not flagged as hard as `povgen`/`povray` by definition count, but line count is
comparable. Split when the next Cycles feature lands: camera/lighting vs render
driver vs glTF export.

Do **not** split `quilt.py` -- cohesion 0.80 and inbound fan make it the stable
core. Splitting it would churn every backend.

### 2.2 Unify the lens / camera protocol surface

Today there are three overlapping shapes:

| Type | Module | Purpose |
|------|--------|---------|
| `QuiltCamera` | `quilt.py` | Full sweep camera (`location`, `look_at`, `fov`, `focal_distance`, `basis`) |
| `_HasLens` | `povray.py` | Subset: `fov` + `focal_distance` for depth budget |
| `_Lens` | `lfd.py` | Dataclass that satisfies `_HasLens` |

Suggestion: promote `_HasLens` to `quilt.HasLens` (or make `QuiltCamera` the
only protocol and type `depth_budget` against a `Protocol` defined next to it).
Then delete the private duplicate and keep `_Lens` as the cheap namespace.

### 2.3 Align `aimed` implementations

`PovCamera.aimed` and `CyclesCamera.aimed` are documented as twins but live as
separate copies (~50 lines each). Options, in increasing ambition:

1. Shared pure function `aim_lookat_camera(location, aim, *, fov, focal_distance, lateral_shift, basis_fn, ctor)` in `quilt.py`
2. Keep both methods as thin wrappers that call that helper
3. Leave as-is but add a parity test that asserts identical geometry for the same inputs under each handedness

Option 3 alone is worth doing even without a merge -- `aimed` is already in the
"unused in production, tested" list, so the test suite is the contract.

---

## Priority 3 -- API and contract hygiene

### 3.1 Stabilize the high fan-in public surface

Symbols with the most inbound edges (and/or CodeRank) that belong in the
breaking-change policy:

| Symbol | Why |
|--------|-----|
| `to_pov` | Coordinate convention; 9 callers inside + downstream scene writers |
| `QuiltSpec` / `n_views` / `QUILT_PRESETS` | Quilt geometry contract for every backend |
| `bridge_post` / `enter_orchestration` | Bridge HTTP; also used by CLI and cast flows |
| `assemble_quilt` / `save_quilt` / `render_quilt` | Primary user-facing path |
| `parse_color` | Shared by povgen consumers |

These are already lazy-exported from `__init__.py`. Worth an explicit
"public API" section in `docs/api/` or a short ADR noting that private
`_vec` / `_texture_suffix` are *not* semver-guaranteed even though they have
high fan-in.

### 3.2 Review test-only public methods

Unused in production but exercised by tests (likely intentional API):

- `PovCamera.aimed`, `CyclesCamera.aimed`
- `PovCamera.cone`
- `AppearanceMap.from_appearance`
- `RunReport.pre`, `RunReport.table`
- `QuiltSpec.with_grid`

Action: confirm each is mentioned in docs or `__all__` / lazy map. If a method
exists only for tests, either promote it (document it) or keep the test but
stop treating it as public surface.

### 3.3 Cache helpers: one story

`tvb_data.cache_dir` ranks high in CodeRank; `cache.dataset_cache_dir` is the
sibling for other downloads. A short module docstring cross-link (or a single
`quiltwright.cache` entry point that TVB delegates to) would make the two-cache
story obvious to agents and humans.

---

## Priority 4 -- Longer-term architecture

### 4.1 Backend matrix, not accidental twins

Three quilt backends share the same geometric contract (off-axis sweep,
focal plane, FOV dolly, depth budget) but implement framing in three places:

- `lfd.render_quilt` / `camera_frame` / `scene_depths`
- `povray` camera_block + wrappers
- `cycles` shift_x + `cycles_camera_from_plotter`

`cycles_camera_from_plotter` already imports `lfd.camera_frame` -- that is the
right direction. Next step: extract a renderer-agnostic framing helper
(FOV narrow + dolly + zoom) used by LFD, Cycles, and any POV path that starts
from a plotter (`pov_camera_from_plotter` already exists in `povgen`).

### 4.2 Layer lint (optional)

Import direction that already holds in practice and is worth freezing:

```
quilt  (geometry, QuiltSpec, QuiltCamera)
  ^
  |-- povgen, weave, bridge, runtime, cache
  |
backends: lfd, povray, cycles, hld
  ^
  |-- cli/*, scripts/*
scene sources: tvb_data, pymol, dynamic
```

A simple import-linter / grimp contract in CI would stop a future CLI command
from reaching into `povgen` internals the wrong way. Only worth adding once a
split of `povgen` lands.

### 4.3 Snapshot cadence

One snapshot exists (2026-08-30). After the next structural change (povgen
split or `_require_pyvista` extract), save a snapshot so `snapshot_diff`
can quantify the cleanup. The post-commit hook via `pycodekg install-hooks`
would make that automatic.

---

## What not to do

- **Do not** chase the 98.2 score by deleting `_HasLens` -- it is a typing Protocol.
- **Do not** split `quilt.py` -- it is the high-cohesion spine every backend imports.
- **Do not** merge `lfd` and `hld` -- different display contracts (quilt vs 2-D video);
  sharing `_require_pyvista` is enough.
- **Do not** over-abstract the three `aimed` methods into a class hierarchy;
  a shared pure function (or parity tests) matches the existing dataclass style.

---

## Suggested work order

| # | Item | Effort | Impact |
|---|------|--------|--------|
| 1 | Extract `require_pyvista` to `runtime` | S | Removes 3-way drift |
| 2 | Module docstring on `cli/__init__.py` | XS | Coverage + agent UX |
| 3 | Shared `_triple` + parity test for `aimed` | S | Contract safety |
| 4 | Promote / relocate `_HasLens` next to `QuiltCamera` | S | Clears false orphan, clearer API |
| 5 | Split `povgen` into package with re-exports | M | Addresses top hub warning |
| 6 | Extract shared FOV-dolly framing helper | M | Backend consistency |
| 7 | Split `povray` camera/depth vs render driver | M | Second hub warning |
| 8 | Import-layer lint after splits | S | Prevents regression |

Items 1--4 are safe on `develop` without a version bump beyond patch.
Items 5--7 deserve their own PRs and a minor version if any import paths change
for external consumers (mitigated by keeping package-level re-exports).
