# bell-jar-holo-2026 hologram

**Generated:** 2026-09-13 15:18:50  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `a8c6d18` (main) **+ uncommitted changes**  
**Commit:** 2026-09-13 14:42:34 -0400 -- chore(release): v0.13.0 release notes  
**Scene:** `pov-scenes/bell_jar/bj_holo_2026.pov` sha256 `6e42c773fde23189`  
**Python:** 3.12.13  |  **quiltwright:** 0.10.1  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_still_life_hologram.py bell-jar-holo-2026 --jobs 16 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | bell-jar-holo-2026 |
| device | 16-landscape |
| quilt | 7680x4320 |
| tile | 960x720 |
| aspect | 1.7778 |
| views | 48 |
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
| aim | (0.0, 20.95, 0.0) |
| field of view | 55.32 deg vertical |
| focal distance | 92.418 |
| near (measured) | 72.0 |
| far (measured, knee) | 129.0 |
| excluded from balance | sea and sky |

## Depth budget

```
  focal plane      92.4 units
  view cone        35.0 deg over 48 views
  eye sweep        +/-29.1 units
  adjacent-view disparity:
    nearest geometry       72.0   2.61 px
    focal plane            92.4   0.00 px
    structured far        129.0   2.61 px
    sea and sky (infinite)      inf   9.22 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 221 s |
| per view | 4.6 s |

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/bell-jar-holo-2026_qs8x6a1.77778.png` |
| Size | 25.0 MB |
| SHA-256 | `fd2cfb1551f8f8944c10fba6214cdf8d8cb26ef02e07971f9a8fa49ea7866a37` |
