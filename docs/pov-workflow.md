# Taking an archive scene to the glass

**Companion to**: [povray.md](povray.md), which explains the *mechanism* — the
off-axis camera, the disparity formula, the clearance constraint. This page is
the *procedure*: the order of operations that gets a scene written in 1997 from
"won't parse" to a quilt that fuses, and what to check at each step so you find
out before the ray-tracer has spent an hour.

Worked end to end on three scenes from the archive — the museum interior, the
bell-jar still life, and porin — which between them cover the two cases that
behave differently: an enclosed room and an open subject on a backdrop.

---

## The rule that shapes everything else

**The scene is read-only.** Not as a matter of taste — it is what makes the
whole approach viable. Every scene in `pov-scenes/` was composed and lit by
someone who is not going to re-derive their choices for a display that shipped
twenty-five years later, and a scene you have edited is a scene whose original
you can no longer diff against. So everything below is either a command-line
argument or a wrapper scene that `#include`s the original and appends to it.

Nothing in this workflow modifies a `.pov` file, including the steps that look
like they must.

---

## 1. Make it parse

Three things break first, in this order.

**The language version.** POV-Ray 2.x `#declare`s carry no trailing semicolon,
and 3.5+ rejects them outright. The scene may declare its own version — most of
the museum family opens with `#version 3.0` — in which case you are done. If it
does not, pin it from the command line:

```bash
povray +I3porin.pov +MV3.1 ...
```

`+MV3.1` is the non-destructive form of the `#version 3.1;` prepend described in
[pdb2pov.md](pdb2pov.md#working-with-v119). Same effect, and the file stays as
it was written. It reaches the quilt renderer through `extra_args`:

```python
render_pov_quilt(scene, spec, camera, extra_args=["+MV3.1"])
```

You will still get `Possible Parse Error` warnings — dozens of them, one per
2.x-syntax `#declare` in the shared include tree. They are warnings. The render
is correct.

**Include paths.** Scenes from the 1990s reference includes by bare filename,
and POV-Ray searches its working directory and the `+L` paths, *not* the
including file's directory. Point `+L` at the shared include tree as well as
POV-Ray's own:

```bash
povray +Ibj.pov +L/usr/share/povray-3.7/include +L../myinclude
```

A missing include fails with a line number in the *wrapper*, not the scene,
which is confusing the first time.

**Include case, on Linux.** These scenes were written on case-insensitive
filesystems, so their `#include` lines use whatever case felt natural at the
time. POV-Ray ships its standard library lower case, and on Linux
`#include "CHARS.INC"` is simply a missing file. `museum/disc1.pov` asks for
eight of them in upper case and does not render on Linux at all, while being
perfectly fine on the Mac it was written on. Diagnose it before assuming a
file is genuinely absent — `ls` the include directory case-insensitively.

A real absence looks the same from the error message. `museum/worldmap.pov`
wanted `worldmap.inc`, which had simply not been carried across with the rest
of the museum tree and had to be fetched from the archive.

**Quality, if there is glass.** POV-Ray disables transparency and refraction
below `+Q8`. A cheap probe of a scene with windows reports a room with no
windows; a cheap probe of a bell jar reports a solid dome. Keep `+Q11` for
anything you intend to measure from.

---

## 2. Render the still at the scene's own aspect

This one is worth its own step because it fails silently and looks like a
modelling error.

POV-Ray builds its frame from `right` and `up`. It maps `right` to the image
width and `up` to the image height **regardless of the pixel dimensions you
ask for**, so rendering into a frame whose aspect differs from `|right|/|up|`
stretches the picture rather than cropping or letterboxing it. There is no
warning.

Read the ratio out of the scene before you pick `+W`/`+H`:

```bash
grep -n 'right\|up\|#declare ASPECT' yinyang.pov
```

| Scene | declares | aspect | renders correctly at |
|---|---|---|---|
| `bell_jar/bj.pov` | `right <3/4,0,0>` | 0.75 | 900×1200 |
| `bell_jar/bj_black.pov` | `right <3/4,0,0>` | 0.75 | 900×1200 |
| `bell_jar/bdna.pov` | `right <3/4,0,0>` | 0.75 | 900×1200 |
| `bell_jar/yinyang.pov` | `right <5/4,0,0>` | 1.25 | 1500×1200 |
| `bell_jar/bdna/bdna.pov` | `right <4/8,0,0>` | 0.5 | 600×1200 |
| `bell_jar/bdna/bdna_anim.pov` | `right <5/8,0,0>` | 0.625 | 750×1200 |
| `porin/3porin.pov` | `right <ASPECT,0,0>`, `ASPECT = 16/9` | 1.778 | 1920×1080 |
| `porin/3porin2.pov` | `right 4/3*x` | 1.333 | 1600×1200 |
| `museum/museum.pov` | `ASPECT = HDTV` | 1.778 | 1920×1080 |
| `museum/museum_dark.pov` | `right <4/3,0,0>` | 1.333 | 1600×1200 |
| `museum/museum_970211.pov` | `ASPECT = PC_ASPECT` | 1.333 | 1600×1200 |
| `museum/museum_pg.pov` | `ASPECT = 5/4` | 1.25 | 1500×1200 |
| `museum/disc1.pov` | `right 4/3*x` | 1.333 | 1600×1200 |

Three of those need care beyond reading the first `right` in the file.
`museum_970211.pov` declares `ASPECT` twice and the first is commented out;
`bdna/bdna.pov` and `bdna/bdna_anim.pov` each declare several cameras at
different aspects and instantiate one at the bottom — `original_camera` at 0.5
and `simple_camera` at 0.625 respectively. Strip comments and find the
instantiated camera, not the first declared one.

Rendered at 960×1200 — an aspect of 0.8 — `yinyang.pov` squeezes its 1.25-wide
frustum by 36%, and the result reads unmistakably as vertical stretch: the bell
jars come out as tall ellipsoids. `bj.pov` rendered into the same frame is off
by only 6% and looks fine, which is exactly why the mistake survives.

**This does not apply to quilts.** `camera_block()` emits its own `right` and
`up` from the quilt spec's aspect, and POV-Ray uses the last camera it parses,
so the scene's `ASPECT` is overridden. Only stills care.

---

## 3. Read the scene's camera

The hologram wants the scene's own viewpoint and the scene's own lens — see
povray.md § 2 for why narrowing the FOV makes ghosting *worse* rather than
better. Three values to recover:

**Eye and aim** come straight off the active `camera { }` — but "active" needs
care in a scene with a dozen declared cameras behind `#if` flags. POV-Ray uses
the last camera it *parses*, so evaluate the flags at the top of the file:

```bash
grep -n '^#declare [A-Z_]* *=' museum_pg.pov | head -20   # the flags
grep -n 'camera *{[a-z_]*}' museum_pg.pov                 # the choices
```

For both museum cuts, `ORIGINAL`, `OUTSIDE_VIEW` and `DO_LOGO_VIEW` are all
false, so the live camera is `camera_zdna3` — not the `camera_zdna` that
appears first in the file.

**Vertical FOV** is what `PovCamera` wants, and POV-Ray does not state it
directly. For a camera that sets `direction` and `up` explicitly:

```
vertical FOV = 2 · atan( |up| / 2 / |direction| )
```

With the near-universal `direction <0,0,1>` and `up <0,1,0>` that is
2·atan(0.5) = **53.13°**, which is where the recurring number in these scripts
comes from.

The trap: **if the camera sets `angle`, it overrides `|direction|`** — POV-Ray
rescales the direction vector so `angle` becomes the *horizontal* FOV. Then

```
|direction| = (|right| / 2) / tan(angle / 2)
```

and you feed the vertical FOV derived from *that* into `PovCamera`. Reading
`direction <0,0,1>` off a camera that also says `angle 75` and concluding 53.13°
gives you a lens 10° too narrow, and every disparity downstream is wrong.

---

## 4. Measure the depth range

Guessing the near and far depths costs a render to discover; measuring them
costs a few minutes. [`scripts/measure_depth_range.py`](../scripts/measure_depth_range.py)
slides an opaque, self-lit plane along the view axis and scores each frame for
how much geometry remains in front of it — a cumulative depth histogram of the
shot.

```bash
python scripts/measure_depth_range.py \
    --scene pov-scenes/porin/3porin.pov \
    --include-path pov-scenes/myinclude \
    --eye 0,0,-1100 --aim 0,0,0 --fov 53.13 \
    --min-distance 700 --max-distance 1600 \
    --pov-arg +MV3.1
```

Two conditions on the measurement, both learned expensively:

- **Probe through the camera you will render with**, not the scene's own. If
  the hologram's eye is shifted or re-aimed, the depths through it differ.
- **Probe at `+Q8` or above**, per step 1.

`--min-distance` exists because a scene composed at another scale should not
spend two hundred probes in the empty space in front of itself. Porin's subject
sits 1100 units out; the museum's default grid would put 90% of its samples
before the scene starts.

---

## 5. Read the knee when the backdrop never closes

The museum's rule — *far depth is where 95% of occludable content is accounted
for* — works because a room has walls. The sweep plane eventually gets behind
everything, the curve flattens, and the 95% point is meaningful.

**An open backdrop never closes.** A sea running to the horizon keeps eating a
little more of the frame at every distance, so the curve never flattens and the
95% criterion returns the end of the sweep. Run unmodified against both still
lifes it reports `FAR_DEPTH = 5000` — the sentinel — for scenes whose subjects
are 60 and 500 units deep respectively.

The fix is to read the knee. The backdrop's contribution is linear in distance
over the far tail, so fit that tail, subtract it, and apply the 95% rule to what
is left:

```python
import numpy as np
d, f = np.array(distances), np.array(fractions)      # from sweep()
tail = d > backdrop_only_beyond                      # eyeball it from the curve
slope, icept = np.polyfit(d[tail], f[tail], 1)       # the backdrop's creep
subject = f - (slope * d + icept)
subject -= subject[d < first_geometry].mean()        # zero the front
total = subject[tail].mean()                         # the subject's share
far = d[np.argmax(subject >= 0.95 * total)]
```

| | subject share of frame | backdrop creep | near | far (95% of subject) |
|---|---|---|---|---|
| `bj.pov` | 35.1% | 0.121 %/unit | 72 | 130 |
| `3porin.pov` | 13.2% | 0.020 %/unit | 790 | 1265 |

Porin's 790 bounds *the barrel*. Read the next section before treating a range
like this as the scene's.

The check that the numbers are honest: the focal plane they imply should land
near the distance the scene's author composed at. The harmonic means are 92.7
and 972.6 against composed aim distances of 96.5 and 1100 — close enough to
believe, and different enough to be worth having measured.

### Watch for content the sweep cannot serve at all

Before trusting a range, look at what sits in front of `--min-distance`. The
sweep only reports what it passes through, so anything nearer than where you
started is silently absent from the numbers — and near content is exactly what
blows a depth budget.

Porin had some. Its "Porin" title and the `E. G. Suchanek, '97` signature were
extruded text translated to `z = -1088` and `-1090`, against a camera at
`z = -1100`: **10 to 12 units from the eye**, while the barrel they annotate is
850 to 1265 units out. They were camera-pinned overlays, not scene content, and
sweeping from 700 stepped straight over them. A second sweep from 5 finds such
content immediately — 0.9% of the frame appearing at 12 units and flat
thereafter, which is the signature of a near overlay with nothing behind it.

No focal plane serves both. At `Z = 972.6`, content at 12 units moves 0.53
image-plane units per 6.5 units of eye travel against a half-frame of 0.375 —
so it does not ghost, it **leaves the frame**, and it is gone by the second
view of the sweep.

The cure is geometric: scaling an overlay *about the camera* preserves its
apparent size and position in the centre view exactly while moving it to any
depth you choose. Porin's texts are now scaled ×90 and ×75 out to **900 units**
— just ahead of the barrel's leading loops, floating at the waterline — so
they ride the sweep with everything else and the quilt carries them. The bell
jar's "DNA Under Glass" lettering never needed this: it is modelled on the
pedestal at scene depth.

**The general check**: if a scene has a title, a signature, a logo or a border,
find out whether it is *in* the scene or *on the lens* before you measure. Grep
for `text {` and read the translate.

---

## 6. Clearance, but only if it is an interior

This is the step that separates the two cases, and it is the one that costs an
hour when skipped.

The quilt sweeps the eye laterally by `focal_distance · tan(cone/2)`. For an
open subject that space is empty and the display's own view cone is fine. Inside
a room it is furniture and walls, and the failure is quiet — the centre view,
the one you preview, is perfect while the outer views render the unlit back of
a wall. Measure the corridor and derive the cone from it; povray.md § 3 has the
procedure and `Clearance` implements it.

| | enclosure | eye sweep | cone |
|---|---|---|---|
| `museum.pov` | walls at −18 / +8 | ±14.8 units | 26.4°, clearance-limited |
| `bj.pov` | open | ±29.2 units | 35°, the display's own |
| `3porin.pov` | open | ±306.7 units | 35°, the display's own |

Porin's ±307-unit sweep sounds alarming and is not: the scene is 11× the
museum's scale, and there is nothing out there to hit.

---

## 7. Print the budget before spending the hour

`format_depth_budget()` costs nothing and reports the two failures that cost
the most — a blown disparity budget and a sweep that leaves the room:

```
  focal plane      92.7 units
  view cone        35.0 deg over 48 views
  eye sweep        +/-29.2 units
  adjacent-view disparity:
    nearest geometry       72.0   2.16 px
    focal plane            92.7   0.00 px
    structured far        130.0   2.16 px
    sea and sky (infinite)      inf   7.51 px  <- soft
```

Roughly 4–5 px is the practical ceiling and past ~8 px expect visible ghosting.
All three scenes land in the same shape: subject comfortably inside the budget,
backdrop flagged soft and left that way on purpose, because it is low-contrast
and paying for it would push the subject off the glass.

| Scene | device | tile | subject | backdrop |
|---|---|---|---|---|
| `museum.pov` | 16" landscape | 960×720 | 3.68 px | 7.19 px |
| `bj.pov` | Portrait | 420×560 | 2.16 px | 7.51 px |
| `3porin.pov` | Portrait | 420×560 | 1.74 px | 7.51 px |

Note that the budget is a property of the *device*, not just the scene:
disparity scales with tile height, so a quarter-size preview genuinely has a
quarter of the disparity. Composition and view validity transfer from a
preview; the ghosting margin does not.

**A preset's native cone is not a target.** § 6 said an open scene can use the
display's own cone because nothing encloses it. That is true of *clearance* and
false of *disparity*. The 16" Landscape declares 50°, and on its 720 px tiles
the bell jar comes out at 4.10 px on the subject — at the ceiling — and 14.29 px
on the sea, nearly double where ghosting gets obvious. The same scene at the
documented 35° standard is 2.77 and 9.66. Nothing bounded the cone, so it had to
be bounded by the budget instead, and `render_still_life_hologram.py` now caps
it at 35° and says so. The cost is look-around, not sharpness.

The general point: an open scene has no wall to run into, which makes it easy to
assume the sweep is free. It is not — it is paid for in disparity, and on a wide
panel the bill arrives at the backdrop.

---

## 8. Render, then verify the parallax

```bash
python scripts/render_still_life_hologram.py bell-jar --preview   # ~40 s
python scripts/render_still_life_hologram.py bell-jar             # 194 s
```

Quilts repay harder anti-aliasing than stills — each view aliases differently
and the display interpolates between them, so edge noise reads as shimmer
rather than grain. `+A0.05 +AM2 +R4` is the house setting; `+A0.1` roughly
halves the cost for previews you still want to look at.

Then confirm the render is actually off-axis rather than toed-in, because both
produce plausible individual frames. Near and far features must shift in
**opposite** directions about a stationary focal plane. povray.md § 4 has the
cross-correlation method and the museum's measured numbers.

---

## 9. If the consumer is not a panel

Steps 1–8 are about getting the geometry right, and none of them change when
the output is going somewhere other than a Looking Glass. A hologram printer or
a lenticular interlacer wants the views as **separate frames** rather than
tiled, which is `render_pov_views()` and a single-row spec — a quilt grid is
`columns × rows` and cannot express a prime view count, which is exactly what
LitiHolo's published specification asks for (23):

```python
from quiltwright import (
    LITIHOLO_SWEEP, PovCamera, format_depth_budget, render_pov_views,
)

camera = PovCamera.aimed(location=EYE, aim=AIM, fov=FOV,
                         focal_distance=FOCAL)

# Print the budget first — see below. This costs nothing.
print(format_depth_budget(LITIHOLO_SWEEP, camera, DEPTHS))

paths = render_pov_views("risedronate.pov", LITIHOLO_SWEEP, camera, "sweep/")
# -> sweep/view000.png ... sweep/view022.png, view 0 leftmost
```

**The budget step is not optional advice here.** `LITIHOLO_SWEEP` is 23 views
over 45°, which is **2.05° between adjacent views** against **0.74°** on a
Portrait quilt — about 2.7× coarser sampling. Everything § 7 says about
disparity applies with less margin, not more, and the preset's 2000 px tile is
taller than anything in the device table, so the same scene reports larger px
figures than it would on a panel. Read the report before spending the render.

Then verify the parallax exactly as § 8 does. The frames are ordinary PNGs in
view order, so the same cross-correlation check applies: near and far features
must shift in opposite directions about a stationary focal plane.

What this is *not* is a verified printer input. Quiltwright emits a sweep
matching the published specification — 23 viewzones, 45° lateral, horizontal
parallax only. No file has been through the printer's software, and whether a
hogel slicer expects these off-axis frusta or the toe-in circular arc a 2003
submission of one of these scenes used is an open question. Both caveats are in
[lfd.md](lfd.md).

---

## Checklist

1. `#version` present? If not, `+MV3.1`.
2. `+L` at the shared include tree. `+Q11` if there is glass.
3. Still renders: match `+W`/`+H` to the scene's `right`/`up` ratio.
4. Active camera: evaluate the `#if` flags. FOV from `direction` — unless
   `angle` is set, in which case from `angle` and `right`.
5. Plane-sweep the depth range through *that* camera.
6. Backdrop open? Read the knee, not the 95% point.
7. Anything in front of where the sweep started? Titles and signatures are
   often pinned to the lens and cannot fuse at any focal plane.
8. Interior? Measure the corridor and derive the cone.
9. Print the depth budget. Then render.
10. Not going to a panel? Same geometry, `render_pov_views()` and a single-row
    spec — and print the budget anyway, because a sweep has less margin.
