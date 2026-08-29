# Museum hologram

**Generated:** 2026-08-26 18:03:11  
**Machine:** x86_64  
**Repository:** quiltwright @ `f029e32` (main)  
**Commit:** 2026-08-26 17:17:28 +0000 -- chore(renders): bell jar landscape quilt run report  
**Scene:** `pov-scenes/museum/museum.pov` sha256 `e7c8814c2b2e1eff`  
**Python:** 3.13.12  |  **quiltwright:** 0.9.0  |  **numpy:** 2.5.2  |  **POV-Ray:** POV-Ray 3.7.0.10.unofficial  
**Host:** vm  |  **OS:** Linux-6.18.44-fc-v21-x86_64-with-glibc2.39  
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
| CPU cores | 4 |
| POV-Ray processes (--jobs) | 1 |
| threads per process | 4 |
| thread count set by | Work_Threads in /home/user/quiltwright/renders/.threads.ini |
| cores in use | 4 of 4 |

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
| wall clock | 2777 s |
| per view | 57.9 s |

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/museum_qs8x6a1.77778.png` |
| Size | 40.9 MB |
| SHA-256 | `e50bb25641e6e29f4399cf430dcc88f02b99c0a11634b982cd99340dc0a0f1a8` |
