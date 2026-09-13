# bell-jar-portrait hologram

**Generated:** 2026-09-13 15:25:56  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `a8c6d18` (main) **+ uncommitted changes**  
**Commit:** 2026-09-13 14:42:34 -0400 -- chore(release): v0.13.0 release notes  
**Scene:** `pov-scenes/bell_jar/bj_portrait.pov` sha256 `db943b1cc0accde1`  
**Python:** 3.12.13  |  **quiltwright:** 0.10.1  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_still_life_hologram.py bell-jar-portrait --device 16-portrait --jobs 16 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | bell-jar-portrait |
| device | 16-portrait |
| quilt | 5995x6000 |
| tile | 545x1000 |
| aspect | 0.5625 |
| views | 66 |
| view cone | 35.0 deg |
| POV-Ray flags | +Q11 +A0.05 +AM2 +R4 |

## Parallelism

| Parameter | Value |
|---|---|
| CPU cores | 18 |
| POV-Ray processes (--jobs) | 16 |
| threads per process | 1 |
| thread count set by | +WT, derived from cores/jobs |
| cores in use | 16 of 18 |

## Camera

| Parameter | Value |
|---|---|
| eye | (0.0, 35.0, -95.0) |
| aim | (0.0, 21.92, 0.0) |
| field of view | 65.92 deg vertical |
| focal distance | 84.906 |
| near (measured) | 68.0 |
| far (measured, knee) | 113.0 |
| excluded from balance | sea and sky |

## Depth budget

```
  focal plane      84.9 units
  view cone        35.0 deg over 66 views
  eye sweep        +/-26.8 units
  adjacent-view disparity:
    nearest geometry       68.0   1.86 px
    focal plane            84.9   0.00 px
    structured far        113.0   1.86 px
    sea and sky (infinite)      inf   7.48 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 399 s |
| per view | 6.0 s |

## Caveat

composed 9:16 -- pass --device 16-portrait (or 27-/32-portrait, go); the default landscape panel will letterbox it

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/bell-jar-portrait_qs11x6a0.5625.png` |
| Size | 30.4 MB |
| SHA-256 | `af1e877ba548773987e82c2eb325bd1920022a76a86dc43319d4288190158233` |
