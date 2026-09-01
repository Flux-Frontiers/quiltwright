---
name: docs-audit
description: Audit quiltwright's mkdocs documentation site before it ships -- replicate the GitHub Pages build (.github/workflows/docs.yml) in an isolated copy, separate new warnings from the pre-existing ones docs.yml already accepts, check every docs/*.md is reachable from mkdocs.yml's nav, and catch internal/non-public content sitting inside docs_dir. Use before cutting a quiltwright release, after editing anything under docs/, mkdocs.yml, or src/quiltwright/ docstrings, or whenever asked to audit/check the docs site or GitHub Pages build.
---

# Auditing quiltwright's docs site

`.github/workflows/docs.yml` builds and deploys `mkdocs build` on every push to
`main` -- there is no PR preview and no dry-run. A broken build only surfaces
after it's already live. This skill front-runs that.

## 1. Replicate the CI build, not the working tree

Building straight from the working tree is misleading: it includes
uncommitted edits and gitignored/local files that `actions/checkout` would
never see (this bit us once -- `docs/quiltwright_brand.md` looked like a
live orphaned page until we noticed it was gitignored and untracked, so CI
never builds it). Always build from a clean export of `HEAD`:

```bash
SCRATCH=$(mktemp -d)
git archive HEAD | tar -x -C "$SCRATCH"
cd "$SCRATCH"

# Mirror docs.yml's own pre-build step exactly -- keep this in sync with
# the "Bring the gallery images into docs_dir" step in .github/workflows/docs.yml.
cp -r gallery docs/gallery
sed -i '' 's#(\.\./gallery/#(gallery/#g' docs/gallery.md docs/index.md

/Users/egs/repos/quiltwright/.venv/bin/python -m mkdocs build --strict
```

Use `--strict` even though CI's own build does not -- CI intentionally
tolerates a known set of warnings (see docs.yml's "Not --strict" comment).
Running strict here is what surfaces the full list to sort through.

## 2. Triage every warning

Read `.github/workflows/docs.yml`'s "Not --strict" comment first -- it names
the two accepted categories as of the last time this skill was updated:

- Cross-links from `docs/*.md` to files outside `docs_dir` (`scripts/`,
  `pov-scenes/`, the top-level `README.md`) -- these render fine on GitHub
  but have no target inside the built site.
- `griffe` warnings from `mkdocstrings` on a `NamedTuple`'s `:param:`
  docstring not matching its synthesized `__init__` signature.

For each warning `mkdocs build --strict` prints: does it fall into one of
those categories? If yes, it's expected noise, not a finding. If no --
a genuinely broken internal link, a missing nav target, an import error, a
new docstring/signature mismatch outside the `NamedTuple` case -- it's a
real regression. Report those specifically; don't just dump the warning log.

If the set of accepted categories has grown (docs.yml's comment changed),
update this section to match -- it's meant to track that comment, not
duplicate it forever.

## 3. Nav completeness

Every tracked `docs/**/*.md` file must appear as a value in `mkdocs.yml`'s
`nav:` tree. `mkdocs build` happily builds and the `search` plugin indexes
any `.md` file under `docs_dir` whether or not it's in `nav` -- an
un-navved page still goes live, just unreachable except by guessing the
URL or finding it in search results.

```bash
git ls-files 'docs/*.md' 'docs/**/*.md'
```

Diff that list against the paths named in `mkdocs.yml`'s `nav:` block. Flag
any file not referenced -- it's either a missing nav entry (fix the nav) or
content that shouldn't be in `docs_dir` at all (see step 4).

## 4. Does this belong on the public site at all?

`docs_dir` is not a scratch space -- anything tracked under `docs/` ships to
`https://flux-frontiers.github.io/quiltwright/` on the next push to `main`,
nav entry or not. Before a release, scan for anything that reads as
internal process rather than a finished guide: design/brand prompts, draft
analysis, half-written notes, anything with the tone of "here's what I'm
thinking" rather than "here's how to use this." Quiltwright already treats
`analysis/` (PyCodeKG reports) as a case where most of it is fine to publish
in the repo but not everything is meant to stay -- apply the same judgment
to `docs/`. If something local needs to keep living under `docs/` for
convenience, gitignore it explicitly (see the `docs/quiltwright_brand.md`
entry in `.gitignore` for the pattern) rather than leaving it ambiguous.

## 5. Report

Summarize as:

- **Build**: clean / N pre-existing (expected) warnings / N new warnings
  needing a fix, with each new one named and pointed at a file:line.
- **Nav**: complete, or the specific untracked/un-navved files found.
- **Public-content check**: anything flagged in step 4, with a
  recommendation (move it, gitignore it, or it's fine as-is).

This is a read-only audit -- report findings and let the user decide fixes,
except for mechanical ones (an obviously missing nav entry) which can be
proposed as a direct edit.
