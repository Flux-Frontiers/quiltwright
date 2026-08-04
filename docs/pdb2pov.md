# Molecules from PDB files, via pdb2pov

**Upstream**: <https://github.com/suchanek/pdb2pov> (v1.19, RCS logs dated 1993–94)
**Feeds**: [`quiltwright.povray`](povray.md)

`pdb2pov` converts Brookhaven PDB atomic structure files into POV-Ray scenes.
It predates this pipeline by thirty years and still feeds it directly — the
scenes it writes need no adaptation beyond a version pragma.

It is also, conveniently, *better* prepared for holographic output than most
hand-built scenes. See [Why molecules are the easy case](#why-molecules-are-the-easy-case).

---

## 1. Building it on a modern machine

The source is K&R-era C with `#ifdef AMIGA` branches. It compiles and runs on
Apple Silicon with **no edits to the original sources** — four compatibility
fixes, all supplied on the command line or via a force-included header.

### The one real bug

`pdb2pov.c` never declares the Numerical-Recipes-style allocators that live in
`util.c` — `dmatrix`, `dvector`, `cmatrix`, `ivector`, `imatrix`. Under K&R
rules an undeclared function is assumed to return `int`, so on a 64-bit target
**every pointer they return is truncated to 32 bits**. This was harmless in
1994 and segfaults immediately now.

Save this as `pdb2pov_protos.h` next to the sources:

```c
/* Prototypes for the allocators in util.c.  pdb2pov.c never declared them,
 * so on a 64-bit target their pointer returns were truncated to int. */
#ifndef PDB2POV_PROTOS_H
#define PDB2POV_PROTOS_H
double **dmatrix(int nrh, int nch);
void     free_dmatrix(double **m, int nrh, int nch);
int    **imatrix(int nrh, int nch);
void     free_imatrix(int **m, int nrh, int nch);
char   **cmatrix(int nrh, int nch);
void     free_cmatrix(char **m, int nrh, int nch);
double  *dvector(int nh);
void     free_dvector(double *v, int nh);
int     *ivector(int nh);
void     free_ivector(int *v, int nh);
#endif
```

### The build line

```bash
cc -std=gnu89 -O0 \
   -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -fno-stack-protector \
   -include stdlib.h -include string.h -include ./pdb2pov_protos.h \
   -Wno-implicit-function-declaration -Wno-deprecated-non-prototype \
   -o pdb2pov pdb2pov.c util.c -lm
```

What each group is for:

| Flag | Why |
|------|-----|
| `-std=gnu89` | K&R function definitions without prototypes |
| `-include ./pdb2pov_protos.h` | the pointer-truncation fix above |
| `-include stdlib.h` | the non-Amiga path never includes it, so `malloc` also truncated |
| `-D_FORTIFY_SOURCE=0 -fno-stack-protector` | modern libc traps on `sprintf` overruns that were benign in 1994 |
| `-Wno-implicit-function-declaration` | several in-file helpers are used before declaration; these all return `int`, so they are genuinely harmless |

> `-O0` is deliberate. The buffer handling is loose enough that optimised
> builds are not worth trusting on unfamiliar input.

Doing this properly upstream would mean adding the prototype header to the
repo and fixing the `sprintf` sizes; the flags above are the zero-edit route.

---

## 2. Preparing the PDB

The parser predates several PDB conventions. Modern files need trimming:

```bash
grep -E "^(ATOM|HETATM|END)" 1CRN.pdb > crambin.pdb
```

`REMARK 290` crystallographic records in particular will crash it. Files that
still carry the chain-ID column parse fine in practice, but if a structure
misbehaves, stripping column 22 restores the pre-1996 layout the parser was
written against:

```bash
awk '/^ATOM/ {print substr($0,1,21) " " substr($0,23)}' in.pdb > out.pdb
```

---

## 3. Converting

Arguments are `InputFile OutputFile` **without extensions** — `.pdb` and
`.pov` are appended automatically.

```bash
./pdb2pov crambin crambin_bs -b -d 1.9 -p
```

| Flag | Effect |
|------|--------|
| `-v` | van der Waals radii |
| `-c` | covalent radii |
| `-b` | ball and stick |
| `-q` | ball and stick with **glass atoms** |
| `-d x.x` | bond cutoff in ångströms |
| `-o` | object only — no camera or lights, for dropping into another scene |
| `-p` | no sky or ground |
| `-s` / `-g` / `-h` | cloudy sky / plain ground / checkered ground |
| `-a` | area light |
| `-x -y -z` | absolute axis rotations in degrees |

`-o` is the one to reach for when composing: it emits the molecule as a bare
POV-Ray object, which is how exhibits get placed inside a larger scene.

---

## 4. The version pragma

`pdb2pov` writes POV-Ray 2.x syntax, where `#declare` statements carry no
trailing semicolon. POV-Ray 3.5 and later reject that unless the language
version is pinned. Prepend one line:

```bash
printf '#version 3.1;\n' | cat - crambin_bs.pov > crambin.pov
```

POV-Ray still emits `Possible Parse Error` warnings about the missing
semicolons. They are warnings; the render is correct.

This applies to the include files too (`atoms_vdw.inc`, `atoms2.inc`,
`atoms_glass2.inc`), which is why the pragma has to lead the *scene*, not sit
inside it. Expect to need it for any pre-2000 scene in the archive.

---

## 5. Rendering as a hologram

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
    fov=53.13,                      # pdb2pov's lens: direction 1, up 1
)
spec = replace(QUILT_PRESETS["16-landscape"], view_cone=35.0)
quilt = render_pov_quilt("crambin.pov", spec, camera, include_paths=["path/to/pdb2pov"])
save_quilt(quilt, "out/crambin", spec)
```

Crambin at 7680×4320 takes about a minute, landing 4.5 px of adjacent-view
movement, symmetric front to back.

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
investigation. Parse two numbers out of the header, compute the focal
distance, render. It is worth wiring that into a helper if more than a few
structures are going through.

---

## Lineage

`pdb2pov` (1993) and `proteusPy.DisulfideVisualization` (2024) are the same
program written thirty years apart: read atoms, emit a sphere per atom scaled
by element radius, emit split-coloured cylinders per bond, colour by element.
One targets a ray-tracer and one targets VTK. Both now terminate at the same
place — [`assemble_quilt`](povray.md#5-api) — by different routes.
