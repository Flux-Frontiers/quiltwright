# Release Notes -- v0.16.0

> Released: 2026-09-26

The Knowledge Press trees wear bark now in the web forest and in the PyVista
quilt path, each limb wrapped in a photograph of its species' bark. The
POV-Ray path could not follow. It draws limbs as `sphere_sweep`s, which are
exact and small but carry no texture coordinates, so a POV-Ray tree could only
ever be one flat colour. This release gives povgen what it was missing: a
mesh that carries UVs, a texture that is a picture, and a way to make the
picture travel with the scene.

Getting the bark to show also turned up something older. povgen scenes declare
no `#version`, so POV-Ray 3.7 has been parsing every one of them in its
pre-3.7 compatibility mode, which lights a scene flatter. Flat colours hide
that. A bark photograph does not: it came out washed out until the scene
declared `#version 3.7`.

## What changed

**`ImageTexture` lays a picture on a mesh by UV.** It takes the image, an
optional tint and an optional bump. The tint is a second, fully filtering
texture layer, so it multiplies the picture the way three.js tints a colour map
by a vertex colour. The bump takes relief from the picture's own brightness,
because POV-Ray 3.7 reads no tangent-space normal maps. `uv_mapping` sits
inside the pigment and the normal rather than on the texture, since POV-Ray
refuses to layer a tint over a texture that carries it there.

**`Mesh2` carries texture coordinates, and `swept_scene` takes a mesh.** A
`Mesh2(uv=...)` emits `uv_vectors`, one per vertex, and `swept_scene` accepts
a `Mesh2` in place of the swept paths along with a `sweep_texture`. That is
the shape `kg_utils.viz3d.bark_sweep` produces, so a tree's bark goes straight
in. A render test lays an image with a green top, a red left and a blue right
on a quad authored right-handed, and checks all three land where they should:
after the cartoon chirality bug in 0.15.1, a mirrored picture was the failure
worth ruling out. On one book's tree the mesh also traced a 900x1200 view in
0.9 s against 72 s as sweeps, and it has no seams where limbs fork.

**Images travel with the scene.** The SDL names each image by file name alone,
and `PovScene.write` copies it next to the `.pov`, where `render_pov_quilt`
already looks. A written scene renders wherever its folder goes. Two different
images with the same file name are refused rather than left to overwrite each
other.

**`PovScene(version=...)` declares a `#version`.** Declaring `"3.7"` takes a
scene out of POV-Ray's pre-3.7 mode and gives a photograph back its contrast.
It is off by default: every scene tuned so far was tuned without it, and
declaring it changes how they are lit.

**Smaller fixes.** `PovScene.bounds()` now measures a `Mesh2`, so a scene
whose subject is a mesh sizes its lights and ground slab from that subject.
`coalesce_mesh2` leaves a mesh with UVs whole instead of dropping its
coordinates, and `Mesh2` accepts NumPy arrays for its geometry.
