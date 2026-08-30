# porin hologram

**Generated:** 2026-08-30 18:41:43  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `e02fdc5` (develop)  
**Commit:** 2026-08-30 18:33:04 -0400 -- feat(scripts): render a LitiHolo sweep from the still-life script  
**Scene:** `pov-scenes/porin/3porin.pov` sha256 `2c97fadb3306a4e8`  
**Python:** 3.12.13  |  **quiltwright:** 0.10.0  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_still_life_hologram.py porin --sweep --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | porin |
| device | LitiHolo sweep (23 views, 45 deg) |
| quilt | 36800x2000 |
| tile | 1600x2000 |
| aspect | 0.8000 |
| views | 23 |
| view cone | 45.0 deg |
| anti-aliasing | +A0.05 +AM2 +R4 |
| POV-Ray quality | +Q11 |

## Parallelism

| Parameter | Value |
|---|---|
| CPU cores | 18 |
| POV-Ray processes (--jobs) | 1 |
| threads per process | 16 |
| thread count set by | +WT courtesy cap |
| cores in use | 16 of 18 |

## Camera

| Parameter | Value |
|---|---|
| eye | (0.0, 0.0, -1100.0) |
| aim | (0.0, 0.0, 0.0) |
| field of view | 53.13 deg vertical |
| focal distance | 972.603 |
| near (measured) | 790.0 |
| far (measured, knee) | 1265.0 |
| excluded from balance | sea and sky |

## Depth budget

```
  focal plane      972.6 units
  view cone        45.0 deg over 23 views
  eye sweep        +/-402.9 units
  adjacent-view disparity:
    nearest geometry      790.0  17.41 px  <- soft
    focal plane           972.6   0.00 px
    structured far       1265.0  17.41 px  <- soft
    sea and sky (infinite)      inf  75.31 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 243 s |
| per view | 10.6 s |

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/porin-litiholo_qs23x1a0.8.png` |
| Size | 53.1 MB |
| SHA-256 | `f6d642df586f80a01c79268e08a64dd4b177305ab1215e8fe0f55dcb692c24ba` |
