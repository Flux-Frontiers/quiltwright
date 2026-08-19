# Release Notes -- v0.7.0

> Released: 2026-08-18

Quiltwright could render a quilt and hand it to Bridge; everything after that
was manual. This release closes that gap. Three new CLI commands cover the
whole tail of the pipeline -- putting a quilt on the panel, hanging a woven
frame on the desktop, and telling you which of those two is broken when the
glass goes black. Alongside them, every full quilt now writes a provenance
record, because a quilt is a 25-40 MB PNG that says nothing about where it
came from.

## What changed

**The CLI reaches the panel.** `quiltwright cast` shows a saved quilt on the
display, recovering the tiling and aspect from the `_qs<cols>x<rows>a<aspect>`
filename suffix, so it usually needs no flags at all. It sits downstream of the
assembler, which means it does not care whether the views came from a PyVista
scene or a POV-Ray one. `cast --check` lists what Bridge can actually see and
marks which heads are Looking Glass panels rather than ordinary monitors --
Bridge enumerates both, and a cast landing on a laptop screen fails silently.

**A hologram you can leave on the desktop.** `quiltwright wallpaper` completes
the path that needs no Looking Glass software running at all. A woven frame is
already interleaved for one specific panel, so displaying it 1:1 *is* the
hologram, and the simplest thing that displays an image 1:1 forever is the
desktop picture. The command matches frame to display by the panel serial both
carry, installs it somewhere stable first -- macOS stores wallpaper as a path,
so pointing the desktop into `renders/` blanks the panel the next time that
directory is cleaned -- and refuses to guess when no display matches, because a
woven frame on the wrong panel is a screenful of noise.

**Bridge, which fails dishonestly.** `quiltwright bridge status` and `reset`
exist because Bridge keeps its HTTP port open and keeps issuing valid
orchestration tokens after it has crashed internally. A cast then reports
success at every step against a daemon that will never draw a pixel, and the
only symptom is a black panel. `status` therefore distrusts a bare 200: it
walks the port, the session, the device enumeration, and whether any device is
a panel at all, then gives a verdict and a matching exit code so it can gate a
cast in a script. `reset` kills every Bridge process and relaunches, which is
the only reliable fix -- Bridge's own menu restart spawns a replacement that
inherits the wedge.

**Run reports.** Every full quilt from `make` now writes a Markdown provenance
record to `renders/reports/`. Quilts are release assets and are not committed,
so without this there is nothing in the repository saying how one was made. The
report carries the scene file *and its SHA-256* -- composing a scene means
rendering against an edited working copy, so the commit alone can describe a
tree the render never saw -- along with the camera and its measured depths, the
depth budget verbatim as printed, the parallelism actually used, timings, and
the output's own digest.

**A render outside `make` no longer takes the whole machine.** POV-Ray threads
one render across every core it can see, and neither existing guard applied at
the documented `jobs=1`. So `make quilt-museum` held two cores back and calling
the same script directly did not. There is now a courtesy cap, and a
`--threads` flag to set or disable it. It yields to a `Work_Threads` line in
`POVINI`, because a command-line `+WT` overrides an INI outright and capping
unconditionally would have defeated `make quilts RENDER_THREADS=$(nproc)`.

**Housekeeping.** The CLI is now a package of `cmd_*` modules matching the rest
of the fleet, which moved the console-script entry point. The README no longer
describes Quiltwright as the tail of two specific pipelines: it takes any
PyVista/VTK scene in memory and any POV-Ray scene on disk, and WaveRider and
pdb2pov are users rather than prerequisites.

## Upgrading

Nothing to migrate. `pip install -U quiltwright` and the new commands are
there; `quiltwright --help` lists them.

Two things to know. If you imported `quiltwright.cli` directly -- an
undocumented path -- it is now `quiltwright.cli.main`; the `quiltwright`
console script is unaffected. And if you drive the render scripts yourself
rather than through `make`, they now hold two cores back by default; pass
`--threads 0` to restore the old behaviour of taking every core.

When a cast leaves the panel black, start with `quiltwright bridge status`
rather than re-rendering.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
