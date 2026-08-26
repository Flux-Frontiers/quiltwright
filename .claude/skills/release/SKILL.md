---
name: release
description: Cut a quiltwright release -- pick the version, promote CHANGELOG.md, sync every version-pinned surface (pyproject.toml, __init__.py, CITATION.cff, README badge/BibTeX/Latest-news/pinned asset URLs), rewrite release-notes.md as prose, tag, and push so CI builds, publishes to PyPI, and creates the GitHub Release. Use when the user asks to cut a release, bump the version, publish quiltwright to PyPI, or tag a new version of this repo. This is a quiltwright-specific procedure -- do not substitute a generic Python-package release flow, since this repo syncs version strings across five files by hand and a tag push triggers a real PyPI publish with no dry-run.
---

# Releasing quiltwright

Pushing a `vX.Y.Z` tag is irreversible: `.github/workflows/release.yml` builds
with Poetry, creates the GitHub Release from `release-notes.md`, and publishes
to PyPI via trusted OIDC publishing -- PyPI refuses to accept the same version
twice, so a botched tag cannot be re-pushed. Get every step right locally,
commit, and confirm with the user before tagging and pushing.

## 0. Preconditions

- `git status` clean, on `main`, up to date with `origin/main`.
- `CHANGELOG.md`'s `## [Unreleased]` section is non-empty and accurately
  describes everything that landed since the last tag (`git log vLAST..HEAD`
  if unsure). If it's thin or stale, fix it before proceeding -- this file is
  the source of truth the rest of this skill promotes from.
- Tests and lint pass (`pytest`; `ruff check` / `ruff format --check`).

## 1. Pick the version

Semantic versioning against the last tag (`git tag -l | tail -1`). Judge the
bump from what `## [Unreleased]` actually contains: new public API or
backend → minor; fixes/docs only → patch. This repo has not yet shipped a
1.0, so backwards-incompatible changes still bump minor, not major.

## 2. Promote the changelog

In `CHANGELOG.md`, turn

```
## [Unreleased]
```

into

```
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD
```

(today's date), leaving the *content* that was under `[Unreleased]` as the
new `[X.Y.Z]` section's body, and a genuinely empty `[Unreleased]` above it
for the next round.

## 3. Sync the version in every surface

Five files, six spots -- grep for the *old* version string across the repo
afterward to confirm nothing was missed (`grep -rn "OLD.VERSION" --include=*.md --include=*.toml --include=*.cff .`,
ignoring `CHANGELOG.md`'s historical entries and any gallery images pinned to
older tags on purpose):

| File | Field(s) |
|---|---|
| `pyproject.toml` | `version = "X.Y.Z"` under `[project]` -- `poetry version <patch\|minor\|major>` does this one arithmetically |
| `src/quiltwright/__init__.py` | `__version__ = "X.Y.Z"` |
| `CITATION.cff` | `version:` **and** `date-released:` (today) |
| `README.md` | the `Version` shields.io badge; the BibTeX block's `version = {...}` (and `year` if the release crosses a year boundary); the `## Latest news` heading and prose (rewrite it as a 2-4 sentence summary of the release, in this repo's voice -- see recent entries for tone); **both** `raw.githubusercontent.com/.../vX.Y.Z/...` asset URLs (the logo near the top and the gallery image), which must point at the *new* tag since GitHub only serves raw content from a ref that exists |

## 4. Rewrite `release-notes.md` as prose

This file is not the changelog -- it's narrative GitHub Release / PyPI-landing
copy, one release at a time (each new release overwrites it; history lives in
`CHANGELOG.md`, not here). Structure, matching prior releases:

```markdown
# Release Notes -- vX.Y.Z

> Released: YYYY-MM-DD

<1-2 paragraph narrative: what this release is *for*, told as a story, not a
list -- see release-notes.md's git history for tone and length>

## What changed

<one prose paragraph per major CHANGELOG entry, expanding the bullet into
2-4 sentences of the "why", not just restating the "what">
```

## 5. Commit

```bash
git add CHANGELOG.md CITATION.cff README.md pyproject.toml release-notes.md src/quiltwright/__init__.py
git commit -m "chore(release): vX.Y.Z release notes"
```

## 6. Confirm, then tag and push

This is the irreversible step -- **stop and confirm with the user before
running it** unless they already explicitly asked for the tag to be pushed.

```bash
git push origin main
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

The tag push triggers `release.yml`: build → GitHub Release from
`release-notes.md` → PyPI publish. Watch the Actions run; a failure there
(e.g. PyPI trusted-publishing misconfiguration) needs fixing and a
`workflow_dispatch` re-run against the existing tag, not a new tag.

## 7. Optional: quilt assets

Rendering the gallery quilts (bell-jar, porin, museum) takes 40 min-6+ hours
and is opt-in, never automatic:

```bash
make quilt-museum && make release-assets TAG=vX.Y.Z   # local, full quality
```

or re-run the `Release` workflow via `workflow_dispatch` with
`render_quilts: true` against the existing tag (CI renders at lower
antialias quality to fit the job time limit; see `release.yml`'s header
comment for the exact tradeoffs).
