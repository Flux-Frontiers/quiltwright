# bdna-go hologram

**Generated:** 2026-09-15 14:05:40  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `0288a28` (feature/playlist-and-go) **+ uncommitted changes**  
**Commit:** 2026-09-15 12:49:58 -0400 -- fix: casts after the first ignored, bridge reset over-matching, uncapped cone (#61)  
**Scene:** `pov-scenes/bell_jar/bdna_go.pov` sha256 `b96c1f35c28e7ddd`  
**Python:** 3.12.13  |  **quiltwright:** 0.10.1  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_still_life_hologram.py bdna-go --device go --view-cone 54 --jobs 16 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | bdna-go |
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
| eye | (0.0, 12.0, -113.0) |
| aim | (0.0, 0.0, 0.0) |
| field of view | 26.0 deg vertical |
| focal distance | 108.118 |
| near (measured) | 101.7 |
| far (measured, knee) | 115.4 |
| excluded from balance | dark gradient |

## Depth budget

```
  focal plane      108.1 units
  view cone        54.0 deg over 66 views
  eye sweep        +/-55.1 units
  adjacent-view disparity:
    nearest geometry      101.7   1.46 px
    focal plane           108.1   0.00 px
    structured far        115.4   1.46 px
    dark gradient (infinite)      inf  23.16 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 8 s |
| per view | 0.1 s |

## Caveat

composed 9:16 for the Looking Glass Go -- pass --device go

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/bdna-go_qs11x6a0.5625.png` |
| Size | 9.1 MB |
| SHA-256 | `938c3b08c68f43a333334d0cf0f6b3b33bad3044ebd27047f9378cf2034e6276` |
