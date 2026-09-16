# porin-portrait hologram

**Generated:** 2026-09-15 18:46:34  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `f994fc8` (feature/porin-portrait) **+ uncommitted changes**  
**Commit:** 2026-09-15 15:51:26 -0400 -- feat: quiltwright playlist, and a Looking Glass Go set with two new scenes (#62)  
**Scene:** `pov-scenes/porin/porin_portrait.pov` sha256 `76897f760412409a`  
**Python:** 3.12.13  |  **quiltwright:** 0.10.1  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_still_life_hologram.py porin-portrait --device go --view-cone 54 --jobs 16 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | porin-portrait |
| device | go |
| quilt | 4092x4092 |
| tile | 372x682 |
| aspect | 0.5625 |
| views | 66 |
| view cone | 54.0 deg |
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
| eye | (20.0, 0.0, -1300.0) |
| aim | (20.0, 0.0, 0.0) |
| field of view | 53.13 deg vertical |
| focal distance | 1133.299 |
| near (measured) | 880.2 |
| far (measured, knee) | 1590.7 |
| excluded from balance | sea and sky |

## Depth budget

```
  focal plane      1133.3 units
  view cone        54.0 deg over 66 views
  eye sweep        +/-577.4 units
  adjacent-view disparity:
    nearest geometry      880.2   3.07 px
    focal plane          1133.3   0.00 px
    structured far       1590.7   3.07 px
    sea and sky (infinite)      inf  10.69 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 78 s |
| per view | 1.2 s |

## Caveat

composed 9:16 for the Looking Glass Go -- pass --device go

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/porin-portrait_qs11x6a0.5625.png` |
| Size | 18.0 MB |
| SHA-256 | `1828a74f970d812f621a08a7e905b2b41b6617da4097d6f15fd91865b8f1c57f` |
