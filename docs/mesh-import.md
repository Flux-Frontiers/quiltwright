# Any 3D object file → a hologram

**Command**: `quiltwright mesh`
**Module**: `quiltwright.cycles` (`mesh_bounds`, `frame_camera`, `autoframe_camera`)

> *If you have a mesh file, you have a hologram — the only missing piece is
> where to put the camera, and that can be measured.*

Quiltwright's [Cycles backend](cycles.md) already imports every mesh format
Blender can read — glTF/GLB, OBJ, STL, PLY, USD, FBX, Alembic — and renders the
textures and PBR materials the file carries. What it does *not* get from an
imported mesh is a camera: a `.blend` can carry its own, but an OBJ or a GLB
off a modeling tool, a photogrammetry scan, an asset library, or an AI
generator such as [Meshy](https://www.meshy.ai/) cannot. Its scale, origin and
up-axis after import are all unknown, so a hand-written `CyclesCamera` is
guesswork — and the wrong guess renders an empty frame or a subject jammed
against the edge.

This is the piece that closes that gap. It measures the imported bounds and
frames them, so an arbitrary object file becomes a quilt in one command.

---

## The one command

```bash
quiltwright mesh model.glb
```

That probes the mesh's bounds, places a front-on camera at the distance that
fills the view, path-traces the sweep, and writes a quilt. Common variations:

```bash
# Fast single-view still while you dial in lighting and view
quiltwright mesh scan.fbx --still --lighting sky

# A finished portrait quilt cast straight to the display
quiltwright mesh asset.obj --device 27-portrait --samples 256 --cast

# A three-quarter view instead of dead-on, wider lens
quiltwright mesh statue.ply --view-direction 0.5 -1 0.3 --fov 20
```

| Flag | What it does |
|---|---|
| `--device` | Target display preset (`portrait` default; `27-portrait`, `go`, …) |
| `--lighting` | `studio` (default), `soft`, `sky`, or a path to an `.hdr`/`.exr` — an imported mesh has no lights, and a path tracer renders an unlit scene *black* |
| `--fov` | Vertical field of view; the framing distance follows from it |
| `--view-direction` | Direction from the object center to the eye (default `0 -1 0`, front-on) |
| `--margin` | Framing headroom beyond a tight fit (`1.2` default; `1.0` is exactly tight) |
| `--samples` | Cycles samples per pixel (128 default; 64 previews, 256 for finals) |
| `--compute` | Cycles compute device: `auto` (default, GPU first), `gpu`, `cpu` |
| `--view-transform` | OCIO view transform (`Standard` default; see [cycles.md](cycles.md)) |
| `--still` | One center view as a flat image at the device's aspect, instead of a full quilt — the fast way to check framing |
| `--preview` | Quarter-size quilt, for iterating |
| `--cast` | Send the finished quilt to Looking Glass Bridge |

## How the framing works

The mesh is imported **once** to measure its world-space bounding box, through
the same importer the render uses — so the box is exactly what the render will
see, with the file's transforms and axis conversion already applied. The camera
is then placed so the box's enclosing sphere (half the diagonal, so the whole
object stays framed from any viewing direction) fills the field of view, using
the exact spherical relation

```text
sin(fov / 2) = radius / distance
```

rather than the small-angle tangent, since object-centric FOVs (~14–30°) are
not small angles. The eye sits along `--view-direction` from the bounds center,
aimed back at that center — **which becomes the holographic focal plane**.
Geometry nearer the camera floats out of the display; geometry beyond it
recedes.

## In Python

The script is thin over three public functions, useful on their own when you
want the pieces:

```python
from quiltwright.cycles import mesh_bounds, frame_camera, render_cycles_quilt
from quiltwright.quilt import QUILT_PRESETS, save_quilt

lo, hi = mesh_bounds("dragon.glb")              # world-space (min, max) corners
camera = frame_camera(lo, hi, fov=14.0)         # a CyclesCamera aimed at the center
quilt  = render_cycles_quilt("dragon.glb", QUILT_PRESETS["portrait"], camera,
                             samples=192, lighting="studio")
save_quilt(quilt, "dragon", QUILT_PRESETS["portrait"])
```

`autoframe_camera("dragon.glb", fov=14.0)` composes the first two into one call.
Because the result is an ordinary `CyclesCamera`, the POV-Ray backend's
[depth budget](povray.md) applies unchanged — run `format_depth_budget()` on it
before committing to a 48-view render, exactly as for any hand-placed camera.

`frame_camera` is pure arithmetic (no Blender), so the framing is unit-tested
directly; `mesh_bounds` and the end-to-end path are covered against a real
import in `tests/test_cycles.py`.

## Notes from real assets

- **Prefer GLB** when your tool offers it. It embeds geometry, textures and PBR
  materials in one binary file — nothing to unzip, no external texture folder to
  keep beside the mesh. An FBX or OBJ from the same tool usually references its
  textures as sibling files, and loses them if that folder goes missing.
- **A baked ground plane frames badly.** Some generators (Meshy among them)
  export the object sitting on a small base or disc. It reads as a ragged shelf
  under the subject and enlarges the bounds; delete that ground mesh in the
  source tool before export for a clean float.
- **Lighting is the biggest lever.** `studio` floats the object in near-black
  for a hero-object look; `soft` is an even, neutral clay reading good for
  *seeing* the model; `sky` drops it into daylight with a horizon; an HDRI gives
  glossy and glazed surfaces something real to reflect. See
  [cycles.md](cycles.md) for the rigs in detail.

## What this is not

For a scene *composed in Python* — a PyVista plotter, or geometry built from
analytic primitives — you do not need this: `render_cycles_quilt_from_plotter()`
frames a plotter directly (see [cycles.md](cycles.md)), and the POV-Ray
generators frame their own scenes. This path is specifically for a **finished
object file that arrived from elsewhere** with no camera and no lights.
