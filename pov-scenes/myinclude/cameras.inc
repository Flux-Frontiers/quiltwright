#declare camera_main = camera {
   location < 2, 0, -45 >
   right <ASPECT, 0, 0>
   look_at <0, 0, 0>
}

#declare camera_close = camera {
location < 0, 6, -30 >
   right <ASPECT, 0, 0>
   look_at <0, 0, 0>
   // angle 50
}

#declare camera_ne11040 = camera {
location < 0, 6, -30 >
   right <ASPECT, 0, 0>
   look_at <-0, 0, 0>
   // angle 60
}

#declare camera_pg117117 = camera {
location < 0, 6, -20 >
   right <ASPECT, 0, 0>
   look_at <-0, 0, 0>
   // angle 60
}

#declare camera_top = camera {
   location < 0, 60, -.1 >
   right <ASPECT, 0, 0>
   look_at <0, 0, 0>
}
