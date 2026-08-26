# porin hologram

**Generated:** 2026-08-26 16:51:24  
**Machine:** x86_64  
**Repository:** quiltwright @ `abba706` (main)  
**Commit:** 2026-08-26 16:22:11 +0000 -- docs: bring the README intro past the two-backend era  
**Scene:** `pov-scenes/porin/3porin.pov` sha256 `2c97fadb3306a4e8`  
**Python:** 3.13.12  |  **quiltwright:** 0.9.0  |  **numpy:** 2.5.2  |  **POV-Ray:** povray: cannot open the user configuration file /root/.povray/3.7/povray.conf: No such file or directory  
**Host:** vm  |  **OS:** Linux-6.18.44-fc-v21-x86_64-with-glibc2.39  
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
| CPU cores | 4 |
| POV-Ray processes (--jobs) | 1 |
| threads per process | 2 |
| thread count set by | Work_Threads in /home/user/quiltwright/renders/.threads.ini |
| cores in use | 2 of 4 |

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
| wall clock | 2421 s |
| per view | 50.4 s |

## Output

| Field | Value |
|---|---|
| File | `renders/quilts/porin_qs8x6a1.77778.png` |
| Size | 31.8 MB |
| SHA-256 | `75531b68a9b9900fc67dfe691842315dc4902ef200176596b4a1a976332f53c5` |
