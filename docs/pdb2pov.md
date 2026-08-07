# Molecules from PDB files, via pdb2pov

**Upstream**: <https://github.com/suchanek/pdb2pov> (v2.2; the original RCS
logs are dated 1993–94)
**Feeds**: [`quiltwright.povray`](povray.md)

`pdb2pov` converts Brookhaven PDB atomic structure files into POV-Ray scenes.
It predates this pipeline by thirty years and still feeds it directly — as of
v2.0 the scenes it writes need no adaptation at all.

It is also, conveniently, *better* prepared for holographic output than most
hand-built scenes. See [Why molecules are the easy case](#why-molecules-are-the-easy-case).

> **Updated for pdb2pov 2.2.** This page previously documented a set of build
> workarounds and a `#version 3.1;` prepending step. Both are gone: v2.0 is
> prototyped C17 and emits POV-Ray 3.7. If you are on v1.19, see
> [Working with v1.19](#working-with-v119) at the foot of this page.

---

## 1. Building it

```bash
git clone https://github.com/suchanek/pdb2pov
cd pdb2pov && make
```

That is the whole procedure. There are no portability flags to arrange, no
force-included prototype header, and no need to disable `_FORTIFY_SOURCE`.
The build is clean under `-Wall -Wextra -Wpedantic`.

`make check` converts the bundled `1CRN.pdb` several ways, asserts that the
parser changes leave crambin's output unchanged, and renders one atom of every
element to prove the element table and the include files agree.

---

## 2. Preparing the PDB

Trimming a modern PDB to its coordinate records used to be mandatory —
earlier versions read past the end of short records and could crash. That is
fixed; `1CRN.pdb` now converts to a byte-identical scene whether trimmed or
not.

Trimming is still how you *choose* what appears:

```bash
grep -E "^(ATOM|END)" 1CRN.pdb > crambin.pdb          # protein only
grep -E "^(ATOM|HETATM|END)" 1CRN.pdb > crambin.pdb   # keep heteroatoms
```

### Heteroatoms and alternate conformations

Two long-standing parser defects were fixed in **pdb2pov 2.1**. If you are on
2.0 or earlier they still apply, and the workarounds are given below.

**Elements now come from the PDB element column** (77–78) rather than being
guessed from the first characters of the atom name. The guess was wrong for
any two-letter element sharing a first letter with a one-letter one, and
anything it could not place was dropped without a message — so an ion could
vanish from a scene while the header atom count still looked plausible:

| Record | Element | Through 2.0 | 2.1 and later |
|--------|---------|-------------|---------------|
| `NA` | sodium | **nitrogen** | sodium, own colour |
| `CL` | chlorine | **carbon** | chlorine, own colour |
| `F` | fluorine | **iron** | fluorine, own colour |
| `ZN` | zinc | **silently dropped** | zinc, own colour |
| `MG` | magnesium | **silently dropped** | magnesium, own colour |

**The palette covers 33 elements as of 2.2**, up from eight:

| Group | Elements |
|-------|----------|
| Organic and biological | H, C, N, O, S, P, Se |
| Halogens | F, Cl, Br, I |
| Alkali and alkaline earth | Li, Na, K, Mg, Ca |
| Transition and heavy metals | Mn, Fe, Co, Ni, Cu, Zn, Mo, W, Ag, Cd, Pt, Au, Hg |
| Other | B, Si, As, Xe |

That covers the biological metals, halogen ligands and phasing heavy atoms,
so a zinc finger, a selenomethionine structure and a mercury derivative all
come out correctly coloured and sized rather than as identical grey spheres.
Anything still unrecognised renders as `Atom_X`, a neutral grey sphere, and
the conversion reports how many atoms landed there and which elements they
were. Nothing disappears silently.

The original eight keep their 1994 colours, which are **not** the CPK
convention — carbon is green, phosphorus yellow, iron dark purple, calcium
white. Elements added in 2.2 use Jmol/CPK colours, so a scene mixing old and
new elements mixes two conventions. That is deliberate: changing the original
eight would alter every existing render.

**Alternate conformations are now filtered** to the blank and `A` altLoc
indicators. Keeping all of them — the behaviour through 2.0 — puts both
conformers in the scene: overlapping spheres at nearly identical positions,
plus spurious bonds between the A and B copies. A 7-record test file with
three side-chain atoms in two conformations gave 7 atoms and 13 bonds where
the correct answer is 4 and 3. `--keep-altlocs` restores the old behaviour.

**On 2.0 or earlier**, strip alternate conformations yourself:

```bash
awk '/^(ATOM|HETATM)/ && (substr($0,17,1)==" " || substr($0,17,1)=="A")' in.pdb > out.pdb
```

and check any metals or ions by hand, since they will be mistyped or missing.

**Chain selection.** 2.1 also adds `--chain`, so a single subunit can be
converted without pre-filtering the file:

```bash
./pdb2pov 4hhb hemoglobin_a -b -d 1.9 -o --chain A
```

If a structure still misbehaves, stripping column 22 restores the pre-1996
layout the parser was written against:

```bash
awk '/^ATOM/ {print substr($0,1,21) " " substr($0,23)}' in.pdb > out.pdb
```

---

## 3. Converting

Arguments are `InputFile OutputFile` **without extensions** — `.pdb` and
`.pov` (or `.inc`) are appended automatically.

```bash
./pdb2pov crambin crambin_bs -b -d 1.9 -p
```

| Flag | Effect |
|------|--------|
| `-v` | van der Waals radii (default) |
| `-c` | covalent radii |
| `-b` | ball and stick |
| `-q` | ball and stick with **glass atoms** |
| `-d x.x` | bond cutoff in ångströms (default 2.2) |
| `-r x.x` | scale factor applied to all atomic radii |
| `-o` | object only — no camera or lights, for dropping into another scene |
| `-p` | plain white sky, no ground |
| `-s` / `-g` / `-h` | cloudy sky / plain ground / checkered ground |
| `-a` | area light |
| `-x -y -z` | absolute axis rotations in degrees |
| `--chain IDS` | restrict to the given chain IDs, e.g. `--chain AB` (2.1) |
| `--keep-altlocs` | keep every alternate conformation (2.1) |
| `--legacy-elements` | guess elements from atom names, pre-2.1 style (2.1) |

`-o` is the one to reach for when composing, and it is the right choice for
quilts specifically — see below.

---

## 4. Rendering as a hologram

```python
from dataclasses import replace
from quiltwright.lfd import QUILT_PRESETS, focal_distance_for_range, save_quilt
from quiltwright.povray import PovCamera, render_pov_quilt

# Both numbers come from pdb2pov's own header comment.
CAM_DIST, ENCLOSING_R = 40.075, 18.759
near, far = CAM_DIST - ENCLOSING_R, CAM_DIST + ENCLOSING_R
focal = focal_distance_for_range(near, far)

camera = PovCamera(
    location=(0, 0, -CAM_DIST),
    look_at=(0, 0, -CAM_DIST + focal),
    fov=53.13,                      # matches pdb2pov's own lens
)
spec = replace(QUILT_PRESETS["16-landscape"], view_cone=35.0)
quilt = render_pov_quilt("crambin.pov", spec, camera, include_paths=["path/to/pdb2pov"])
save_quilt(quilt, "renders/quilts/crambin", spec)
```

Crambin at 7680×4320 takes about a minute, landing 4.5 px of adjacent-view
movement, symmetric front to back.

### Prefer `-o` for quilts

`render_pov_quilt` appends its own camera per view, and POV-Ray uses the last
camera it parses while warning about earlier ones. Converting with `-o`
produces a `.inc` with no camera and no lights, so there is nothing to
override and nothing to warn about. You supply the camera and lighting from
the host scene, which is what you want anyway when the framing is being driven
by the display's view cone rather than by the molecule.

The `fov=53.13` above reproduces pdb2pov's framing — its camera uses
`direction 1, up 1`, giving a vertical field of view of 2·atan(0.5). With
`-o` there is no camera to match, so the value is yours to choose.

### The enclosing radius is now a POV float

v2.0 emits the bounding radius as a declaration, not only as a header
comment, so a host scene can read it without scraping:

```povray
#declare crambin_enclosing_radius = 18.759;
#declare crambin_obj              = union { /* atoms and bonds */ }
#declare crambin                  = object { crambin_obj }
```

The old `bounded_by { sphere { ... } }` wrapper is gone — POV-Ray 3.x bounds
CSG automatically and warns that a manual sphere is redundant. Nothing is
lost: the number that mattered is the one above, and automatic bounding is
tighter than a sphere drawn around the whole molecule.

An `-o` include saves and restores the language version around its own
declarations, so including it will not switch your scene to 3.7 behind your
back.

---

## Why molecules are the easy case

Two properties of `pdb2pov` output remove most of the work described in
[povray.md](povray.md):

**It writes the bounding sphere into the file.** The header comment reports
the atom count, the coordinate extents, and the enclosing sphere radius:

```
//	Atoms:  327
//	Extent:	Xmin: -14.866 Xmax: 17.515,
//		Ymin: -12.803, Ymax: 13.650
//		Zmin: -15.113 Zmax: 16.889
//	Enclosing Sphere: 18.759
```

The depth budget needs exactly two numbers — nearest and farthest content —
and for a centred object those are `camera_distance ∓ radius`. No plane-sweep
probing required, unlike an interior.

**The subject floats in empty space.** The sweep-clearance trap that cost the
museum eleven of its forty-eight views cannot occur: there are no walls for
the camera to reverse through. Any cone the display supports is safe.

The practical consequence is that molecular scenes need no per-scene
investigation. Parse two numbers out of the header — or read the emitted
`*_enclosing_radius` float — compute the focal distance, render. It is worth
wiring that into a helper if more than a few structures are going through.

---

## Working with v1.19

If you are pinned to the old release, the original guidance still applies.

Building needed a set of flags that let the K&R sources compile under a
current toolchain without editing them:

| Flag | Why |
|------|-----|
| `-include ./pdb2pov_protos.h` | `pdb2pov.c` called the allocators in `util.c` without declaring them; under K&R rules their pointers were truncated to 32 bits on a 64-bit host |
| `-include stdlib.h` | the non-Amiga path never included it, so `malloc` truncated the same way |
| `-D_FORTIFY_SOURCE=0 -fno-stack-protector` | modern libc traps a `sprintf` overrun in the date stamp |
| `-std=gnu89` | K&R function definitions without prototypes |
| `-Wno-implicit-function-declaration` | several in-file helpers used before declaration |

On GNU/Linux it also needed `-lm`, which the old Makefile omitted; macOS
supplies libm via libSystem, so the gap was invisible there.

v1.19 wrote POV-Ray 2.x, where `#declare` statements carry no trailing
semicolon. POV-Ray 3.5+ rejects that outright unless the language version is
pinned:

```bash
printf '#version 3.1;\n' | cat - crambin_bs.pov > crambin.pov
```

POV-Ray still emitted `Possible Parse Error` warnings — seventeen of them for
a ball-and-stick crambin. They were warnings; the render was correct.

**This still applies to other pre-2000 scenes in the archive.** The museum
scenes under `pov-scenes/` are POV-Ray 2.x and continue to need the pragma,
as do the copies of `atoms2.inc` and friends under `pov-scenes/myinclude/`,
which are deliberately left at their 2.x syntax so those scenes keep
rendering. Only pdb2pov's own bundled includes were updated to 3.7.

---

## Lineage

`pdb2pov` (1993) and `proteusPy.DisulfideVisualization` (2024) are the same
program written thirty years apart: read atoms, emit a sphere per atom scaled
by element radius, emit split-coloured cylinders per bond, colour by element.
One targets a ray-tracer and one targets VTK. Both now terminate at the same
place — [`assemble_quilt`](povray.md#5-api) — by different routes.
