# porin hologram

**Generated:** 2026-08-31 23:25:49  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `9c6c3cf` (main) **+ uncommitted changes**  
**Commit:** 2026-08-31 23:16:53 -0400 -- chore: drop quiltwright_analysis_after_p1_p2.md from analysis/  
**Scene:** `pov-scenes/porin/3porin.pov` sha256 `2c97fadb3306a4e8`  
**Python:** 3.12.13  |  **quiltwright:** 0.10.1  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_still_life_hologram.py porin --jobs 1 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | porin |
| device | 16-landscape |
| quilt | 7680x4320 |
| tile | 960x720 |
| aspect | 1.7778 |
| views | 48 |
| view cone | 35.0 deg |
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
  view cone        35.0 deg over 48 views
  eye sweep        +/-306.7 units
  adjacent-view disparity:
    nearest geometry      790.0   2.23 px
    focal plane           972.6   0.00 px
    structured far       1265.0   2.23 px
    sea and sky (infinite)      inf   9.66 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 189 s |
| per view | 3.9 s |

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/porin_qs8x6a1.77778.png` |
| Size | 31.2 MB |
| SHA-256 | `b256129dc29d2e353e78105de660bf84ce1dfa63892a843a2877b9469f718ce4` |
