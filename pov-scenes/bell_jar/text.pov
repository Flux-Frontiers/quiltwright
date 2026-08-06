 

  #include "colors.inc"

  #include "stones.inc"



  background { color rgb 1 }



  camera {

    location <-3, 5, -15>

    look_at 0

    angle 45

  }



  light_source { <500,500,-1000> White }



 box { <-5, -1, 0.1>, <5, 1, 1>

    texture { T_Stone10 }

  }

  

 text { ttf "timrom.ttf" "B-DNA Under Glass" 0.1, 0

  pigment { BrightGold }

  finish { reflection .25 specular 1 }

  translate -4.2*x



  }



 text { ttf "timrom.ttf" "E.G. Suchanek, 1996" 0.10, 0

  pigment { BrightGold }

  finish { reflection .25 specular 1 }

  translate <1.0,-1.2,0>

  scale <.5, .5, .5>

    }

   

 difference {

  box { <-5, -1, 0.1>, <5, 1, 1>

      texture { T_Stone10 }

    }

    text { ttf "timrom.ttf" "B-DNA" 0.10, 0

      pigment { BrightGold }

      finish { reflection .25 specular 1 }

      translate -4.2*x

    }

    

  difference {

    box { <3, -2, 0.1>, <5, 0, 1>

      texture { T_Stone10 }

    }

    text { ttf "timrom.ttf" "E.G. Suchanek, 1996" 0.10, 0

      pigment { BrightGold }

      finish { reflection .25 specular 1 }

      translate <1.0, -1.2, 0>

      scale <.5, .5, .5>

    }

  }



}

