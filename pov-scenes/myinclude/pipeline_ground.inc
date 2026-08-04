#if (DO_GROUND = true)
plane { y, -15
    pigment { Sapphire_Agate  scale 10.0}
    finish { reflection .35 specular 1 }
    normal { ripples .5 turbulence .5 scale 15 }
/*
     finish {
       ambient 0.2
       diffuse 0.8
     }
*/
 }
#end // if do_ground
