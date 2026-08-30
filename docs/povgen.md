# Transcoding PyVista scenes to POV-Ray

`quiltwright.povgen` writes `.pov` scenes from analytic primitives, so a scene
composed in Python -- or grown by a geometry engine such as `kg_utils.viz3d` --
can be **ray-traced** by [`render_pov_quilt`](povray.md) instead of rasterised
by VTK.

It is the bridge between quiltwright's two existing backends, which until now
never met: [`lfd`](lfd.md) sweeps a live `pv.Plotter`, [`povray`](povray.md)
sweeps a `.pov` file on disk. `povgen` produces the second from the first.

---

## Concept

### Why analytic, and not a mesh dump

By the time geometry reaches a `pv.Plotter` it is already tessellated:
`pv.Sphere` is a triangulated ball, a swept tube is a strip of quads. There are
two ways to get that into POV-Ray.

**Dump the triangles** into a `mesh2`. Faithful and universal, but it keeps
VTK's facets and costs a great deal of text, re-parsed once per view -- 48
times for a Portrait quilt.

**Re-emit the intent.** A limb is a swept path of radii; a leaf is a ball at a
point. POV-Ray has exact primitives for both:

```pov
sphere_sweep { linear_spline, 24, <x,y,z>, r, ... }   // one limb
#declare Leaf = sphere { 0, 0.4 }
object { Leaf translate <x,y,z> }                      // one leaf
```

Measured on a 3000-leaf organic tree from `kg_utils.viz3d` -- 99 limbs,
192k triangles and 159k vertices once tessellated:

| Form | Size |
|---|---|
| `mesh2` equivalent | ~12.5 MB |
| analytic, oriented leaf instances | 839 KB |
| analytic, unoriented instances | 534 KB |
| analytic, plain spheres | 508 KB |

So **15× to 25× smaller**, depending on how much per-leaf orientation you
keep -- the `matrix` on an oriented instance is most of the per-leaf cost. Plus
an exact silhouette at any zoom and a bounding hierarchy the ray-tracer is
good at. That quality difference is the reason to leave VTK, so `povgen`
reaches for the analytic form first.

The rule of thumb: if the producer knows *why* the geometry has its shape,
re-emit the description. `mesh2` is the fallback for geometry that has no
analytic description -- volumes, isosurfaces, imported meshes -- and is not yet
implemented.

### Where the pieces live

`povgen` knows about primitives and SDL. It does **not** know about trees,
graphs, or molecules -- the producer supplies geometry, `povgen` writes the
file. Concretely, for the organic-tree stack:

| Layer | Supplies |
|---|---|
| `kg_utils.viz3d.limb_paths` | `[(points, radii), ...]` per limb -- pure NumPy |
| `kg_utils.viz3d.leaf_frames` | `(positions, directions)` per leaf -- pure NumPy |
| `quiltwright.povgen` | turns either into SDL |

Neither package imports the other. `limb_paths` and `leaf_frames` are the
NumPy halves of `smooth_paths` and `leaf_glyphs`, split out so a POV-Ray
export needs no VTK at all.

---

## 1. A minimal scene

```python
from quiltwright.quilt import QUILT_PRESETS, save_quilt
from quiltwright.povgen import PovScene, Sphere, Texture, lights_from_bounds, to_pov
from quiltwright.povray import render_pov_quilt, PovCamera

scene = PovScene(background="#101018")
scene.add(Sphere((0, 0, 0), 1.0, Texture("#dd4433")))
for light in lights_from_bounds(*scene.bounds()):
    scene.add_light(light)
path = scene.write("ball.pov")

spec = QUILT_PRESETS["portrait"]
camera = PovCamera(location=to_pov((0, 0, 8)), look_at=to_pov((0, 0, 0)), fov=40)
save_quilt(render_pov_quilt(path, spec, camera), "ball", spec)
```

Scene coordinates are written **right-handed** -- the same convention as
PyVista, VTK and NumPy -- and converted on emission. See section 3.

Note the `to_pov` around the camera. **A `PovCamera` is not converted for
you**: only `pov_camera_from_plotter` does that, and `camera_block` emits
whatever it is handed. A hand-built camera has to be converted by the caller,
or it will aim into the mirrored half of the world. This example would survive
the mistake -- the ball is at the origin, so its *z* is zero and a flip is
invisible -- which is exactly why it is worth spelling out here rather than
leaving to be discovered on a scene where it matters.

## 2. Carrying a plotter's viewpoint over

`pov_camera_from_plotter` transfers a composed plotter's camera. VTK's
`view_angle` and `PovCamera.fov` are both *vertical* degrees, so the lens maps
one-to-one:

```python
from quiltwright.lfd import render_quilt  # PyVista backend
from quiltwright.povgen import pov_camera_from_plotter

camera = pov_camera_from_plotter(plotter, fov=None)   # keep the scene's own FOV
```

Pass the same `fov` to both backends and they frame identically -- both run the
same dolly arithmetic before sweeping. `fov=None` on both sides is what you
want when comparing them.

> **The scene contains no camera, deliberately.** `render_pov_quilt` appends
> one off-axis camera per view and POV-Ray uses the *last* camera it parses, so
> a camera written here would be silently overridden with a warning.

## 3. Handedness

PyVista, VTK and NumPy are right-handed. **POV-Ray is left-handed.** `povgen`
authors everything right-handed and negates *z* on emission -- the same
correction `pypdb2pov` applies to PDB coordinates. `pov_camera_from_plotter`
applies the same conversion to the camera, so the two agree and the image
*matches* the PyVista render rather than mirroring it.

**`PovCamera` itself holds POV-Ray coordinates, already converted.** It
predates `povgen` and knows nothing about handedness; `camera_block` emits it
verbatim. Build one by hand and the conversion is yours to apply:

```python
camera = PovCamera(
    location=to_pov((0.0, -8.0, 3.0)),   # right-handed, +z up
    look_at=to_pov((0.0, 0.0, 3.0)),
    sky=to_pov((0.0, 0.0, 1.0)),         # -> (0, 0, -1)
)
```

Forget it and the geometry sits at negative *z* while the lens aims at
positive *z*. POV-Ray renders a clean picture of empty space, the scene file
looks perfect, and any assertion comparing the camera against the
right-handed bounds it came from passes.

Pass `handedness="none"` to author directly in POV-Ray coordinates. If you do,
use it consistently for the scene *and* the camera bridge.

Two consequences worth knowing:

- **Box corners are re-sorted** after the flip, because negating *z* swaps
  which corner is the lower one and POV-Ray requires `corner1 <= corner2`.
  Handled for you.
- **Rotations are conjugated** by the reflection, so an `Instance` matrix means
  the same thing in the mirrored world.
- **Triangle winding reverses.** Irrelevant to the analytic primitives here,
  none of which have a winding -- but a future `mesh2` emitter must reverse each
  face's index order or its normals will point inward and the surface will
  render black.

## 4. Materials

`Texture(color, opacity, finish)` covers the common case.

**Opacity becomes POV-Ray `transmit`, not `filter`.** This matters: `transmit`
passes light through unchanged, which is the correct analogue of VTK's alpha.
`filter` tints everything seen through the surface by the surface's own colour,
and using it will quietly recolour your whole scene.

Lighting is *not* transcoded. VTK's default is a headlight at the camera, which
POV-Ray does not reproduce and which looks flat when ray-traced anyway.
`lights_from_bounds` gives a serviceable two-light rig sized to the scene so a
transcoded scene renders legibly, and then you should light it properly --
area lights are most of what makes ray-tracing visibly better than VTK.

**Tell it which way is up.** The rig places its key light "above and to the
right," and `up` defaults to `+y` -- right for a VTK scene, wrong for a `+z`-up
one such as anything from `kg_utils.viz3d`. Left at the default there, the key
light lands at `centre_z − 1.4·radius`: below the ground, lighting the subject
from underneath.

```python
lights_from_bounds(*scene.bounds(), up=(0, 0, 1))
```

Only the up axis is inferred. Which side counts as "front" follows from `up`
and cannot know where your camera is, so a scene needing the key on a
particular side should place its own lights.

**`scene.bounds()` cannot see instances**, and instancing is the reason to use
this module -- so check the two don't collide before feeding bounds to a light
rig or a camera. A tree gets away with it: its wood is swept and reaches the
crown, so the bounds cover the subject even though every leaf is an instance.
A scene whose subject *is* the instances does not -- ten thousand instanced
boulders around one measurable marker post return the bounds of the post, and
an entirely instanced scene returns `None`. Either keep one measurable
primitive spanning the subject (an untextured `Box` is invisible to a render
but visible to `bounds()`), or track the extent as you place the instances and
skip `bounds()` entirely.

## 5. Swept paths

`SphereSweep` is the analytic replacement for `spline.tube(...)`. It defaults
to `linear_spline` rather than `b_spline` because **`linear_spline`
interpolates its control points** while `b_spline` only approximates them.
Callers generally hand over a path that has already been smoothed, so a second
approximating spline would pull the surface off the geometry PyVista tubed.

```python
from kg_utils.viz3d import limb_paths
from quiltwright.povgen import sphere_sweeps_from_paths, Texture

scene.add(sphere_sweeps_from_paths(limb_paths(skeleton), Texture("#6b4a2f")))
```

Two details `sphere_sweeps_from_paths` handles: consecutive duplicate points
(which make POV-Ray's sweep solver degenerate) are dropped, and zero radii are
raised to `min_radius`, because a zero-radius sweep end produces artifacts
rather than a sharp tip. The `tolerance` default of 0.05 is deliberate too --
POV-Ray's own default of 1e-6 makes the solver miss thin sweeps at scene scale
and drop segments.

## 6. Instancing a crown

A leaf is the same prototype a few thousand times, so declare it once:

```python
from kg_utils.viz3d import LEAF_ASPECT, leaf_frames
from quiltwright.povgen import Sphere, Texture, instances_from_frames

points, directions = leaf_frames(attractors, skeleton, size=0.35)
scene.declare("Leaf", Sphere((0, 0, 0), 0.35))
scene.add(instances_from_frames("Leaf", points, directions, Texture("#3f7d3f")))
```

Orientation follows VTK's glyph convention -- the prototype's **+x** axis is
aligned to each direction vector. The remaining two axes are completed
deterministically, so a given input always produces the same file, but that
completion is not VTK's: glyph **roll** will differ from a PyVista render even
though position, aim and silhouette agree. Flatten the prototype with
`LEAF_ASPECT` to match `leaf_glyphs`' blade shape.

---

## 7. Verification

`tests/test_povgen_parity.py` renders the same scene through *both* backends
at a matched camera and compares silhouettes. Surfaces are flat emissive, so
the comparison isolates geometry from the two renderers' different lighting
models.

Measured agreement on the reference scene: **IoU ≈ 0.95**, with identical
silhouette bounding boxes. The residual is antialiasing at the rim -- the
extents land on the same rows and columns, which is what pins the lens.

The scene is **deliberately asymmetric in depth**, and that is the whole point.
A scene straddling the focal plane renders almost identically whether or not
*z* was flipped, so it cannot detect the most damaging bug this module could
have. The fixture places one sphere well in front of the focal plane and
another well behind it at the same radius; perspective alone decides which
looks bigger, so mirroring depth swaps them and IoU collapses from ~0.96 to
~0. That was confirmed by mutation testing, not assumed:

| Mutation | Caught by |
|---|---|
| `to_pov` stops negating *z* | 5 parity tests + 4 unit tests |
| camera `sky` not converted | `test_tilted_camera_up_vector_is_converted` |
| `SphereSweep` defaults to `b_spline` | 4 unit tests |

The sky mutation is why one test tilts the camera: every other test leaves
`up` at `(0, 1, 0)`, whose *z* is zero, so the conversion applied to it is
invisible and a bridge that forgot to convert `sky` passes them all.

Two further properties are asserted because they are invisible in any single
view and only show up on the physical panel:

- **Parallax runs the same way in both backends.** A mirrored sweep inverts
  the hologram's depth.
- **Near and far geometry move in opposite directions.** That opposition is
  what a light-field display turns into depth.

Run them with a `povray` binary and a GL stack present; they skip otherwise.

```
pytest tests/test_povgen_parity.py
```

---

## 8. Gotchas

- **Do not emit a camera.** POV-Ray uses the last one parsed; yours will be
  overridden by the per-view camera with a warning.
- **`transmit`, never `filter`,** for VTK-style opacity (section 4).
- **`linear_spline`, not `b_spline`,** for already-smoothed paths (section 5).
- **Smooth once, render twice.** `limb_paths` uses a NumPy Catmull-Rom that
  interpolates the same control points as `pv.Spline` but is not bit-identical
  to VTK's. When two backends must agree to the pixel, call `smooth_paths` once
  and give both the same points rather than letting each smooth its own.
- **`sphere_sweep` ends are hemispherical; `tube` ends are flat.** A tapered
  limb therefore extends further past its thick end in POV-Ray than in
  PyVista -- about a pixel of centroid bias on a 200px tile. Harmless in a
  render, worth knowing when comparing them.
- **Cost scales with view count.** A Portrait quilt is 48 full ray-traces. For
  radiosity or photons, render one view with the cache saved and the rest with
  it loaded via `extra_args` -- the lighting is identical across a sweep, so
  recomputing it per view is pure waste.
