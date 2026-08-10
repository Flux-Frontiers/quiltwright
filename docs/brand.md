# Quiltwright — Brand Identity & Logo Generation Prompt

Quiltwright is **not** part of the KG product family (KGRAG, PyCodeKG, DocKG,
MemoryKG, GutenbergKG, DiaryKG, AgentKG, FTreeKG) and its cybernetic-brain
visual language, nor does it reuse WaveRider's manifold-and-observer icon. It
ships under the same **Flux-Frontiers** umbrella as WaveRider and shares that
family's general style strategy — flat vector, transparent background, no
gradients, no drop shadows, no 3D shading, no photorealism, square 1024×1024,
wordmark below in clean Futura sans-serif — but the mark itself is unique to
what Quiltwright does.

## Brand DNA

The whole point of the pipeline is driving real holographic hardware
(Looking Glass, HLD, Litiholo) — a scene comes in, an off-axis camera sweep
produces a set of views, those views assemble into a tiled "quilt," and the
quilt is what makes the hardware show depth. The logo has to end in an
actual hologram-like glyph, not just illustrate the quilting metaphor in the
abstract: **scene → sweep → quilt → hologram**.

## Color Palette

| Element | Color | Hex |
|---|---|---|
| Scene object, rays, seam-lines, wordmark | Holographic Indigo | `#5B4FE0` |
| Hologram glyph — ghost layer 1 | Cyan | `#00E5FF` |
| Hologram glyph — ghost layer 2 | Magenta | `#FF3EA5` |
| Hologram glyph — center layer | Holographic Indigo | `#5B4FE0` |
| Subtitle | Muted indigo-grey | `#8B85C4` |

Indigo is unclaimed across the sister-repo family (closest neighbor is
MemoryKG's violet `#9B4DCA`, distinct enough to sit side by side). The
cyan/magenta chromatic ghosting is the one place this logo breaks the
"single flat accent" rule the family otherwise follows — the same kind of
deliberate exception WaveRider makes for its translucent manifold fill,
justified here because it depicts a real optical phenomenon (parallax
ghosting reads universally as "glasses-free 3D").

## Logo Prompt

### Quiltwright — Light-Field Quiltmaker

> Flat vector logo. At the top, a single small faceted object — a gem-like
> polyhedron standing in for "any scene" (molecular structure, manifold,
> whatever feeds the pipeline) — rendered in clean steel-grey outline with
> flat fill, no shading. From it, 5-7 thin straight rays fan downward and
> outward at slightly different angles, like an open hand fan or sunburst —
> this is the off-axis camera sweep. Each ray terminates in a small tilted
> square tile, and these tiles are arranged into a tidy 3×3 grid below the
> fan — a quilt block. Each tile shows a faint duplicate silhouette of the
> object rotated a few degrees from its neighbor, so the grid reads as a
> contact sheet of near-identical views. Thin dashed seam-lines run between
> the tiles, like quilting stitches, in the primary accent color (Holographic
> Indigo, #5B4FE0). From the center of the quilt grid, the assembled image
> lifts upward and forward as a single glowing glyph — the same faceted
> object once more, but now drawn as three overlapping, semi-transparent
> silhouettes offset a few degrees from each other: one in cyan (#00E5FF),
> one in magenta (#FF3EA5), one in Holographic Indigo (#5B4FE0) dead-center —
> chromatic parallax ghosting, the universal visual shorthand for
> glasses-free holographic depth. This glyph is the largest, brightest
> element in the composition and sits above everything else as the clear
> terminus of the pipeline: scene → sweep → quilt → hologram. No shading or
> gradients anywhere except the deliberate transparency of the three ghost
> layers in the glyph itself, which is the one permitted optical effect
> since it depicts a real phenomenon. No drop shadows, no photorealism, no
> lens flares elsewhere. Below the composition, "Quiltwright" in bold clean
> Futura sans-serif, Holographic Indigo (#5B4FE0), with the subtitle
> "Holographic Output for Scientific Visualisation" beneath it in smaller,
> lighter weight, muted indigo-grey (#8B85C4). Fully transparent background
> (PNG with alpha). Square composition, 1024×1024.

## Generation Notes

**Recommended generators:**
- **Midjourney v6** — append `--style raw --ar 1:1 --no photorealism, shadows, gradients` to the prompt above.
- **DALL-E 3** — the prompt works as-is; request SVG-friendly flat style in the system message.
- **Stable Diffusion XL** — use with a flat-vector LoRA.

Once a version lands, export square PNGs at 512/256/128/64/32 alongside the
master, matching the sizing convention used in `doc_kg/assets/` and
`diary_kg/assets/logos/`.
