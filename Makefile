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
# focal plane and the same sweep -- but `dispersion` on the glass makes it
# roughly 4.5x the render.  Preview first.
quilt-bell-jar-holo-2026:  $(THREAD_INI)  ## crystal bell jar quilt, 16" landscape (slow -- dispersion)
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

.PHONY: release-assets clean-views help
release-assets:  ## attach quilts to a GitHub release: make release-assets TAG=v1.2.3
	@test -n "$(TAG)" || { echo "usage: make release-assets TAG=v1.2.3"; exit 1; }
	gh release upload $(TAG) renders/quilts/*_qs*.png --clobber

clean-views:  ## empty the renders/views/ scratch directory
	rm -rf renders/views/*

help:  ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'
	@echo "  still-<name>       one still; names: $(subst still-,,$(STILL_TARGETS))"
