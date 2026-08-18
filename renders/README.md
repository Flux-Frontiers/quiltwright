# Reference renders

Output, not source. Everything regenerates from `pov-scenes/` plus the
scripts, but regeneration needs a POV-Ray install and patience, so what is
kept where follows weight:

| Directory | Contents | Kept |
|---|---|---|
| `stills/` | Full-quality single-frame references, one per scene | committed (~14 MB) -- the diffable record of what each scene looks like |
| `quilts/` | Looking Glass quilts, written here by the render scripts | release assets (25-40 MB each) -- rendered on CI by `release.yml`, or locally via `make release-assets` |
| `views/` | Per-view captures, test frames and experiments | local scratch, never committed |

`make stills`, `make quilts`, or per-scene targets (`make help`) drive all of
it.

Produced with POV-Ray 3.7 on Linux. See
[docs/pov-workflow.md](../docs/pov-workflow.md) for the procedure and the traps.

## stills/

Render each at **its own declared aspect** -- POV-Ray maps `right` to image
width and `up` to image height whatever pixel dimensions you ask for, so a
mismatched frame stretches the picture with no warning. The declared value per
scene is tabulated in the workflow doc.

| File | Scene | Aspect | Size |
|---|---|---|---|
| `bell_jar_bj.png` | `bell_jar/bj.pov` | 0.75 | 900×1200 |
| `bell_jar_bj_holo.png` | `bell_jar/bj_holo.pov` | 1.778 | 1920×1080 |
| `bell_jar_bj_portrait.png` | `bell_jar/bj_portrait.pov` | 0.5625 | 1080×1920 |
| `bell_jar_bj_black.png` | `bell_jar/bj_black.pov` | 0.75 | 900×1200 |
| `bell_jar_bdna.png` | `bell_jar/bdna.pov` | 0.75 | 900×1200 |
| `bell_jar_yinyang.png` | `bell_jar/yinyang.pov` | 1.25 | 1500×1200 |
| `bell_jar_bdna_variant.png` | `bell_jar/bdna/bdna.pov` | 0.5 | 600×1200 |
| `porin_3porin.png` | `porin/3porin.pov` | 1.778 | 1920×1080 |
| `museum.png` | `museum/museum.pov` | 1.778 | 1920×1080 |
| `museum_970211.png` | `museum/museum_970211.pov` | 1.333 | 1600×1200 |
| `museum_pg.png` | `museum/museum_pg.pov` | 1.25 | 1500×1200 |
| `lambda_main.png` | `lambda/lambda_main.pov` | 1.778 | 1920×1080 |

`bell_jar_wall_0.06.png` and `bell_jar_wall_0.09.png` are the comparison the
glass thickness was chosen from -- `BJ_WALL` in `bell_jar/bell_jar.inc`. 0.06 is
the default; 0.09 is visible but chunky and distorts the duplex behind it.
Setting it to 0 restores the original zero-thickness surface.

`museum/disc1.pov` is absent because it does not render on Linux -- it asks for
the standard includes in upper case. See the scene README.

`museum/museum_dark.pov` and `museum/worldmap.pov` are absent by choice. Both
render, and both remain in `pov-scenes/`; neither earns a reference still.

`porin/3porin2.pov` is absent because it renders nothing: it is the stock
POV-Ray scene template with `#include "3porin.inc"` appended, and that include
only `#declare`s `porin`. Until something instantiates it the frame is sky and
ground plane, so there is no reference still to keep.

The remaining stills here -- `st_helens.png`, `damavand.png`, `brain.png` and
`mouse_brain.png` -- come from the PyVista pipeline rather than POV-Ray, and so
have no `right` vector to match; they are rendered at the shape their scene is
composed for. See [docs/pyvista-datasets.md](../docs/pyvista-datasets.md).

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
