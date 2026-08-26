# bell-jar hologram

**Generated:** 2026-08-26 17:16:41  
**Machine:** x86_64  
**Repository:** quiltwright @ `14b6d1f` (main)  
**Commit:** 2026-08-26 16:55:11 +0000 -- fix(runreport): record the POV-Ray banner, not a startup warning  
**Scene:** `pov-scenes/bell_jar/bj.pov` sha256 `c844ab880784cc66`  
**Python:** 3.13.12  |  **quiltwright:** 0.9.0  |  **numpy:** 2.5.2  |  **POV-Ray:** povray: cannot open the user configuration file /root/.povray/3.7/povray.conf: No such file or directory  
**Host:** vm  |  **OS:** Linux-6.18.44-fc-v21-x86_64-with-glibc2.39  
**Command:** `scripts/render_still_life_hologram.py bell-jar --jobs 1 --report`

---

## Run configuration

| Parameter | Value |
|---|---|
| subject | bell-jar |
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
| CPU cores | 4 |
| POV-Ray processes (--jobs) | 1 |
| threads per process | 4 |
| thread count set by | Work_Threads in /home/user/quiltwright/renders/.threads.ini |
| cores in use | 4 of 4 |

## Camera

| Parameter | Value |
|---|---|
| eye | (0.0, 35.0, -95.0) |
| aim | (0.0, 18.0, 0.0) |
| field of view | 53.13 deg vertical |
| focal distance | 92.673 |
| near (measured) | 72.0 |
| far (measured, knee) | 130.0 |
| excluded from balance | sea and sky |

## Depth budget

```
  focal plane      92.7 units
  view cone        35.0 deg over 48 views
  eye sweep        +/-29.2 units
  adjacent-view disparity:
    nearest geometry       72.0   2.77 px
    focal plane            92.7   0.00 px
    structured far        130.0   2.77 px
    sea and sky (infinite)      inf   9.66 px  <- soft
```

## Timing

| Parameter | Value |
|---|---|
| wall clock | 1474 s |
| per view | 30.7 s |

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/bell-jar_qs8x6a1.77778.png` |
| Size | 25.2 MB |
| SHA-256 | `af272aec4b7ff2010b4e5838b887e869c7cc7dfbc5a3b69594ba0bc64dda0a70` |
