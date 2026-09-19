# Release Notes -- v0.15.0

> Released: 2026-09-19

Off-axis versus toe-in was the first of four questions put to Liti
Holographics in August, and this release answers it the way such questions
usually get answered: not by a reply, but by watching what the machine is
actually fed. LitiHolo's own capture tool is a web renderer that orbits a
Sketchfab camera around a pinned aim point and screenshots 23 stops. There
is no frustum shear anywhere in it. It is toe-in, the projection every
docstring in this library tells you not to use.

That matters because a hogel slicer is not a lens sheet. Quiltwright's
insistence on off-axis projection is a statement about Looking Glass
lenticular optics, where a toe-in sweep produces keystone distortion the
display cannot fuse. A holographic printer resamples the view set into
hogels by its own rules, and if it has only ever been given toe-in captures,
handing it an off-axis set is an unlabelled change of input rather than a
correction. So toe-in is now available, deliberately, with the geometry that
produced a sweep named in the emitted wrapper comment. Off-axis remains the
default, and `render_pov_quilt()` does not take the option at all.

## What changed

**`geometry="toe-in"` on `render_pov_views()`, and `toe_in_cameras()`
behind it.** The eye travels a circular arc of constant radius about
`look_at`, and every view is re-aimed at that point, so each frame is a
plain symmetric frustum. This is the shape the vendor tool emits, and the
2003 submission of one of these same scenes was toe-in too, and printed.
What remains unknown is whether the slicer requires toe-in or merely
tolerates it, and whether it resamples a denser source set. The option
exists so that question can be tested rather than assumed.

**`LITIHOLO_TOOL_SWEEP`, kept separate from `LITIHOLO_SWEEP`.** One is the
specification sheet, the other is the tool at its factory defaults, and they
disagree. The tool steps 2.5 degrees per move and captures 23 stops from
-27.5 to +27.5, which is a 55-degree cone, not 45. Its default capture is
400x400 square rather than the 1600x2000 this project had guessed. Neither
number is a specification -- both are editable fields in the tool's UI --
but they are what the hardware has actually received, and that is worth
recording under its own name instead of quietly amending the other.

**`pack_litiholo_sweep()` and `litiholo_names()`, the delivery step.** A
rendered sweep re-encoded as JPEG under the vendor tool's own names,
`render-400x400-HPO-01.jpg` through `-23.jpg`, one-indexed with view 0
leftmost, optionally zipped as the tool's `-HPO-captures.zip`. It is
renderer-agnostic and changes no geometry -- the same role `assemble_quilt()`
plays for a panel. Transparent frames are composited onto black rather than
having their alpha discarded, since black is the ground the tool's own
transparent capture ends up on, and it is the one background a hologram
must not get wrong. Full-parallax mode is documented as a gap:
`litiholo_names(mode="FP")` raises rather than name a 23x17 grid that
quiltwright cannot yet fill.

**`view_angles()`, the angle list both geometries sample.** `view_offsets()`
is now derived from it, so an off-axis sweep and a toe-in sweep of the same
spec provably sample the same angles, and a depth budget's quoted sampling
interval means the same thing either way.

**[docs/lfd.md](docs/lfd.md) records what the tool settles and what it does
not.** The answered question and the three still open are now written down
next to the evidence for each, so the next person to look does not have to
re-derive which is which.
