// corner columns - Meek Museum
//
// 23 Feb 94 - Michael Mittelstadt
//

#declare co_1 =
union { cylinder { <0,8,0>,<0,56,0>,1 }
        sphere { <0,8,0>,1 }
        sphere { <0,56,0>,1 }
//        bounded_by { box { <-1.05,7.95,-1.05>,<1.05,56.05,1.05> }}
 }

#include "stones.inc"

#declare column=
union {
  cylinder { <0,0,0>,<0,1,0>,6 }
  cylinder { <0,1,0>,<0,3,0>,5 }
  cylinder { <0,3,0>,<0,4,0>,4.66 }
  difference {
    cylinder { <0,4,0>,<0,60,0>,4 }
    object { co_1 translate 4*x rotate 0*y }
    object { co_1 translate 4*x rotate 45*y }
    object { co_1 translate 4*x rotate 90*y }
    object { co_1 translate 4*x rotate 135*y }
    }
  texture { T_Stone7 }
  }



