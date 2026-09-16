# Quiltwright render targets.
#
#   make help            list targets
#   make gallery         all reference stills -> gallery/
#   make still-museum    one still (see STILL TARGETS below)
#   make quilts          all Looking Glass quilts -> renders/quilts/
#   make quilt-porin     one quilt
#   make preview-museum  quarter-size quilt for iterating
#
# Stills render at each scene's declared aspect (see renders/README.md —
# POV-Ray stretches silently if the pixel aspect disagrees with `right`).
# Quilts go through the scripts, which inject their own device camera.

# A bare `make` shows help; rendering is always an explicit ask.
.DEFAULT_GOAL := help

POVRAY  ?= povray
PYTHON  ?= .venv/bin/python
# The console script, not `$(PYTHON) -m quiltwright.cli.main`: main.py defines
# the click group but has no __main__ guard, so -m imports it and exits 0
# without running anything -- a target built that way silently renders nothing.
QUILTWRIGHT ?= .venv/bin/quiltwright

# Rendering leaves two cores for the rest of the machine, so a multi-minute
# quilt does not make the desktop unusable.  Override to use the whole box:
#   make quilts RENDER_THREADS=$(NCPU)
NCPU           ?= $(shell sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)
RENDER_THREADS ?= $(shell n=$(NCPU); [ $$n -gt 2 ] && echo $$((n - 2)) || echo 1)

# POV-Ray threads a single render across every core by default, and the only
# way to cap that for the quilt scripts -- which invoke povray themselves -- is
# an INI file named by POVINI.  A command-line +WT overrides it, which is why
# JOBS stays at 1 (see below).
#
# POVINI *replaces* the INI POV-Ray would otherwise have read; it does not add
# to it.  That default is what carries the Library_Path entries for the standard
# includes, so a file containing only Work_Threads makes colors.inc unfindable
# and every stock scene fails to parse.  The generated file is therefore a copy
# of the default with the cap appended -- later keys win, so the append is safe.
THREAD_INI := renders/.threads.ini
export POVINI = $(abspath $(THREAD_INI))

POV_BASE_INI ?= $(shell for f in "$$HOME/.povray/3.7/povray.ini" \
	                     /opt/homebrew/etc/povray/3.7/povray.ini \
	                     /usr/local/etc/povray/3.7/povray.ini \
	                     /etc/povray/3.7/povray.ini; do \
	                   [ -f "$$f" ] && { echo "$$f"; break; }; \
	                 done)

# Concurrent POV-Ray *processes*.  1 is both the render scripts' own default
# and the documented recommendation (docs/povray.md section 6): POV-Ray already
# threads one render across all cores, so extra processes buy nothing.  Raising
# it also defeats RENDER_THREADS -- quiltwright.povray derives its own +WT when
# jobs > 1, and a command-line +WT wins over POVINI.
JOBS    ?= 1

# +Q11: full quality.  +A0.1: final-pass anti-aliasing (stills; quilts set
# their own).  +FN: PNG.  -D: no preview window.
POVFLAGS ?= +FN -D +Q11 +A0.1

GALLERY := $(abspath gallery)
INC      = ../myinclude

# Regenerated every run so a changed RENDER_THREADS always takes effect.
# renders/ is gitignored, so this never reaches the repository.
.PHONY: $(THREAD_INI)
$(THREAD_INI):
	@mkdir -p $(dir $@)
	@test -n "$(POV_BASE_INI)" || { \
	   echo "warning: no povray.ini found; standard includes may not resolve" >&2; }
	@if [ -n "$(POV_BASE_INI)" ]; then cat "$(POV_BASE_INI)"; fi > $@
	@printf '\n;; appended by the quiltwright Makefile\nWork_Threads=%s\n' \
		'$(RENDER_THREADS)' >> $@

# --- STILL TARGETS ---------------------------------------------------------
# still-<name> renders pov-scenes/$(DIR)/$(SCENE) at $(SIZE) to
# gallery/<name>.png.  disc1.pov is absent: it does not render on
# Linux (asks for the standard includes in upper case).

still-bell_jar_bj:           DIR=bell_jar
still-bell_jar_bj:           SCENE=bj.pov
still-bell_jar_bj:           SIZE=+W900 +H1200

still-bell_jar_bj_holo:      DIR=bell_jar
still-bell_jar_bj_holo:      SCENE=bj_holo.pov
still-bell_jar_bj_holo:      SIZE=+W1920 +H1080

still-bell_jar_bj_holo_2026: DIR=bell_jar
still-bell_jar_bj_holo_2026: SCENE=bj_holo_2026.pov
still-bell_jar_bj_holo_2026: SIZE=+W1920 +H1080

still-bell_jar_bj_portrait:  DIR=bell_jar
still-bell_jar_bj_portrait:  SCENE=bj_portrait.pov
still-bell_jar_bj_portrait:  SIZE=+W1080 +H1920

still-bell_jar_bj_black:     DIR=bell_jar
still-bell_jar_bj_black:     SCENE=bj_black.pov
still-bell_jar_bj_black:     SIZE=+W900 +H1200

still-bell_jar_bdna:         DIR=bell_jar
still-bell_jar_bdna:         SCENE=bdna.pov
still-bell_jar_bdna:         SIZE=+W900 +H1200

still-bell_jar_yinyang:      DIR=bell_jar
still-bell_jar_yinyang:      SCENE=yinyang.pov
still-bell_jar_yinyang:      SIZE=+W1500 +H1200

still-bell_jar_bdna_variant: DIR=bell_jar/bdna
still-bell_jar_bdna_variant: SCENE=bdna.pov
still-bell_jar_bdna_variant: SIZE=+W600 +H1200
still-bell_jar_bdna_variant: INC=../../myinclude ..

still-porin_3porin:          DIR=porin
still-porin_3porin:          SCENE=3porin.pov
still-porin_3porin:          SIZE=+W1920 +H1080

still-museum:                DIR=museum
still-museum:                SCENE=museum.pov
still-museum:                SIZE=+W1920 +H1080

still-museum_970211:         DIR=museum
still-museum_970211:         SCENE=museum_970211.pov
still-museum_970211:         SIZE=+W1600 +H1200

still-museum_pg:             DIR=museum
still-museum_pg:             SCENE=museum_pg.pov
still-museum_pg:             SIZE=+W1500 +H1200

still-museum_2026:           DIR=museum
still-museum_2026:           SCENE=museum_2026.pov
still-museum_2026:           SIZE=+W1920 +H1080

still-lambda_main:           DIR=lambda
still-lambda_main:           SCENE=lambda_main.pov
still-lambda_main:           SIZE=+W1920 +H1080

# The vitrine exhibits are deliberately not here: they need pdb2pov's include
# directory, whose path is per-machine (`pypdb2pov --include-dir` prints it),
# so they render through scripts/render_vitrine.py rather than through a make
# target that would have to guess.  See pov-scenes/vitrine/README.md.
# still-bell_jar_bj_black, still-bell_jar_bdna_variant and still-museum_970211
# are absent by choice rather than by oversight.  Their scenes are in the tree
# and their targets below still work on demand; they are simply not part of
# the presented set any more, and listing them here would put their images
# back in gallery/ on the next `make gallery`.
STILL_TARGETS := still-bell_jar_bj still-bell_jar_bj_holo \
                 still-bell_jar_bj_holo_2026 \
                 still-bell_jar_bj_portrait \
                 still-bell_jar_bdna \
                 still-bell_jar_yinyang \
                 still-porin_3porin \
                 still-museum \
                 still-museum_pg still-museum_2026 still-lambda_main

still-%: $(THREAD_INI)
	@mkdir -p $(GALLERY)
	cd pov-scenes/$(DIR) && $(POVRAY) +I$(SCENE) $(addprefix +L,$(INC)) \
		+O$(GALLERY)/$*.png $(SIZE) $(POVFLAGS) +WT$(RENDER_THREADS)

.PHONY: gallery stills
gallery: $(STILL_TARGETS)  ## render every reference still -> gallery/
# Kept so anything that already types `make stills` still works.  renders/
# stills/ is now local scratch; the committed set is gallery/.
stills: gallery

# --- QUILTS ----------------------------------------------------------------
# The scripts place the focal plane from measured depths and sweep the view
# cone; see docs/pov-workflow.md.  Output: renders/quilts/<subject>_qs....png

# Every full quilt writes a run report to renders/reports/ -- the quilt itself
# is a gitignored release asset, so the report is the only committed record of
# which scene, commit, camera and POV-Ray produced it. Previews skip it: they
# are iterations, and reports are tracked.
#
# EXTRA_ARGS passes through to the render script, e.g.
#   make quilt-museum EXTRA_ARGS="--antialias 0.1"
EXTRA_ARGS ?=

.PHONY: quilt-bell-jar quilt-bell-jar-holo quilt-bell-jar-holo-2026 quilt-bell-jar-portrait quilt-porin quilt-lambda quilt-museum quilts
quilt-bell-jar:  $(THREAD_INI)  ## bell jar quilt, 16" landscape (~3 min uncapped on 18 cores)
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar --jobs $(JOBS) --report $(EXTRA_ARGS)

# bj_holo.pov: the same scene re-composed 16:9, with the title and signature
# moved out to the focal plane.  Native landscape, so no --fov correction.
quilt-bell-jar-holo:  $(THREAD_INI)  ## recomposed bell jar quilt, 16" landscape
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar-holo --jobs $(JOBS) --report $(EXTRA_ARGS)

# bj_holo_2026.pov: the same frame with real refracting crystal in place of
# the 1996 tinted film.  Same camera as quilt-bell-jar-holo, so the same
# focal plane and the same sweep.
quilt-bell-jar-holo-2026:  $(THREAD_INI)  ## crystal bell jar quilt, 16" landscape
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar-holo-2026 --jobs $(JOBS) --report $(EXTRA_ARGS)

# bj_portrait.pov: the 9:16 companion, for the tall panels (16/27/32-portrait,
# go).  Pass --device to pick one; the default 16-landscape would letterbox it.
quilt-bell-jar-portrait:  $(THREAD_INI)  ## portrait bell jar quilt, 16" portrait
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar-portrait --device 16-portrait --jobs $(JOBS) --report $(EXTRA_ARGS)

quilt-porin:  $(THREAD_INI)  ## porin quilt, 16" landscape (~2 min uncapped on 18 cores)
	$(PYTHON) scripts/render_still_life_hologram.py porin --jobs $(JOBS) --report $(EXTRA_ARGS)

# Composed 16:9 in 1998 (right <HDTV>), so its framing is native on a landscape
# panel and no --fov correction is needed.  Its timing is the only one measured
# under the defaults above (16 threads, JOBS=1); the other three predate the cap.
quilt-lambda:  $(THREAD_INI)  ## lambda repressor quilt, 16" landscape (~2.5 min at 16 threads)
	$(PYTHON) scripts/render_still_life_hologram.py lambda --jobs $(JOBS) --report $(EXTRA_ARGS)

quilt-museum:  $(THREAD_INI)  ## museum quilt, 16" landscape (~6 min uncapped; the slow one)
	$(PYTHON) scripts/render_museum_hologram.py --jobs $(JOBS) --report $(EXTRA_ARGS)

quilts: quilt-bell-jar quilt-porin quilt-lambda quilt-museum  ## all four quilts

# The PyVista subjects. Seconds each, not minutes -- VTK rasterises where
# POV-Ray ray-traces -- so there is no --jobs and no preview variant.
#
# Two of them need a cone narrower than the 35 deg the script falls back to:
# both are wide terrain with the horizon at true infinity, which puts far
# disparity past the 4-5 px a panel can fuse. The values below are measured,
# not guessed -- st-helens runs 8.0 px at 35 deg and 4.5 at 20; damavand 5.4
# and 4.4 at 29. brain and mouse-brain are bounded volumes and stay in budget
# on the default.
.PHONY: quilt-brain quilt-damavand quilt-mouse-brain quilt-st-helens quilts-pyvista
quilt-brain:  ## brain quilt, 16" landscape (PyVista)
	$(PYTHON) scripts/render_pyvista_hologram.py brain $(EXTRA_ARGS)

quilt-damavand:  ## Damavand terrain quilt, 16" landscape (PyVista, cone 29)
	$(PYTHON) scripts/render_pyvista_hologram.py damavand --view-cone 29 $(EXTRA_ARGS)

quilt-mouse-brain:  ## Allen Institute mouse brain quilt, portrait (PyVista)
	$(PYTHON) scripts/render_pyvista_hologram.py mouse-brain $(EXTRA_ARGS)

quilt-st-helens:  ## Mount St Helens quilt, 16" landscape (PyVista, cone 20)
	$(PYTHON) scripts/render_pyvista_hologram.py st-helens --view-cone 20 $(EXTRA_ARGS)

quilts-pyvista: quilt-brain quilt-damavand quilt-mouse-brain quilt-st-helens  ## all four PyVista quilts

# The ParaView subjects. The sweep runs inside ParaView's own pvpython, so
# this needs a ParaView install (`quiltwright paraview --check`) and nothing
# from the Python environment beyond quiltwright itself.
#
# Run from the repository root, always: the state file locates terrain.csv by
# a path relative to the working directory, not to itself, and a state that
# cannot find its data renders an empty scene rather than failing. See
# paraview-scenes/README.md.
#
# Every target passes --device explicitly. The command's default device is a
# convenience that can change -- it moved from portrait to 16-landscape -- and a
# target that leaned on it would silently render something else afterwards.
.PHONY: quilt-mount-hood quilt-mount-hood-portrait still-mount-hood

# Landscape is the primary layout. Its tiles are wider than portrait's (960x720
# against 420x560) and its native cone is 50 deg, so the portrait settings do
# not carry over: at zoom 1.62 and 50 deg this measured 10.4 px, nearly double
# the ceiling. Cone and zoom trade against each other at constant disparity --
# 35 deg allows zoom 1.30, 25 deg about 1.75, 20 deg about 2.1. This takes
# 20 deg for the tightest framing: 5.41 px near, 4.32 px far, with a narrower
# look-around range as the price.
quilt-mount-hood:  ## Mount Hood terrain quilt, 16" landscape (ParaView, cone 20)
	$(QUILTWRIGHT) paraview paraview-scenes/mount-hood/mount-hood.pvsm \
		--device 16-landscape --view-cone 20 --zoom 2.10 \
		--out renders/quilts/mount-hood $(EXTRA_ARGS)

# The portrait companion. Portrait's native cone is already 35 deg, so no
# override is needed; --zoom 1.62 is its measured ceiling, 5.49 px against 5.5.
quilt-mount-hood-portrait:  ## Mount Hood terrain quilt, portrait (ParaView)
	$(QUILTWRIGHT) paraview paraview-scenes/mount-hood/mount-hood.pvsm \
		--device portrait --zoom 1.62 --out renders/quilts/mount-hood-portrait $(EXTRA_ARGS)

# Not in STILL_TARGETS, so `make gallery` does not require a ParaView install.
# save_quilt() appends the _qs metadata suffix every backend writes, and that
# pattern is gitignored everywhere, so the committed gallery name is taken
# from under it afterwards. Portrait, to reproduce the committed image.
still-mount-hood:  ## Mount Hood flat still -> gallery/mount_hood.png (ParaView, portrait)
	@mkdir -p $(GALLERY)
	$(QUILTWRIGHT) paraview paraview-scenes/mount-hood/mount-hood.pvsm \
		--device portrait --zoom 1.62 --still --out $(GALLERY)/mount_hood $(EXTRA_ARGS)
	mv $(GALLERY)/mount_hood_qs*.png $(GALLERY)/mount_hood.png

# The Looking Glass Go set: 9:16, 11x6, 66 views.  The Go's native cone is 54
# deg, the calibration Bridge reports.  The two DNA scenes are composed for it
# and render at that cone -- on a dark ground there is nothing to ghost, and
# the 35-degree cap would drop a third of their parallax.  Everything else
# takes the cap.  bell-jar-portrait is already composed 9:16 and plays on the
# Go as quilt-bell-jar-portrait renders it.
.PHONY: quilt-bdna-go quilt-dna-ribbon-go quilt-f1atpase-go quilt-f1atpase-cartoon-go quilt-porin-portrait-go quilt-mount-hood-go quilt-brain-go quilts-go playlist-go
quilt-bdna-go:  $(THREAD_INI)  ## B-DNA from DNA Under Glass, Looking Glass Go (cone 54)
	$(PYTHON) scripts/render_still_life_hologram.py bdna-go --device go --view-cone 54 --jobs $(JOBS) --report $(EXTRA_ARGS)

quilt-dna-ribbon-go:  $(THREAD_INI)  ## the museum's metallic DNA ribbon, Looking Glass Go (cone 54)
	$(PYTHON) scripts/render_still_life_hologram.py dna-ribbon-go --device go --view-cone 54 --jobs $(JOBS) --report $(EXTRA_ARGS)

quilt-f1atpase-go:  $(THREAD_INI)  ## F1-ATPase exhibit (vitrine case), Looking Glass Go
	$(PYTHON) scripts/render_vitrine.py f1atpase --device go --jobs $(JOBS) $(EXTRA_ARGS)

# The molecule alone, no exhibit case: a real PyMOL cartoon (154668 vertices,
# 307824 faces) of 1BMF, bovine mitochondrial F1-ATPase -- alpha3beta3gamma,
# the rotary motor headpiece.  cartoon_inc() does not reorient the structure,
# so the default elevated-3/4 VIEW_DIRECTION is arbitrary against it; this one
# is measured instead, PCA on the CA atoms of the biological assembly
# (see scripts/render_cartoon_hologram.py's module docstring for the method).
# The assembly turns out close to isotropic -- no long axis with an obvious
# "top" -- so the three PCA axes were compared by eye rather than picked by
# variance; this one gave the clearest read of the alternating alpha/beta
# arrangement.  --view-direction takes it in the structure's own frame.
# --view-cone 54, the Go's native one: the cartoon fills almost the whole
# frame, so there is little backdrop to ghost, the same reasoning
# quilt-bdna-go and quilt-dna-ribbon-go apply.
quilt-f1atpase-cartoon-go:  ## F1-ATPase cartoon, molecule only, Looking Glass Go (cone 54)
	$(PYTHON) scripts/render_cartoon_hologram.py molecules/1bmf.cif.gz \
		--backend povray --device go --view-cone 54 --view-direction 0.961 0.114 -0.251 \
		--out renders/quilts/f1atpase-cartoon-go $(EXTRA_ARGS)

# 3porin.pov's ASPECT/CAM_X/CAM_Z declares are guarded (#ifndef), and
# porin_portrait.pov sets all three itself before #include-ing it, so
# nothing scene-specific needs passing here beyond --device.  --view-cone 54
# is the Go's own, same as the two DNA scenes above: the subject itself
# measures 3.07 px at that cone, well inside budget.  Only the "sea and sky
# (infinite)" residual runs soft (10.7 px), and that is the *backdrop* field
# every still-life subject already excludes from its depth budget on
# purpose -- porin's original 16:9 cut carries the same "sea and sky"
# backdrop and the same exclusion, not something new to the portrait cut.
quilt-porin-portrait-go:  $(THREAD_INI)  ## porin trimer, recomposed 9:16, Looking Glass Go
	$(PYTHON) scripts/render_still_life_hologram.py porin-portrait --device go --view-cone 54 --jobs $(JOBS) --report $(EXTRA_ARGS)

quilt-mount-hood-go:  ## Mount Hood terrain, Looking Glass Go (ParaView)
	$(QUILTWRIGHT) paraview paraview-scenes/mount-hood/mount-hood.pvsm \
		--device go --zoom 1.62 --out renders/quilts/mount-hood-go $(EXTRA_ARGS)

quilt-brain-go:  ## brain, Looking Glass Go (PyVista)
	$(PYTHON) scripts/render_pyvista_hologram.py brain --device go --out renders/quilts/brain-go $(EXTRA_ARGS)

quilts-go: quilt-bdna-go quilt-dna-ribbon-go quilt-bell-jar-portrait quilt-f1atpase-go quilt-f1atpase-cartoon-go quilt-porin-portrait-go quilt-mount-hood-go quilt-brain-go  ## the whole Go set

# The Go set in playing order.  PANEL_HEAD is the Bridge head the Go is on --
# `quiltwright cast --check` lists them; -1 lets Bridge choose, which is right
# with no other display attached.  f1atpase-cartoon-go plays in place of the
# vitrine exhibit case: the molecule alone reads better on the panel than the
# case's atomic-sphere model, which quilt-f1atpase-go still renders for anyone
# who wants the exhibit framing back.
GO_QUILTS  := bdna-go dna-ribbon-go bell-jar-portrait f1atpase-cartoon-go porin-portrait mount-hood-go brain-go
PANEL_HEAD ?= -1
playlist-go:  ## play the Go set as one looping playlist (PANEL_HEAD=<index>)
	$(QUILTWRIGHT) playlist $(foreach s,$(GO_QUILTS),renders/quilts/$(s)_qs11x6a0.5625.png) \
		--head $(PANEL_HEAD) $(EXTRA_ARGS)

.PHONY: preview-bell-jar preview-bell-jar-holo preview-bell-jar-holo-2026 preview-bell-jar-portrait preview-porin preview-lambda preview-museum
preview-bell-jar: $(THREAD_INI)  ## quarter-size bell jar quilt for iterating
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar --preview --jobs $(JOBS)

preview-bell-jar-holo: $(THREAD_INI)  ## quarter-size recomposed bell jar quilt
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar-holo --preview --jobs $(JOBS)

preview-bell-jar-holo-2026: $(THREAD_INI)  ## quarter-size crystal bell jar quilt
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar-holo-2026 --preview --jobs $(JOBS)

preview-bell-jar-portrait: $(THREAD_INI)  ## quarter-size portrait bell jar quilt
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar-portrait --device 16-portrait --preview --jobs $(JOBS)

preview-porin: $(THREAD_INI)  ## quarter-size porin quilt
	$(PYTHON) scripts/render_still_life_hologram.py porin --preview --jobs $(JOBS)

preview-lambda: $(THREAD_INI)  ## quarter-size lambda repressor quilt
	$(PYTHON) scripts/render_still_life_hologram.py lambda --preview --jobs $(JOBS)

preview-museum: $(THREAD_INI)  ## quarter-size museum quilt
	$(PYTHON) scripts/render_museum_hologram.py --preview --jobs $(JOBS)

# --- HOUSEKEEPING ----------------------------------------------------------

# The subjects a release actually bundles. renders/quilts/ accumulates every
# scene anyone has ever iterated on (lambda, brain, vitrine-hemoglobin, ...)
# plus a -preview render per subject, and *_qs*.png matches all of it -- a
# glob that broad would attach unrelated exploratory renders and quarter-size
# iterations to a public GitHub release. <subject>_qs*.png (no dash before
# _qs) matches only that subject's full-quality quilt, since every preview
# and variant inserts a -suffix before _qs. Override per release when the
# "current" cut of a scene changes, e.g.
#   make release-assets TAG=v1.2.3 RELEASE_QUILT_SUBJECTS="bell-jar porin museum"
RELEASE_QUILT_SUBJECTS ?= bell-jar-holo-2026 bell-jar-portrait porin porin-litiholo \
                          museum lambda vitrine-hemoglobin mount-hood mount-hood-portrait \
                          brain damavand mouse-brain st-helens

# Dynamic Desktop HEICs and HLD videos to bundle. Both are backend output a
# quilt cannot stand in for -- the HEICs carry the day/night appearance pair,
# the mp4s the HLD sweep -- so they ship alongside rather than instead. Clear
# it for a release that ships neither:
#   make release-assets TAG=v1.2.3 RELEASE_DYNAMIC_ASSETS=
RELEASE_DYNAMIC_ASSETS ?= renders/dynamic/bj_holo_2026_appearance.heic \
                          renders/dynamic/bj_holo_2026_appearance_native_LKG-J00332.heic \
                          renders/hld/bell-jar-holo-2026_hld.mp4 \
                          renders/hld/bell-jar-portrait_hld.mp4

.PHONY: release-assets clean-views help
release-assets:  ## attach the release-bundle quilts (and any dynamic HEICs) to a GitHub release: make release-assets TAG=v1.2.3
	@test -n "$(TAG)" || { echo "usage: make release-assets TAG=v1.2.3"; exit 1; }
	gh release upload $(TAG) $(foreach s,$(RELEASE_QUILT_SUBJECTS),renders/quilts/$(s)_qs*.png) $(RELEASE_DYNAMIC_ASSETS) --clobber

clean-views:  ## empty the renders/views/ scratch directory
	rm -rf renders/views/*

help:  ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'
	@echo "  still-<name>       one still; names: $(subst still-,,$(STILL_TARGETS))"
