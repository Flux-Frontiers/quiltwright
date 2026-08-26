"""
Blender Cycles Quilt Renderer
=============================

Drives `Blender <https://www.blender.org/>`_'s Cycles path tracer to produce
*quilts* for Looking Glass holographic displays.  This is the
hardware-ray-tracing sibling of :mod:`quiltwright.povray`: on Apple Silicon,
Cycles' Metal backend runs ray/triangle intersection on the GPU's dedicated
ray-tracing cores (M3 and later; earlier chips run the same Metal path in GPU
software), and the equivalent applies on NVIDIA (OptiX), AMD (HIP) and Intel
(oneAPI) hardware elsewhere.  POV-Ray can never use any of that -- it is a
CPU tracer with its own primitive intersectors -- so scenes that exist as
*meshes* rather than POV-Ray SDL come here instead.

The structural win over the POV-Ray backend is bigger than the hardware:
POV-Ray re-parses the scene and rebuilds its data structures once per view --
48 times for a Portrait quilt -- while this backend runs **one** Blender
process for the whole sweep.  The scene imports once, Cycles builds its BVH
once (``use_persistent_data``), and only the camera moves between views.

**Off-axis projection.**  The same shear as every other quiltwright backend,
expressed through Blender's *camera shift*.  For an eye offset ``s`` along
the camera's unit right vector, with focal distance ``Z``, vertical field of
view ``fov`` and view aspect ``a``, the eye translates by ``s`` (the aim
point riding along, so the view direction never rotates) and the frustum is
sheared back with

.. code-block:: text

    shift_x = -s / (2 * Z * tan(fov/2) * a)

which is the identical quantity VTK's ``SetWindowCenter`` receives in
:func:`quiltwright.lfd._apply_off_axis_view`, in Blender's units (fractions
of the frame width, under a horizontal sensor fit) instead of VTK's
half-widths.  The original look-at point stays pinned to the centre of every
view; that point is the holographic focal plane.

**Scene sources.**  A ``.blend`` file renders with its own materials, lights
and world; everything Blender can import -- glTF/GLB, OBJ, STL, PLY, USD,
FBX, Alembic -- is loaded into an empty scene.  Imported meshes usually
arrive without lights, which in a path tracer means a black frame, so by
default a neutral world and a sun are added when the scene has no light of
its own.  The ``lighting`` parameter picks the rig: a neutral
world-plus-sun (``"soft"``, the default), a camera-relative three-point
studio rig (``"studio"``), Blender's physical sky (``"sky"``), an
equirectangular ``.hdr``/``.exr`` environment map, or ``None`` to add
nothing.

A ``.blend`` may also supply its *own* camera: pass ``camera=None`` and the
file's active camera becomes the centre view.  The focal plane then comes
from the camera's depth-of-field focus distance (or focus object) -- that is
Blender's native "this distance matters" annotation, and setting it does not
blur anything unless DoF is actually enabled.

**Requirements** -- a ``blender`` binary (macOS: ``brew install --cask
blender``; the standard ``/Applications`` install is found automatically),
plus pillow for quilt assembly.  Blender 4.x or later.

Typical usage::

    from quiltwright.lfd import QUILT_PRESETS, save_quilt
    from quiltwright.cycles import CyclesCamera, render_cycles_quilt

    camera = CyclesCamera(location=(0, -35, 8), look_at=(0, 0, 5), fov=14)
    spec = QUILT_PRESETS["portrait"]
    quilt = render_cycles_quilt("protein.glb", spec, camera, samples=128)
    save_quilt(quilt, "protein", spec)   # -> protein_qs8x6a0.75.png

Part of Quiltwright -- https://github.com/suchanek/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from quiltwright.lfd import QuiltSpec, _camera_frame, assemble_quilt
from quiltwright.povray import COURTESY_CORES_HELD_BACK

#: Environment variable overriding which Blender binary is used.
BLENDER_ENV = "BLENDER_BINARY"

#: Where the standard macOS install puts the CLI, which is never on PATH.
MACOS_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"

#: Scene file suffixes this backend accepts, mapped to the import route the
#: driver takes.  ``.blend`` opens natively; everything else is imported into
#: an empty scene.
SCENE_FORMATS: dict[str, str] = {
    ".blend": "blend",
    ".gltf": "gltf",
    ".glb": "gltf",
    ".obj": "obj",
    ".stl": "stl",
    ".ply": "ply",
    ".usd": "usd",
    ".usda": "usd",
    ".usdc": "usd",
    ".usdz": "usd",
    ".fbx": "fbx",
    ".abc": "abc",
}


def _find_blender(binary: str | None = None) -> str:
    """Locate the Blender executable.

    :param binary: Explicit path or command name; falls back to the
        ``BLENDER_BINARY`` environment variable, then ``blender`` on
        ``PATH``, then the standard macOS application bundle.
    :return: Path to the executable.
    :raises RuntimeError: If no Blender binary can be found.
    """
    candidate = binary or os.environ.get(BLENDER_ENV)
    if candidate:
        found = shutil.which(candidate)
        if found:
            return found
        raise RuntimeError(
            f"Blender binary {candidate!r} not found.\n"
            "Install it (macOS:  brew install --cask blender) or set "
            f"{BLENDER_ENV} to its full path."
        )
    found = shutil.which("blender")
    if found:
        return found
    if os.access(MACOS_BLENDER, os.X_OK):
        return MACOS_BLENDER
    raise RuntimeError(
        "No blender binary on PATH and no /Applications/Blender.app.\n"
        "Install it (macOS:  brew install --cask blender) or set "
        f"{BLENDER_ENV} to its full path."
    )


def _scene_format(scene_path: Path) -> str:
    """Map a scene file to its driver import route.

    :param scene_path: Path to the scene file.
    :return: A key of :data:`SCENE_FORMATS` values (``"blend"``, ``"gltf"``, ...).
    :raises ValueError: If the suffix is not one this backend can load.
    """
    kind = SCENE_FORMATS.get(scene_path.suffix.lower())
    if kind is None:
        supported = ", ".join(sorted(SCENE_FORMATS))
        raise ValueError(
            f"unsupported scene format {scene_path.suffix!r} ({scene_path.name}); "
            f"supported: {supported}"
        )
    return kind


def _triple(v) -> tuple[float, float, float]:
    """Coerce a 3-vector -- list, tuple, NumPy array -- to a float 3-tuple.

    :param v: Any iterable of three reals.
    :return: ``(x, y, z)`` as plain floats.
    :raises ValueError: If *v* does not have exactly three components.
    """
    x, y, z = (float(c) for c in v)
    return (x, y, z)


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CyclesCamera:
    """A Blender camera in look-at form, plus the quilt's focal geometry.

    The *look_at* point defines the holographic focal plane, so aim it at
    whatever should sit on the surface of the glass.  Geometry closer to the
    camera floats out of the display; geometry beyond it recedes.

    **Coordinates are Blender's own: right-handed, Z up.**  This is the same
    convention most mesh interchange formats and :mod:`pyvista` use, so no
    conversion applies -- unlike :class:`~quiltwright.povray.PovCamera`,
    which speaks POV-Ray's left-handed world.

    The ``fov``/``focal_distance`` pairing matches ``PovCamera``, so
    :func:`~quiltwright.povray.depth_budget` and
    :func:`~quiltwright.povray.format_depth_budget` accept either camera:
    run the depth budget before committing Cycles to a 48-view render,
    exactly as you would for POV-Ray.

    :param location: Eye position ``(x, y, z)``.
    :param look_at: Point the camera is aimed at.  Becomes the focal plane.
    :param up: Up-hint used to build the camera basis.  Must not be parallel
        to the view direction.  Defaults to ``+z``, Blender's world up.
    :param fov: *Vertical* field of view in degrees.  Looking Glass
        recommends ~14° for object-centric content; see
        :class:`~quiltwright.povray.PovCamera` for why interiors should keep
        their native FOV instead.
    """

    location: tuple[float, float, float]
    look_at: tuple[float, float, float]
    up: tuple[float, float, float] = (0.0, 0.0, 1.0)
    fov: float = 14.0

    @property
    def focal_distance(self) -> float:
        """Distance from the eye to the focal plane, in scene units."""
        return float(np.linalg.norm(np.asarray(self.look_at, dtype="d") - self.location))

    def basis(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Orthonormal camera basis ``(forward, right, up)``.

        Right-handed -- ``right = forward x up_hint`` -- so a camera looking
        down ``+y`` with ``+z`` up gets ``right = +x``.  The driver rebuilds
        the same basis inside Blender; the end-to-end test pins the two
        against each other via the focal-plane invariant.

        :return: Three unit vectors as ``(3,)`` arrays.
        :raises ValueError: If the camera is degenerate (zero-length view
            direction, or *up* parallel to it).
        """
        loc = np.asarray(self.location, dtype="d")
        forward = np.asarray(self.look_at, dtype="d") - loc
        norm = np.linalg.norm(forward)
        if norm == 0:
            raise ValueError("CyclesCamera.location and look_at are identical")
        forward = forward / norm

        right = np.cross(forward, np.asarray(self.up, dtype="d"))
        norm = np.linalg.norm(right)
        if norm < 1e-12:
            raise ValueError(
                f"CyclesCamera.up {self.up} is parallel to the view direction; "
                "pick a different up-hint"
            )
        right = right / norm
        return forward, right, np.cross(right, forward)

    @classmethod
    def aimed(
        cls,
        location: Sequence[float],
        aim: Sequence[float],
        *,
        fov: float,
        focal_distance: float | None = None,
        lateral_shift: float = 0.0,
        up: tuple[float, float, float] = (0.0, 0.0, 1.0),
    ) -> CyclesCamera:
        """Adopt a scene's own viewpoint, re-aimed and re-centred for a sweep.

        The mesh-world twin of :meth:`.PovCamera.aimed`, with the same
        contract: the focal plane moves to *focal_distance* along the
        original aim ray and the eye slides *lateral_shift* along the
        camera's right vector, without touching the view direction or the
        lens.  Pair with :class:`~quiltwright.povray.Clearance` for enclosed
        scenes.

        :param location: The scene's eye position.
        :param aim: The scene's aim point.  Used for direction only unless
            *focal_distance* is ``None``.
        :param fov: Vertical field of view in degrees.
        :param focal_distance: Distance along the aim ray to place the focal
            plane.  Defaults to the scene's own aim distance.
        :param lateral_shift: Distance to slide the eye along the camera's
            right vector before re-aiming.
        :param up: Up-hint, as on :class:`CyclesCamera`.
        :return: The centre-view camera.
        :raises ValueError: If the camera is degenerate (see :meth:`basis`)
            or *focal_distance* is not positive.
        """
        base = cls(location=_triple(location), look_at=_triple(aim), up=up, fov=fov)
        forward, right, _ = base.basis()
        distance = base.focal_distance if focal_distance is None else float(focal_distance)
        if distance <= 0:
            raise ValueError(f"focal_distance must be positive, got {distance}")
        eye = np.asarray(base.location, dtype="d") + right * float(lateral_shift)
        return cls(
            location=_triple(eye),
            look_at=_triple(eye + forward * distance),
            up=up,
            fov=fov,
        )


def view_shift_x(offset: float, focal_distance: float, fov: float, aspect: float) -> float:
    """Blender camera ``shift_x`` for one quilt view, under a horizontal
    sensor fit.

    The off-axis shear in Blender's units: the eye has translated *offset*
    along the right vector, and this shift slides the frustum window back so
    the original look-at point stays centred.  It is the same quantity VTK's
    ``SetWindowCenter`` receives in the PyVista backend, converted from
    half-widths to Blender's fractions of the frame width (a factor of 2).

    :param offset: Lateral eye offset along the camera's right vector, in
        scene units, from :func:`~quiltwright.lfd.view_offsets`.
    :param focal_distance: Camera-to-focal-plane distance, in scene units.
    :param fov: Vertical field of view in degrees.
    :param aspect: Width / height of the rendered view.
    :return: The ``shift_x`` value for this view.
    """
    return -offset / (2.0 * focal_distance * math.tan(math.radians(fov) / 2.0) * aspect)


# ---------------------------------------------------------------------------
# The driver: runs inside Blender, not under quiltwright's interpreter
# ---------------------------------------------------------------------------

#: Written to the working directory and executed as
#: ``blender --background --factory-startup --python driver.py -- job.json``.
#: It is deliberately dependency-free (bpy + stdlib) and speaks to the
#: parent process only through ``QW_``-prefixed stdout lines, because
#: Blender's own output is chatty and version-dependent.
_DRIVER = r'''
"""Quiltwright Cycles driver.  Generated; do not edit -- the source of truth
is quiltwright/cycles.py.  Runs under Blender's bundled Python."""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector


def fail(msg):
    print("QW_ERROR: " + msg, flush=True)
    sys.exit(1)


def load_scene(job):
    path = job["scene"]
    kind = job["format"]
    if kind == "blend":
        try:
            bpy.ops.wm.open_mainfile(filepath=path)
        except Exception as exc:
            fail("could not open %s: %s" % (path, exc))
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    importers = {
        "gltf": lambda p: bpy.ops.import_scene.gltf(filepath=p),
        "obj": lambda p: bpy.ops.wm.obj_import(filepath=p),
        "stl": lambda p: bpy.ops.wm.stl_import(filepath=p),
        "ply": lambda p: bpy.ops.wm.ply_import(filepath=p),
        "usd": lambda p: bpy.ops.wm.usd_import(filepath=p),
        "fbx": lambda p: bpy.ops.import_scene.fbx(filepath=p),
        "abc": lambda p: bpy.ops.wm.alembic_import(filepath=p),
    }
    importer = importers.get(kind)
    if importer is None:
        fail("unsupported scene format: " + kind)
    try:
        importer(path)
    except Exception as exc:
        fail("import of %s failed: %s" % (path, exc))


def setup_render(scene, job):
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = job["width"]
    scene.render.resolution_y = job["height"]
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0
    scene.render.use_border = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    # The BVH survives between views; rebuilding it per view would be the
    # POV-Ray failure mode this backend exists to avoid.
    scene.render.use_persistent_data = True
    scene.cycles.samples = job["samples"]
    scene.cycles.use_denoising = job["denoise"]


def setup_device(scene, requested):
    """Pick a Cycles compute device.  Metal first: on Apple Silicon that is
    the hardware ray-tracing path.  The others cover the same backend on
    non-Apple GPUs; CPU is the always-works fallback."""
    if requested == "cpu":
        scene.cycles.device = "CPU"
        return "CPU"
    addon = bpy.context.preferences.addons.get("cycles")
    cprefs = getattr(addon, "preferences", None)
    if cprefs is not None:
        for dev_type in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                cprefs.compute_device_type = dev_type
            except Exception:
                continue
            try:
                cprefs.refresh_devices()
            except AttributeError:  # pre-4.0 spelling
                cprefs.get_devices()
            if not any(d.type == dev_type for d in cprefs.devices):
                continue
            for d in cprefs.devices:
                d.use = d.type == dev_type
            scene.cycles.device = "GPU"
            return dev_type
    if requested == "gpu":
        fail(
            "no GPU compute device available (tried METAL/OPTIX/CUDA/HIP/ONEAPI); "
            "pass device='cpu' or check Blender's Cycles preferences"
        )
    scene.cycles.device = "CPU"
    return "CPU"


def build_camera(scene, cam, aspect):
    """Create the quilt camera from an explicit CyclesCamera job entry.

    Rebuilds the same right-handed basis as CyclesCamera.basis(); the
    end-to-end test pins the two against each other.  Horizontal sensor fit
    with the sensor cut to the render aspect makes shift_x a fraction of the
    frame width and angle_y the true vertical FOV at once.
    """
    fov = math.radians(cam["fov"])
    data = bpy.data.cameras.new("quiltwright")
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = 36.0
    data.sensor_height = 36.0 / aspect
    data.angle_y = fov

    eye = Vector(cam["location"])
    forward = Vector(cam["look_at"]) - eye
    focal = forward.length
    if focal == 0.0:
        fail("camera location and look_at are identical")
    forward.normalize()
    right = forward.cross(Vector(cam["up"]))
    if right.length < 1e-12:
        fail("camera up vector is parallel to the view direction")
    right.normalize()
    up = right.cross(forward)

    obj = bpy.data.objects.new("quiltwright", data)
    scene.collection.objects.link(obj)
    scene.camera = obj
    # Blender cameras look down local -Z with +Y up: columns are the world
    # right / up / backward axes, plus the eye.
    obj.matrix_world = Matrix(
        (
            (right.x, up.x, -forward.x, eye.x),
            (right.y, up.y, -forward.y, eye.y),
            (right.z, up.z, -forward.z, eye.z),
            (0.0, 0.0, 0.0, 1.0),
        )
    )
    # Default clip planes (0.1..1000) silently truncate scenes at other
    # scales; tie them to the focal geometry instead.
    data.clip_start = focal * 1e-3
    data.clip_end = focal * 1e3
    tan_half_x = math.tan(fov / 2.0) * aspect
    return obj, focal, tan_half_x, 1.0


def scene_camera(scene, aspect):
    """Adopt the .blend's own active camera as the centre view.

    The focal plane comes from the camera's DoF focus object or focus
    distance -- Blender's native annotation for "this distance matters",
    inert unless DoF rendering is actually enabled.  The camera's own lens
    and sensor are preserved; only shift_x moves during the sweep.

    The frustum arithmetic mirrors BKE_camera_params_compute_viewplane
    exactly, because its two fit-dependent quantities follow *different*
    rules (verified against rendered output, not the docs):

    * the sensor size is ``sensor_height`` only when the fit is *declared*
      VERTICAL -- AUTO uses ``sensor_width`` even when it resolves to a
      vertical fit;
    * the shift unit follows the *resolved* fit: shift_x is a fraction of
      the frame width under a horizontal fit but of the frame height under
      a vertical one, hence the aspect factor on shift_scale.
    """
    obj = scene.camera
    if obj is None:
        fail("the .blend has no active camera; pass an explicit CyclesCamera")
    data = obj.data
    if data.type != "PERSP":
        fail(
            "the .blend camera is %s; the off-axis quilt sweep needs a "
            "perspective camera" % data.type
        )
    focus_object = data.dof.focus_object
    if focus_object is not None:
        focal = (focus_object.matrix_world.translation - obj.matrix_world.translation).length
    else:
        focal = data.dof.focus_distance
    if not focal or focal <= 0:
        fail(
            "the .blend camera has no depth-of-field focus distance to use as "
            "the focal plane; set one (it does not blur unless DoF is enabled) "
            "or pass an explicit CyclesCamera"
        )
    sensor = data.sensor_height if data.sensor_fit == "VERTICAL" else data.sensor_width
    tan_half_sensor = sensor / (2.0 * data.lens)
    resolved = data.sensor_fit
    if resolved == "AUTO":
        resolved = "HORIZONTAL" if aspect >= 1.0 else "VERTICAL"
    if resolved == "HORIZONTAL":
        tan_half_x = tan_half_sensor
        shift_scale = 1.0
    else:
        tan_half_x = tan_half_sensor * aspect
        shift_scale = aspect
    return obj, float(focal), tan_half_x, shift_scale


def get_world(scene):
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("quiltwright")
        scene.world = world
    world.use_nodes = True
    return world


def grey_world(scene, value, strength):
    background = get_world(scene).node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (value, value, value, 1.0)
        background.inputs["Strength"].default_value = strength


def add_light(scene, name, kind, position, target, energy, size=None):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    if size is not None:
        data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    aim = (Vector(target) - Vector(position)).normalized()
    obj.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
    return obj


def apply_lighting(scene, spec, base, focal):
    """Light an imported scene that has none of its own.

    Every rig is expressed relative to the camera and scaled by the focal
    distance -- area-light wattage grows with distance squared, so apparent
    brightness is invariant under scene scale and the same preset lights an
    angstrom-radius molecule and a room.
    """
    if spec is None:
        return
    if any(o.type == "LIGHT" for o in scene.objects):
        return
    forward = (-base.col[2].to_3d()).normalized()
    right = base.col[0].to_3d().normalized()
    up = base.col[1].to_3d().normalized()
    target = base.translation + forward * focal
    kind = spec["kind"]

    if kind == "soft":
        grey_world(scene, 0.85, 0.5)
        sun = bpy.data.lights.new("quiltwright_sun", "SUN")
        sun.energy = 3.0
        obj = bpy.data.objects.new("quiltwright_sun", sun)
        scene.collection.objects.link(obj)
        aim = (forward + Vector((0.0, 0.0, -1.0))).normalized()
        obj.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
    elif kind == "studio":
        # Three-point rig: key over the camera's left shoulder, a broad low
        # fill from the right, a rim behind the subject.  Near-black world
        # so the rig, not ambience, draws the form.
        grey_world(scene, 0.03, 1.0)
        d = focal
        watts = 30.0 * d * d
        key = target + (-right * 0.9 + up * 0.7 - forward * 0.7) * d
        fill = target + (right * 1.0 + up * 0.1 - forward * 0.8) * d
        rim = target + (forward * 0.9 + up * 0.6 + right * 0.3) * d
        add_light(scene, "quiltwright_key", "AREA", key, target, watts, size=0.45 * d)
        add_light(scene, "quiltwright_fill", "AREA", fill, target, watts * 0.22, size=1.2 * d)
        add_light(scene, "quiltwright_rim", "AREA", rim, target, watts * 0.7, size=0.25 * d)
    elif kind == "sky":
        world = get_world(scene)
        tree = world.node_tree
        background = tree.nodes.get("Background")
        sky = tree.nodes.new("ShaderNodeTexSky")
        try:
            sky.sky_type = "NISHITA"
        except TypeError:
            pass  # newer Blender: the physical sky is the only type
        sky.sun_elevation = math.radians(33.0)
        sky.sun_intensity = 1.2
        # Sun over the camera's left shoulder: sun_rotation is measured
        # about +Z with the sun at -Y when zero.
        azimuth = math.atan2(forward.x, -forward.y)
        sky.sun_rotation = azimuth + math.radians(225.0)
        if background is not None:
            tree.links.new(sky.outputs["Color"], background.inputs["Color"])
            background.inputs["Strength"].default_value = 0.3
    elif kind == "hdri":
        world = get_world(scene)
        tree = world.node_tree
        background = tree.nodes.get("Background")
        env = tree.nodes.new("ShaderNodeTexEnvironment")
        try:
            env.image = bpy.data.images.load(spec["path"])
        except Exception as exc:
            fail("could not load HDRI %s: %s" % (spec["path"], exc))
        if background is not None:
            tree.links.new(env.outputs["Color"], background.inputs["Color"])
            background.inputs["Strength"].default_value = 1.0
    else:
        fail("unknown lighting rig: %s" % kind)


def main():
    argv = sys.argv
    with open(argv[argv.index("--") + 1]) as fh:
        job = json.load(fh)

    load_scene(job)
    scene = bpy.context.scene
    setup_render(scene, job)
    print("QW_DEVICE %s" % setup_device(scene, job["device"]), flush=True)

    aspect = job["width"] / job["height"]
    if job["camera"] is not None:
        cam, focal, tan_half_x, shift_scale = build_camera(scene, job["camera"], aspect)
    else:
        cam, focal, tan_half_x, shift_scale = scene_camera(scene, aspect)

    base = cam.matrix_world.copy()
    right = base.col[0].to_3d().normalized()
    base_shift = cam.data.shift_x

    if job["format"] != "blend":
        apply_lighting(scene, job["lighting"], base, focal)

    n = len(job["angles"])
    for i, angle in enumerate(job["angles"]):
        offset = focal * math.tan(angle)
        view = base.copy()
        view.translation = base.translation + right * offset
        cam.matrix_world = view
        cam.data.shift_x = base_shift - shift_scale * offset / (2.0 * focal * tan_half_x)
        scene.render.filepath = os.path.join(job["out_dir"], "view%03d.png" % i)
        bpy.ops.render.render(write_still=True)
        print("QW_VIEW %d/%d" % (i + 1, n), flush=True)

    print("QW_DONE", flush=True)


main()
'''


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _camera_job(camera: CyclesCamera | None) -> dict | None:
    """Serialise *camera* for the driver, or ``None`` for the scene's own."""
    if camera is None:
        return None
    if camera.focal_distance == 0:
        raise ValueError("CyclesCamera.location and look_at are identical")
    return {
        "location": _triple(camera.location),
        "look_at": _triple(camera.look_at),
        "up": _triple(camera.up),
        "fov": float(camera.fov),
        "focal_distance": camera.focal_distance,
    }


#: Named lighting rigs the driver can build; see :func:`_lighting_job`.
LIGHTING_RIGS = ("soft", "studio", "sky")


def _lighting_job(lighting: str | Path | None) -> dict | None:
    """Serialise the *lighting* argument for the driver.

    :param lighting: A rig name from :data:`LIGHTING_RIGS`, a path to an
        equirectangular ``.hdr``/``.exr`` environment map, or ``None`` to
        never add light.
    :return: The driver's lighting spec, or ``None``.
    :raises ValueError: If *lighting* is neither a known rig nor an HDRI.
    :raises FileNotFoundError: If an HDRI path does not exist.
    """
    if lighting is None:
        return None
    if isinstance(lighting, str) and lighting in LIGHTING_RIGS:
        return {"kind": lighting}
    path = Path(lighting).expanduser()
    if path.suffix.lower() in (".hdr", ".exr"):
        if not path.is_file():
            raise FileNotFoundError(f"HDRI environment map not found: {path}")
        return {"kind": "hdri", "path": str(path.resolve())}
    raise ValueError(
        f"lighting must be one of {LIGHTING_RIGS}, a .hdr/.exr path, or None; got {lighting!r}"
    )


def _view_angles(spec: QuiltSpec) -> list[float]:
    """Per-view sweep angles in radians, view 0 leftmost.

    The angular form of :func:`~quiltwright.lfd.view_offsets`: the driver
    multiplies by ``focal * tan`` itself, because with ``camera=None`` the
    focal distance is only known inside Blender (it comes from the .blend
    camera's DoF focus).  ``view_offsets(spec, Z) == Z * tan(angles)`` by
    construction, which the tests assert.
    """
    half_cone = math.radians(spec.view_cone) / 2.0
    n = spec.n_views
    if n == 1:
        return [0.0]
    return list(np.linspace(-half_cone, half_cone, n))


def _run_blender(
    blender: str,
    workdir: Path,
    job: dict,
    extra_args: Sequence[str],
    threads: int | None,
    progress: bool,
) -> list[Path]:
    """Write the job and driver, run Blender once, and collect the views.

    :param blender: Blender executable.
    :param workdir: Working directory; receives ``driver.py``, ``job.json``
        and the rendered ``view*.png`` frames.
    :param job: Driver job description; ``out_dir`` is set here.
    :param extra_args: Extra Blender command-line arguments, inserted before
        ``--python``.
    :param threads: ``-t`` thread count.  ``None`` applies the same courtesy
        cap as the POV-Ray backend (``cpu_count - 2``); ``0`` lets Blender
        take every core.  Only CPU rendering is affected.
    :param progress: Print a progress line while rendering.
    :return: The rendered PNG paths, in view order.
    :raises RuntimeError: If Blender exits non-zero, reports a driver error,
        or renders fewer views than the job asked for.
    """
    job = {**job, "out_dir": str(workdir)}
    job_file = workdir / "job.json"
    job_file.write_text(json.dumps(job, indent=2))
    driver = workdir / "driver.py"
    driver.write_text(_DRIVER)

    args = list(extra_args)
    if not any(str(a) in ("-t", "--threads") for a in args):
        if threads is None:
            cores = os.cpu_count()
            if cores:
                args += ["-t", str(max(1, cores - COURTESY_CORES_HELD_BACK))]
        elif threads > 0:
            args += ["-t", str(threads)]

    cmd = [
        blender,
        "--background",
        "--factory-startup",
        *args,
        "--python",
        str(driver),
        "--",
        str(job_file),
    ]

    n = len(job["angles"])
    tail: deque[str] = deque(maxlen=400)
    error: str | None = None
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=workdir
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip("\n")
        tail.append(line)
        if line.startswith("QW_ERROR: "):
            error = line[len("QW_ERROR: ") :]
        elif progress and line.startswith("QW_VIEW "):
            print(f"\r  cycles view {line[len('QW_VIEW ') :]}", end="", flush=True)
        elif progress and line.startswith("QW_DEVICE "):
            print(f"  cycles on {line[len('QW_DEVICE ') :]}", flush=True)
    returncode = proc.wait()
    if progress:
        print()

    if error is not None:
        raise RuntimeError(f"Cycles render failed: {error}")
    if returncode != 0:
        transcript = "\n".join(tail)
        raise RuntimeError(f"Blender failed ({returncode}):\n{transcript[-3000:]}")

    views = [workdir / f"view{i:03d}.png" for i in range(n)]
    missing = [v.name for v in views if not v.is_file()]
    if missing:
        raise RuntimeError(
            f"Blender reported success but {len(missing)} view(s) are missing "
            f"({missing[0]} ...); transcript tail:\n" + "\n".join(list(tail)[-40:])
        )
    return views


def _prepare(
    scene: str | Path,
    spec: QuiltSpec,
    camera: CyclesCamera | None,
    view_cone: float | None,
    binary: str | None,
) -> tuple[str, Path, str, QuiltSpec]:
    """Shared validation for the two render entry points.

    :return: ``(blender, scene_path, format, spec)`` with any view-cone
        override applied.
    :raises FileNotFoundError: If the scene file does not exist.
    :raises ValueError: If the format is unsupported, or ``camera=None`` is
        combined with a scene that cannot carry its own camera.
    """
    blender = _find_blender(binary)
    scene_path = Path(scene).expanduser().resolve()
    if not scene_path.is_file():
        raise FileNotFoundError(f"scene not found: {scene_path}")
    kind = _scene_format(scene_path)
    if camera is None and kind != "blend":
        raise ValueError(
            f"camera=None uses the scene's own active camera, which only a "
            f".blend can carry; a {scene_path.suffix} import needs an explicit "
            "CyclesCamera"
        )
    if view_cone is not None:
        spec = replace(spec, view_cone=view_cone)
    return blender, scene_path, kind, spec


def render_cycles_quilt(
    scene: str | Path,
    spec: QuiltSpec,
    camera: CyclesCamera | None,
    *,
    view_cone: float | None = None,
    samples: int = 64,
    denoise: bool = True,
    device: str = "auto",
    lighting: str | Path | None = "soft",
    threads: int | None = None,
    binary: str | None = None,
    extra_args: Sequence[str] = (),
    keep_views: str | Path | None = None,
    progress: bool = True,
) -> np.ndarray:
    """Render a mesh scene with Cycles into a Looking Glass quilt.

    Sweeps *camera* horizontally across the display's view cone using
    off-axis projections (see the module docstring), path-traces one image
    per view, and tiles them with :func:`~quiltwright.lfd.assemble_quilt`.

    The whole sweep runs in **one** Blender process: the scene imports once
    and Cycles keeps its BVH across views (``use_persistent_data``), so cost
    per view is dominated by actual ray tracing -- on Apple Silicon, Metal
    hardware ray tracing when a GPU device is available.

    :param scene: Path to the scene -- ``.blend``, or any importable mesh
        format in :data:`SCENE_FORMATS`.  Not modified.
    :param spec: Quilt specification (grid, size, aspect, cone).
    :param camera: Base camera; its ``look_at`` becomes the focal plane.
        ``None`` adopts a ``.blend``'s own active camera, taking the focal
        plane from its DoF focus distance (see the module docstring).
    :param view_cone: Override the spec's view cone in degrees.
    :param samples: Cycles samples per pixel.  64 previews cleanly with
        denoising; 128-256 for finals.
    :param denoise: Run Cycles' denoiser on each view.
    :param device: ``"auto"`` prefers a GPU (Metal first) and falls back to
        CPU; ``"gpu"`` errors if no GPU compute device exists; ``"cpu"``
        forces CPU rendering.
    :param lighting: How to light an *imported* scene that has no lights of
        its own -- without this a path tracer renders an unlit import black.
        ``"soft"`` (default) is a neutral world plus a sun; ``"studio"`` a
        camera-relative three-point rig over a dark world; ``"sky"``
        Blender's physical sky; a ``.hdr``/``.exr`` path an HDRI
        environment world.  ``None`` adds nothing.  Rigs scale with the
        focal distance, never touch a ``.blend``, and defer to any light
        the import carries.
    :param threads: Blender ``-t`` thread count.  ``None`` applies the same
        courtesy cap as the POV-Ray backend (``cpu_count - 2``); ``0`` lets
        Blender take every core.  GPU rendering is unaffected.
    :param binary: Blender executable; defaults to ``BLENDER_BINARY``,
        ``blender`` on ``PATH``, or the macOS application bundle.
    :param extra_args: Extra Blender command-line arguments, e.g. a
        ``["--log", "..."]`` debug flag.
    :param keep_views: Directory to retain the per-view PNGs and the job
        description in, for inspection.  Discarded if ``None``.
    :param progress: Print a progress line while rendering.
    :return: ``uint8`` RGB array of shape ``(quilt_height, quilt_width, 3)``.
    """
    from PIL import Image

    blender, scene_path, kind, spec = _prepare(scene, spec, camera, view_cone, binary)

    # Match render_quilt/render_pov_quilt: capture at the declared view
    # aspect so the frustum is undistorted, then let assemble_quilt resample
    # into the tile (anamorphic presets, e.g. the 27" quilts).
    render_h = spec.tile_height
    render_w = round(render_h * spec.aspect)

    job = {
        "scene": str(scene_path),
        "format": kind,
        "width": render_w,
        "height": render_h,
        "angles": _view_angles(spec),
        "camera": _camera_job(camera),
        "samples": int(samples),
        "denoise": bool(denoise),
        "device": device,
        "lighting": _lighting_job(lighting),
    }

    with tempfile.TemporaryDirectory(prefix="cycles_quilt_") as tmp:
        workdir = Path(tmp)
        views = _run_blender(blender, workdir, job, extra_args, threads, progress)
        quilt = assemble_quilt((np.asarray(Image.open(png).convert("RGB")) for png in views), spec)
        if keep_views is not None:
            out = Path(keep_views).expanduser()
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(workdir / "job.json", out / "job.json")
            for png in views:
                shutil.copy2(png, out / png.name)
    return quilt


def render_cycles_views(
    scene: str | Path,
    spec: QuiltSpec,
    camera: CyclesCamera | None,
    out_dir: str | Path,
    *,
    view_cone: float | None = None,
    samples: int = 64,
    denoise: bool = True,
    device: str = "auto",
    lighting: str | Path | None = "soft",
    threads: int | None = None,
    binary: str | None = None,
    extra_args: Sequence[str] = (),
    keep_job: bool = False,
    progress: bool = True,
) -> list[Path]:
    """Render a mesh scene as a sweep of separate view images.

    Identical camera geometry to :func:`render_cycles_quilt` -- the same
    off-axis sheared frustum, the same focal plane -- but the frames are
    written out individually instead of being tiled into a quilt, for
    consumers like hologram printers and lenticular interlacers.  Pair with
    :func:`~quiltwright.lfd.sweep_spec` for view counts no quilt grid can
    express.

    :param scene: Path to the scene, as for :func:`render_cycles_quilt`.
    :param spec: Sweep or quilt specification supplying view count, view
        cone, and per-view pixel size.
    :param camera: Base camera, or ``None`` for a ``.blend``'s own.
    :param out_dir: Directory to write the frames into; created if absent.
    :param view_cone: Override the spec's view cone in degrees.
    :param samples: Cycles samples per pixel.
    :param denoise: Run Cycles' denoiser on each view.
    :param device: ``"auto"``, ``"gpu"`` or ``"cpu"``, as for
        :func:`render_cycles_quilt`.
    :param lighting: Rig for an unlit *imported* scene -- ``"soft"``,
        ``"studio"``, ``"sky"``, an HDRI path, or ``None``; see
        :func:`render_cycles_quilt`.
    :param threads: Blender ``-t`` thread count; see
        :func:`render_cycles_quilt`.
    :param binary: Blender executable override.
    :param extra_args: Extra Blender command-line arguments.
    :param keep_job: Also write the ``job.json`` driver input alongside the
        frames, for inspection.
    :param progress: Print a progress line while rendering.
    :return: Paths to the written frames, in view order -- view 0 leftmost.
    """
    blender, scene_path, kind, spec = _prepare(scene, spec, camera, view_cone, binary)

    render_h = spec.tile_height
    render_w = round(render_h * spec.aspect)

    job = {
        "scene": str(scene_path),
        "format": kind,
        "width": render_w,
        "height": render_h,
        "angles": _view_angles(spec),
        "camera": _camera_job(camera),
        "samples": int(samples),
        "denoise": bool(denoise),
        "device": device,
        "lighting": _lighting_job(lighting),
    }

    with tempfile.TemporaryDirectory(prefix="cycles_sweep_") as tmp:
        workdir = Path(tmp)
        views = _run_blender(blender, workdir, job, extra_args, threads, progress)
        out = Path(out_dir).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        if keep_job:
            shutil.copy2(workdir / "job.json", out / "job.json")
        return [Path(shutil.copy2(png, out / png.name)) for png in views]


# ---------------------------------------------------------------------------
# The PyVista bridge: a composed plotter, hardware-ray-traced
# ---------------------------------------------------------------------------
#
# PyVista scenes are meshes, and meshes are what this backend exists for --
# but a plotter lives in VTK's world and Cycles in Blender's, and the glTF
# hop between them applies a coordinate rotation that is easy to get wrong
# and disastrous when wrong (the scene renders fine; the *sweep* is
# mirrored or tilted).  These helpers own that hop as one contract:
#
# * The scene is exported with ``rotate_scene=False``, so the glTF file
#   carries raw VTK world coordinates.  The alternative bakes a
#   glTF-Y-up rotation whose exact form has varied across pyvista/VTK
#   versions; raw coordinates are the stable choice.
# * Blender's glTF importer then applies its fixed Y-up-to-Z-up
#   convention, landing a VTK point ``(x, y, z)`` at ``(x, -z, y)`` in
#   Blender's world (verified against imported geometry, not inferred).
# * The camera goes through the *same* rotation, so scene and camera agree
#   and the rendered views are identical to what the plotter framed.
#
# Scalar-mapped colours survive the hop: VTK bakes the mapped colours into
# a baseColorTexture, which Blender wires into the Principled BSDF on
# import.  Lights do not exist in the export, which is what the backend's
# ``lighting`` rigs are for.


def _to_blender(v: np.ndarray) -> tuple[float, float, float]:
    """Map a VTK/PyVista world point into Blender's world after glTF import.

    Blender's importer rotates glTF's +Y-up convention onto its own +Z-up;
    with the scene exported un-rotated (``rotate_scene=False``), that is the
    only transform between the two worlds: ``(x, y, z) -> (x, -z, y)``.
    """
    x, y, z = (float(c) for c in v)
    return (x, -z, y)


def export_plotter_gltf(plotter, path: str | Path) -> Path:
    """Export a composed PyVista plotter scene as glTF for this backend.

    A thin wrapper over ``plotter.export_gltf`` that pins the export
    settings the coordinate contract above depends on -- most importantly
    ``rotate_scene=False``.  Export works headless: no OpenGL context or
    prior render is required, so it runs where ``plotter.show()`` cannot.

    :param plotter: A ``pv.Plotter`` with the scene composed.
    :param path: Destination ``.gltf`` path.  Buffers and baked colour
        textures are inlined, so the one file is the whole scene.
    :return: *path*, as a :class:`~pathlib.Path`.
    """
    out = Path(path).expanduser()
    plotter.export_gltf(str(out), inline_data=True, rotate_scene=False, save_normals=True)
    return out


def cycles_camera_from_plotter(plotter, *, fov: float | None = 14.0, zoom: float | None = None):
    """Build the :class:`CyclesCamera` matching a plotter's current view.

    The plotter's camera defines the centre view and its focal point becomes
    the holographic focal plane, exactly as in
    :func:`~quiltwright.lfd.render_quilt` -- including its FOV convention:
    the lens is narrowed to *fov* and the camera dollied back so the focal
    plane stays the same size in frame.  The result is expressed in
    Blender's world under the glTF contract above, so it pairs with
    :func:`export_plotter_gltf` and nothing else.

    The plotter is read, never mutated: unlike ``render_quilt``, whose
    sweep must drive the live VTK camera, this backend renders from a copy
    of the view, so the plotter remains exactly as composed.

    :param plotter: A ``pv.Plotter`` (or anything with a vtkCamera-shaped
        ``.camera``) with the view positioned, e.g. via
        ``plotter.camera_position`` or ``plotter.reset_camera()``.
    :param fov: Vertical field of view in degrees for the quilt cameras;
        the eye dollies back to compensate.  ``None`` keeps the plotter's
        own FOV and distance.
    :param zoom: Optional dolly factor applied after framing; values > 1
        make the subject fill more of each tile, which is what drives
        perceived depth.
    :return: The centre-view :class:`CyclesCamera`.
    """
    pos, focal, _, true_up, distance = _camera_frame(plotter.camera)
    forward = (focal - pos) / distance
    if fov is None:
        fov = float(plotter.camera.view_angle)
    else:
        half_height = distance * math.tan(math.radians(plotter.camera.view_angle) / 2.0)
        distance = half_height / math.tan(math.radians(fov) / 2.0)
    if zoom is not None and zoom != 1.0:
        distance /= zoom
    eye = focal - forward * distance
    return CyclesCamera(
        location=_to_blender(eye),
        look_at=_to_blender(focal),
        up=_to_blender(true_up),
        fov=float(fov),
    )


def render_cycles_quilt_from_plotter(
    plotter,
    spec: QuiltSpec,
    *,
    fov: float | None = 14.0,
    zoom: float | None = None,
    gltf: str | Path | None = None,
    **kwargs,
) -> np.ndarray:
    """Render a PyVista plotter's scene into a quilt with Cycles.

    The hardware-ray-traced sibling of :func:`~quiltwright.lfd.render_quilt`:
    same plotter in, same quilt out, but the views are path-traced by Cycles
    -- with GPU ray tracing where the hardware offers it -- instead of
    rasterised by VTK.  Compose the scene and position the camera exactly as
    you would for ``render_quilt``, then swap the call.

    The scene is exported to glTF once (see :func:`export_plotter_gltf`) and
    the whole sweep renders in one Blender process.  The export carries no
    lights, so the backend's ``lighting`` rigs supply them -- the ``"soft"``
    default for a neutral look, ``lighting="studio"`` for a three-point
    product shot, ``"sky"`` or an HDRI path for environments; pass
    materials-appropriate ``samples`` for finals.

    :param plotter: An *off-screen* ``pv.Plotter`` with the scene composed.
        Read, never mutated -- and never rendered, so this works on
        machines whose GL stack cannot even take a screenshot.
    :param spec: Quilt specification (grid, size, aspect, cone).
    :param fov: Vertical field of view in degrees, with the
        ``render_quilt`` dolly-back convention; ``None`` keeps the
        plotter's own.
    :param zoom: Optional dolly factor applied after framing, as on
        :func:`~quiltwright.lfd.render_quilt`.
    :param gltf: Also write the exported scene here, for inspection or
        reuse.  Exported to a temporary file if ``None``.
    :param kwargs: Forwarded to :func:`render_cycles_quilt` -- ``samples``,
        ``denoise``, ``device``, ``threads``, ``view_cone``, ``binary``,
        ``keep_views``, ``progress`` and the rest.
    :return: ``uint8`` RGB array of shape ``(quilt_height, quilt_width, 3)``.
    """
    if not plotter.camera.is_set:
        # Mirror render_quilt's first-render behaviour, without rendering.
        plotter.camera_position = plotter.renderer.get_default_cam_pos()
        plotter.reset_camera()
    camera = cycles_camera_from_plotter(plotter, fov=fov, zoom=zoom)

    if gltf is not None:
        scene = export_plotter_gltf(plotter, gltf)
        return render_cycles_quilt(scene, spec, camera, **kwargs)
    with tempfile.TemporaryDirectory(prefix="cycles_gltf_") as tmp:
        scene = export_plotter_gltf(plotter, Path(tmp) / "scene.gltf")
        return render_cycles_quilt(scene, spec, camera, **kwargs)
