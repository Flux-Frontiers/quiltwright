# Release Notes -- v0.14.0

> Released: 2026-09-16

This release grows two fronts at once: ParaView gains its own scene
directory and a real subject to render, and the Looking Glass Go gets a
proper set -- five subjects composed for its 9:16 panel, held together by a
new `quiltwright playlist` command that actually advances instead of
showing only the first entry. A view-cone cap that had only ever lived in
the render scripts now applies everywhere a quilt gets built.

## What changed

**`paraview-scenes/`, ParaView's counterpart to `pov-scenes/`.** Mount Hood
is its first subject, an elevation surface from Mike Bailey's ParaView
teaching set, shipped with the data it reads because a `.pvsm` records an
absolute path to every file its readers open and the upstream one points at
a drive letter from the machine it was authored on. `make quilt-mount-hood`
and `make still-mount-hood` render it; the PyVista subjects that previously
had no make targets at all (`brain`, `damavand`, `mouse-brain`, `st-helens`)
now do too, each at a view cone measured rather than guessed where the
horizon sits at true infinity.

**View-cone capping is now one function everywhere.**
`quiltwright.quilt.resolve_view_cone()` replaces a cap that used to live
only inside the render scripts. `quiltwright paraview` and `quiltwright
mesh` used a wide panel's native cone uncapped -- Mount Hood on the 16"
Landscape hit 10.4 px of adjacent-view disparity, nearly double the
ceiling, with only a "soft" flag in the depth report as warning. The same
bug existed in `render_vitrine.py`, `render_dna_helix_hologram.py` and
`render_cartoon_hologram.py`, which the Go preset's move to its true native
54-degree cone (previously recorded as 35) would have made worse. All five
callers now cap by default, print the narrowing, and take `--view-cone` to
override.

**`quiltwright playlist` and a fixed `cast_quilt()`.** Several quilts as one
playlist that advances on a timer and loops, verified on a Go under Bridge
2.6.3 with mixed tilings in one list. Building the playlist completely
before calling `play_playlist` is what makes it advance -- a quilt inserted
into a playlist already playing never shows. That same bug was hiding
inside `cast_quilt()` itself: every cast after the first reused the same
playlist name, so Bridge handed back the existing playlist instead of
starting a new one, and a re-rendered quilt looked unchanged because it
never reached the glass. Confirmed by A/B on a real panel; both `cast_quilt()`
and `quiltwright cast --playlist` now default to a fresh name.

**A Looking Glass Go set: five subjects, 9:16.** `bdna-go` stands the
space-filling B-DNA from DNA Under Glass upright and out of its jar.
`dna-ribbon-go` is the museum's metallic DNA ribbon alone, framed with
`no_image` softboxes for the reflections a silver surface needs -- an
earlier cut hung it in a crystal column between two bowls, but on the panel
the glass read as a flat capsule and took the depth budget the ribbon
needed. `f1atpase-cartoon-go` is F1-ATPase without the vitrine exhibit case
around it: a real PyMOL cartoon of 1BMF (bovine mitochondrial F1-ATP
synthase, alpha3beta3gamma) rendered with a camera direction measured by
PCA on the assembly's own CA coordinates rather than the script's previous
fixed default -- the first real end-to-end exercise of the POV-Ray cartoon
backend, 154668 vertices and 307824 faces, correctly folded and colored.
`porin-portrait` recomposes the existing porin trimer scene 9:16 with no
geometry duplicated: two new `#ifndef`-guarded declares let the wrapper
scene set the aspect and camera before including the original. Centering it
took two tries -- the barrel's vertex bounding-box centroid overshot,
confirmed live on a Go as "offset to the left a bit," and the fix was to
mask the rendered subject from its backdrop and measure the actual pixel
centroid instead of trusting the mesh's own reported extents. `playlist-go`
plays all five in rotation.

**`bridge reset` and `bridge status` now match Bridge by executable path,**
not by scanning for `LookingGlassBridge` anywhere in a process's command
line -- a `grep` or a `tail -f` on its log used to read as Bridge, and
`reset` sends that list SIGTERM then SIGKILL.

**Smaller fixes.** The DOI badge, `CITATION.cff` and the README BibTeX cited
v0.10.0's version-specific DOI instead of the concept DOI that resolves to
the newest archive; `CITATION.cff` now carries a comment against repeating
the mistake. The release bundle grows from three subjects to thirteen, plus
both Dynamic Desktop assets and both HLD videos, all attached at release
time rather than carried in the repository. The docs' overview pages now
describe four backends instead of three, catching up to what v0.13.0
actually shipped.

## Upgrading

No breaking changes -- `pip install -U quiltwright` is enough.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
