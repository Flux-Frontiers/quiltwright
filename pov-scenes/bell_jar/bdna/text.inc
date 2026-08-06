#declare Text_Inc_Temp = version
#version 1.0


  #include "colors.inc"
  #include "stones.inc"
  #include "marble2.inc"


#declare title_stone = union {
 box { <-5, -1, 0.1>, <5, 1, 1>
    texture { marble1 }
  }

  

 text { ttf "timrom.ttf" "B-DNA Under Glass" 0.1, 0
  pigment { BrightGold }
  finish { reflection .25 specular 1 }
  translate <-4.2, 0, 0>

  }



 text { ttf "timrom.ttf" "E.G. Suchanek, 1996" 0.10, 0
  pigment { BrightGold }
  finish { reflection .25 specular 1 }
  translate <1.0,-1.2,0>
  scale <.5, .5, .5>
 }

   

 difference {
  box { <-5, -1, 0.1>, <5, 1, 1>
      texture { marble1 }
    }
    text { ttf "timrom.ttf" "B-DNA" 0.10, 0
      pigment { BrightGold }
      finish { reflection .25 specular 1 }
      translate <-4.2, 0.0, 0.0>
    }

    

  difference {
    box { <3, -2, 0.1>, <5, 0, 1>
      texture { marble1 }
    }

    text { ttf "timrom.ttf" "E.G. Suchanek, 1996" 0.10, 0
      pigment { BrightGold }
      finish { reflection .25 specular 1 }
      translate <1.0, -1.2, 0>
      scale <.5, .5, .5>
    }
  }

 }
}



#version Text_Inc_Temp

