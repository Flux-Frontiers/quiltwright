# Quiltwright render targets.
#
#   make help            list targets
#   make stills          all reference stills -> renders/stills/
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
JOBS    ?= $(shell sysctl -n hw.ncpu 2>/dev/null || nproc)

# +Q11: full quality.  +A0.1: final-pass anti-aliasing (stills; quilts set
# their own).  +FN: PNG.  -D: no preview window.
POVFLAGS ?= +FN -D +Q11 +A0.1

STILLS  := $(abspath renders/stills)
INC      = ../myinclude

# --- STILL TARGETS ---------------------------------------------------------
# still-<name> renders pov-scenes/$(DIR)/$(SCENE) at $(SIZE) to
# renders/stills/<name>.png.  disc1.pov is absent: it does not render on
# Linux (asks for the standard includes in upper case).

still-bell_jar_bj:           DIR=bell_jar
still-bell_jar_bj:           SCENE=bj.pov
still-bell_jar_bj:           SIZE=+W900 +H1200

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

still-porin_3porin2:         DIR=porin
still-porin_3porin2:         SCENE=3porin2.pov
still-porin_3porin2:         SIZE=+W1600 +H1200

still-museum:                DIR=museum
still-museum:                SCENE=museum.pov
still-museum:                SIZE=+W1920 +H1080

still-museum_dark:           DIR=museum
still-museum_dark:           SCENE=museum_dark.pov
still-museum_dark:           SIZE=+W1600 +H1200

still-museum_970211:         DIR=museum
still-museum_970211:         SCENE=museum_970211.pov
still-museum_970211:         SIZE=+W1600 +H1200

still-museum_pg:             DIR=museum
still-museum_pg:             SCENE=museum_pg.pov
still-museum_pg:             SIZE=+W1500 +H1200

still-museum_worldmap:       DIR=museum
still-museum_worldmap:       SCENE=worldmap.pov
still-museum_worldmap:       SIZE=+W1600 +H1200

still-lambda_main:           DIR=lambda
still-lambda_main:           SCENE=lambda_main.pov
still-lambda_main:           SIZE=+W1920 +H1080

STILL_TARGETS := still-bell_jar_bj still-bell_jar_bj_black still-bell_jar_bdna \
                 still-bell_jar_yinyang still-bell_jar_bdna_variant \
                 still-porin_3porin still-porin_3porin2 \
                 still-museum still-museum_dark still-museum_970211 \
                 still-museum_pg still-museum_worldmap still-lambda_main

still-%:
	@mkdir -p $(STILLS)
	cd pov-scenes/$(DIR) && $(POVRAY) +I$(SCENE) $(addprefix +L,$(INC)) \
		+O$(STILLS)/$*.png $(SIZE) $(POVFLAGS)

.PHONY: stills
stills: $(STILL_TARGETS)  ## render every reference still

# --- QUILTS ----------------------------------------------------------------
# The scripts place the focal plane from measured depths and sweep the view
# cone; see docs/pov-workflow.md.  Output: renders/quilts/<subject>_qs....png

# EXTRA_ARGS passes through to the render script, e.g.
#   make quilt-museum EXTRA_ARGS="--antialias 0.1"
EXTRA_ARGS ?=

.PHONY: quilt-bell-jar quilt-porin quilt-museum quilts
quilt-bell-jar:  ## bell jar quilt, 16" landscape (~9 min on 18 cores)
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar --jobs $(JOBS) $(EXTRA_ARGS)

quilt-porin:  ## porin quilt, 16" landscape (~18 min on 18 cores)
	$(PYTHON) scripts/render_still_life_hologram.py porin --jobs $(JOBS) $(EXTRA_ARGS)

quilt-museum:  ## museum quilt, 16" landscape (the slow one)
	$(PYTHON) scripts/render_museum_hologram.py --jobs $(JOBS) $(EXTRA_ARGS)

quilts: quilt-bell-jar quilt-porin quilt-museum  ## all three quilts

.PHONY: preview-bell-jar preview-porin preview-museum
preview-bell-jar:  ## quarter-size bell jar quilt for iterating
	$(PYTHON) scripts/render_still_life_hologram.py bell-jar --preview --jobs $(JOBS)

preview-porin:  ## quarter-size porin quilt
	$(PYTHON) scripts/render_still_life_hologram.py porin --preview --jobs $(JOBS)

preview-museum:  ## quarter-size museum quilt
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
