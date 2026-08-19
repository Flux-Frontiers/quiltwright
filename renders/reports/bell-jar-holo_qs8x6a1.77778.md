# bell-jar-holo hologram

**Generated:** 2026-08-18 19:28:26  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `52fc5b9` (main) **+ uncommitted changes**  
**Commit:** 2026-08-18 19:08:02 -0400 -- feat(bell_jar): light-field cuts of the DNA still life  
**Scene:** `pov-scenes/bell_jar/bj_holo.pov` sha256 `78622c509b68a431`  
**Python:** 3.12.13  |  **quiltwright:** 0.6.0  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_still_life_hologram.py bell-jar-holo --jobs 1 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | bell-jar-holo |
| device | 16-landscape |
| quilt | 7680x4320 |
| tile | 960x720 |
| aspect | 1.7778 |
| views | 48 |
| view cone | 35.0 deg |
| anti-aliasing | +A0.05 +AM2 +R4 |
| POV-Ray quality | +Q11 |
| concurrent processes | 1 |

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
| wall clock | 280 s |
| per view | 5.8 s |

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/bell-jar-holo_qs8x6a1.77778.png` |
| Size | 24.6 MB |
| SHA-256 | `e6a0f386a742bf145caf2dbe81462c3ed1e510b0db25d8ba70a7b4c46c26c926` |
