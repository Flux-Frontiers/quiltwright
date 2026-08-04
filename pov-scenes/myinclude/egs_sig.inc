//
// my signature
//

#declare egstext = object {
 text
 {
  ttf                       // font type (only TrueType format for now)
  "timrom.ttf",             // Microsoft Windows-format TrueType font file name
  "E. G. Suchanek, '97",   // the string to create
  .25,                     // the extrusion depth
  0                        // offset
   pigment { BrightGold }
  finish { reflection .25 specular 1 ambient .3 }
 }
}
