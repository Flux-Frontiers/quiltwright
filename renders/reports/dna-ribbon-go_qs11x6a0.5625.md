# dna-ribbon-go hologram

**Generated:** 2026-09-15 14:15:45  
**Machine:** Apple M5 Max, 64 GB RAM  
**Repository:** quiltwright @ `0288a28` (feature/playlist-and-go) **+ uncommitted changes**  
**Commit:** 2026-09-15 12:49:58 -0400 -- fix: casts after the first ignored, bridge reset over-matching, uncapped cone (#61)  
**Scene:** `pov-scenes/museum/dna_ribbon_go.pov` sha256 `1f05f46909e61057`  
**Python:** 3.12.13  |  **quiltwright:** 0.10.1  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** turing  |  **OS:** macOS-27.0-arm64-arm-64bit  
**Command:** `scripts/render_still_life_hologram.py dna-ribbon-go --device go --view-cone 54 --jobs 16 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | dna-ribbon-go |
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
| eye | (0.0, 8.0, -95.0) |
| aim | (0.0, 0.0, 0.0) |
| field of view | 26.0 deg vertical |
| focal distance | 93.996 |
| near (measured) | 86.3 |
| far (measured, knee) | 103.2 |
| excluded from balance | dark gradient |

## Depth budget

```
  focal plane      94.0 units
  view cone        54.0 deg over 66 views
  eye sweep        +/-47.9 units
  adjacent-view disparity:
    nearest geometry       86.3   2.07 px
    focal plane            94.0   0.00 px
    structured far        103.2   2.07 px
    dark gradient (infinite)      inf  23.16 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 12 s |
| per view | 0.2 s |

## Caveat

composed 9:16 for the Looking Glass Go -- pass --device go

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/dna-ribbon-go_qs11x6a0.5625.png` |
| Size | 6.1 MB |
| SHA-256 | `9092097dc700dba682d2c065bc4db2ff990898752577781accc45f38a56c6b45` |
