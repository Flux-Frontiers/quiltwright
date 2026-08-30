# Reference renders

Output, not source. Everything regenerates from `pov-scenes/` plus the
scripts, but regeneration needs a POV-Ray install and patience, so what is
kept where follows weight.

The presented set is **not** here: it lives at the top level in
[`gallery/`](../gallery/), cataloged in [docs/gallery.md](../docs/gallery.md).
It is the work, not a build artifact, and keeping it under `renders/` made it
look like one. Everything in *this* directory is output.

| Directory | Contents | Kept |
|---|---|---|
| `stills/` | Working renders you are currently looking at | local scratch, never committed -- promote to [`../gallery/`](../gallery/) what earns a place |
| `quilts/` | Looking Glass quilts, written here by the render scripts | release assets (25-40 MB each) -- rendered on CI by `release.yml`, or locally via `make release-assets` |
| `reports/` | Run reports -- one Markdown provenance record per full quilt | committed (~2 kB each) -- the only record of how a gitignored quilt was made |
| `views/` | Per-view captures, test frames and experiments | local scratch, never committed |

`make gallery`, `make quilts`, or per-scene targets (`make help`) drive all of
it.

Produced with POV-Ray 3.7 on Linux. See
[docs/pov-workflow.md](../docs/pov-workflow.md) for the procedure and the traps.

## reports/

`make quilt-<name>` writes one, or pass `--report` to either render script
(`--report PATH` to place it yourself). It records the provenance a PNG cannot
carry: the scene file *and its SHA-256*, the repository commit and whether the
tree was dirty, the camera and measured depths, the depth budget verbatim as
printed, wall-clock timing, and the output's own digest.

The scene hash matters more than the commit. Composing a scene means rendering
against an edited working copy, so the commit alone can name a tree the render
never saw -- the header says `+ uncommitted changes` when that is the case, and
the scene digest pins the actual input either way.

## quilts/

Gitignored like everything else here -- at every depth, since the `*_qs...`
patterns carry no slash -- and they land here when you render them:

```bash
python scripts/render_still_life_hologram.py bell-jar          # 16" landscape, ~9 min
python scripts/render_still_life_hologram.py porin             # ~18 min
python scripts/render_still_life_hologram.py porin --device portrait
```

| Quilt | Device | Grid | Tile | Cone | Size |
|---|---|---|---|---|---|
| `bell-jar_qs8x6a1.77778.png` | 16" landscape | 8×6, 48 views | 960×720 | 35° | 25 MB |
| `porin_qs8x6a1.77778.png` | 16" landscape | 8×6, 48 views | 960×720 | 35° | 37 MB |
| `porin_qs8x6a0.75.png` | Portrait | 8×6, 48 views | 420×560 | 35° | 13 MB |

The filename carries the metadata Looking Glass software parses: `_qs`, columns
`x` rows, `a` aspect. The 35° cone is the script's cap, not the 16" panel's
native 50° -- at 50° the sea reaches 14.3 px of adjacent-view disparity against
a ~8 px ghosting threshold. `--view-cone 50` opts back in.

One thing to expect from a fresh render: a **bell-jar quilt rendered before
the `BJ_WALL` glass fix** will not match earlier stills -- the jar was a
zero-thickness surface until then. The porin title and signature, once
camera-pinned overlays that left the frame during the sweep, now sit at scene
depth (900 units, just ahead of the barrel) and ride the sweep with everything
else.
