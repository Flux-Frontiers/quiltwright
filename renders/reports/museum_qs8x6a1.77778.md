# Museum hologram

**Generated:** 2026-08-31 23:32:17  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `9c6c3cf` (main) **+ uncommitted changes**  
**Commit:** 2026-08-31 23:16:53 -0400 -- chore: drop quiltwright_analysis_after_p1_p2.md from analysis/  
**Scene:** `pov-scenes/museum/museum.pov` sha256 `e7c8814c2b2e1eff`  
**Python:** 3.12.13  |  **quiltwright:** 0.10.1  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_museum_hologram.py --jobs 1 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| device | 16-landscape |
| quilt | 7680x4320 |
| tile | 960x720 |
| aspect | 1.7778 |
| views | 48 |
| view cone | 30.4 deg |
| anti-aliasing | +A0.05 +AM2 +R4 |
| POV-Ray quality | +Q11 |

## Parallelism

| Parameter | Value |
|---|---|
| CPU cores | 18 |
| POV-Ray processes (--jobs) | 1 |
| threads per process | 16 |
| thread count set by | Work_Threads in /Users/egs/repos/quiltwright/renders/.threads.ini |
| cores in use | 16 of 18 |

## Camera

| Parameter | Value |
|---|---|
| focal distance | 40.444 |
| field of view | 53.13 deg vertical |
| nearest geometry | 26.0 |
| far interior | 91.0 |
| lateral corridor | -18.0 to 8.0 (margin 2.0) |

## Depth budget

```
  focal plane      40.4 units
  view cone        30.4 deg over 48 views
  eye sweep        +/-11.0 units (clearance +/-11.0 after 2.0 margin)
  adjacent-view disparity:
    nearest geometry       26.0   4.63 px
    focal plane            40.4   0.00 px
    far interior           91.0   4.63 px
    sky (infinite)          inf   8.33 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 387 s |
| per view | 8.1 s |

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/museum_qs8x6a1.77778.png` |
| Size | 41.3 MB |
| SHA-256 | `a761c61539bded6a25f2c8facaabc50f81d2655ffb1f997f22b7b29d922c9cc0` |
