/* $Id: atoms2.inc,v 1.2 1995/09/22 14:53:12 suchanek Exp $ */
/* Object and texture declarations for some stock Atoms. For POV-Ray */

/* Must include:  */
  #include "colors.inc"
  #include "shapes.inc"
  #include "textures.inc"

/* $Log: atoms2.inc,v $
# Revision 1.2  1995/09/22  14:53:12  suchanek
# *** empty log message ***
# */


#declare Atoms_Inc_Temp = version

#version 2.0

#declare Clear_Atom = texture {
   pigment {color red 1.0 green 1.0 blue 1.0 filter 0.95}
   finish {Shiny
    ambient 0.2
    diffuse 0.0
    reflection 0.05
    refraction 1.0
    ior 1.0
   }
}

#declare my_glass_finish = finish {
      ambient 0.1
      diffuse 0.1
      specular 0.8
      reflection 0.1
      refraction 0.9
      ior 1.15
      roughness 0.0003
      phong 1 phong_size 400
}

/* normal atoms */

#declare Atom_H= object {
       sphere {<0.0, 0.0, 0.0> H_RAD }
       texture {
        finish {Shiny }
        pigment {
         color White
         quick_color White
       }
  }
}

#declare Atom_He= object {
       sphere {<0.0, 0.0, 0.0> He_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Orange
         quick_color Orange
       }
  }
}

#declare Atom_Li= object {
       sphere {<0.0, 0.0, 0.0> Li_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Be= object {
       sphere {<0.0, 0.0, 0.0> Be_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Orange
         quick_color Orange
       }
  }
}

#declare Atom_B= object {
       sphere {<0.0, 0.0, 0.0> B_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Orange
         quick_color Orange
       }
  }
}

#declare Atom_C= object {
       sphere {<0.0, 0.0, 0.0> C_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Gray25
         quick_color Gray25
       }
  }
}

#declare Atom_N= object {
       sphere {<0.0, 0.0, 0.0> N_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Blue
         quick_color Blue
       }
  }
}

#declare Atom_O= object {
       sphere {<0.0, 0.0, 0.0> O_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Red
         quick_color Red
       }
  }
}

#declare Atom_F= object {
       sphere {<0.0, 0.0, 0.0> F_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Ne= object {
       sphere {<0.0, 0.0, 0.0> Ne_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Orange
         quick_color Orange
       }
  }
}

#declare Atom_Na= object {
       sphere {<0.0, 0.0, 0.0> Na_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Mg= object {
       sphere {<0.0, 0.0, 0.0> Mg_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Al= object {
       sphere {<0.0, 0.0, 0.0> Al_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Si= object {
       sphere {<0.0, 0.0, 0.0> Si_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Scarlet
         quick_color Scarlet
       }
  }
}

#declare Atom_P= object {
       sphere {<0.0, 0.0, 0.0> P_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Yellow
         quick_color Yellow
       }
  }
}

#declare Atom_S= object {
       sphere {<0.0, 0.0, 0.0> S_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Yellow
         quick_color Yellow
       }
  }
}

#declare Atom_Cl= object {
       sphere {<0.0, 0.0, 0.0> Cl_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Ar= object {
       sphere {<0.0, 0.0, 0.0> Ar_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Orange
         quick_color Orange
       }
  }
}

#declare Atom_K= object {
       sphere {<0.0, 0.0, 0.0> K_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Ca= object {
       sphere {<0.0, 0.0, 0.0> Ca_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Sc= object {
       sphere {<0.0, 0.0, 0.0> Sc_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Scarlet
         quick_color Scarlet
       }
  }
}

#declare Atom_Ti= object {
       sphere {<0.0, 0.0, 0.0> Ti_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_V= object {
       sphere {<0.0, 0.0, 0.0> V_RAD }
       texture {
        finish {Shiny }
        pigment {
         color BlueViolet
         quick_color BlueViolet
       }
  }
}

#declare Atom_Cr= object {
       sphere {<0.0, 0.0, 0.0> Cr_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Mn= object {
       sphere {<0.0, 0.0, 0.0> Mn_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Fe= object {
       sphere {<0.0, 0.0, 0.0> Fe_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Scarlet
         quick_color Scarlet
       }
  }
}

#declare Atom_Co= object {
       sphere {<0.0, 0.0, 0.0> Co_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ni= object {
       sphere {<0.0, 0.0, 0.0> Ni_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Cu= object {
       sphere {<0.0, 0.0, 0.0> Cu_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Zn= object {
       sphere {<0.0, 0.0, 0.0> Zn_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ga= object {
       sphere {<0.0, 0.0, 0.0> Ga_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ge= object {
       sphere {<0.0, 0.0, 0.0> Ge_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_As= object {
       sphere {<0.0, 0.0, 0.0> As_RAD }
       texture {
        finish {Shiny }
        pigment {
         color PaleGreen
         quick_color PaleGreen
       }
  }
}

#declare Atom_Se= object {
       sphere {<0.0, 0.0, 0.0> Se_RAD }
       texture {
        finish {Shiny }
        pigment {
         color SpringGreen
         quick_color SpringGreen
       }
  }
}

#declare Atom_Br= object {
       sphere {<0.0, 0.0, 0.0> Br_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Green
         quick_color Green
       }
  }
}

#declare Atom_Kr= object {
       sphere {<0.0, 0.0, 0.0> Kr_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Orange
         quick_color Orange
       }
  }
}

#declare Atom_Rb= object {
       sphere {<0.0, 0.0, 0.0> Rb_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Sr= object {
       sphere {<0.0, 0.0, 0.0> Sr_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Y= object {
       sphere {<0.0, 0.0, 0.0> Y_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Yellow
         quick_color Yellow
       }
  }
}

#declare Atom_Zr= object {
       sphere {<0.0, 0.0, 0.0> Zr_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Nb= object {
       sphere {<0.0, 0.0, 0.0> Nb_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Mo= object {
       sphere {<0.0, 0.0, 0.0> Mo_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Tc= object {
       sphere {<0.0, 0.0, 0.0> Tc_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ru= object {
       sphere {<0.0, 0.0, 0.0> Ru_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Rh= object {
       sphere {<0.0, 0.0, 0.0> Rh_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Pd= object {
       sphere {<0.0, 0.0, 0.0> Pd_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ag= object {
       sphere {<0.0, 0.0, 0.0> Ag_RAD }
       texture {Silver_Texture}
}

#declare Atom_Cd= object {
       sphere {<0.0, 0.0, 0.0> Cd_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_In= object {
       sphere {<0.0, 0.0, 0.0> In_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Sn= object {
       sphere {<0.0, 0.0, 0.0> Sn_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Sb= object {
       sphere {<0.0, 0.0, 0.0> Sb_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Te= object {
       sphere {<0.0, 0.0, 0.0> Te_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_I= object {
       sphere {<0.0, 0.0, 0.0> I_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Xe= object {
       sphere {<0.0, 0.0, 0.0> Xe_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Cs= object {
       sphere {<0.0, 0.0, 0.0> Cs_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ba= object {
       sphere {<0.0, 0.0, 0.0> Ba_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_La= object {
       sphere {<0.0, 0.0, 0.0> La_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ce= object {
       sphere {<0.0, 0.0, 0.0> Ce_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Pr= object {
       sphere {<0.0, 0.0, 0.0> Pr_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Nd= object {
       sphere {<0.0, 0.0, 0.0> Nd_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Pm= object {
       sphere {<0.0, 0.0, 0.0> Pm_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Sm= object {
       sphere {<0.0, 0.0, 0.0> Sm_RAD }
       texture {
        finish {Shiny }
        pigment {
         color DarkGreen
         quick_color DarkGreen
       }
  }
}

#declare Atom_Eu= object {
       sphere {<0.0, 0.0, 0.0> Eu_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Gd= object {
       sphere {<0.0, 0.0, 0.0> Gd_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Tb= object {
       sphere {<0.0, 0.0, 0.0> Tb_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Dy= object {
       sphere {<0.0, 0.0, 0.0> Dy_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ho= object {
       sphere {<0.0, 0.0, 0.0> Ho_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Er= object {
       sphere {<0.0, 0.0, 0.0> Er_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Tm= object {
       sphere {<0.0, 0.0, 0.0> Tm_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Yb= object {
       sphere {<0.0, 0.0, 0.0> Yb_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Maroon
         quick_color Maroon
       }
  }
}

#declare Atom_Lu= object {
       sphere {<0.0, 0.0, 0.0> Lu_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Hf= object {
       sphere {<0.0, 0.0, 0.0> Hf_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ta= object {
       sphere {<0.0, 0.0, 0.0> Ta_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Wb= object {
       sphere {<0.0, 0.0, 0.0> Wb_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Re= object {
       sphere {<0.0, 0.0, 0.0> Re_RAD }
       texture {
        finish {Shiny }
        pigment {
         color Red
         quick_color Red
       }
  }
}

#declare Atom_Os= object {
       sphere {<0.0, 0.0, 0.0> Os_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ir= object {
       sphere {<0.0, 0.0, 0.0> Ir_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Pt= object {
       sphere {<0.0, 0.0, 0.0> Pt_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Au= object {
       sphere {<0.0, 0.0, 0.0> Au_RAD }
       texture {Gold_Texture}
}

#declare Atom_Hg= object {
       sphere {<0.0, 0.0, 0.0> Hg_RAD }
       texture {Brass_Texture}
}

#declare Atom_Tl= object {
       sphere {<0.0, 0.0, 0.0> Tl_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Pb= object {
       sphere {<0.0, 0.0, 0.0> Pb_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Bi= object {
       sphere {<0.0, 0.0, 0.0> Bi_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Po= object {
       sphere {<0.0, 0.0, 0.0> Po_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_At= object {
       sphere {<0.0, 0.0, 0.0> At_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Rn= object {
       sphere {<0.0, 0.0, 0.0> Rn_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Fr= object {
       sphere {<0.0, 0.0, 0.0> Fr_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ra= object {
       sphere {<0.0, 0.0, 0.0> Ra_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Ac= object {
       sphere {<0.0, 0.0, 0.0> Ac_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Th= object {
       sphere {<0.0, 0.0, 0.0> Th_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Pa= object {
       sphere {<0.0, 0.0, 0.0> Pa_RAD }
       texture {
        finish {Shiny }
        pigment {
         color PaleGreen
         quick_color PaleGreen
       }
  }
}

#declare Atom_U= object {
       sphere {<0.0, 0.0, 0.0> U_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Np= object {
       sphere {<0.0, 0.0, 0.0> Np_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Pu= object {
       sphere {<0.0, 0.0, 0.0> Pu_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Am= object {
       sphere {<0.0, 0.0, 0.0> Am_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Cm= object {
       sphere {<0.0, 0.0, 0.0> Cm_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Bk= object {
       sphere {<0.0, 0.0, 0.0> Bk_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Cf= object {
       sphere {<0.0, 0.0, 0.0> Cf_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Es= object {
       sphere {<0.0, 0.0, 0.0> Es_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Fm= object {
       sphere {<0.0, 0.0, 0.0> Fm_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Md= object {
       sphere {<0.0, 0.0, 0.0> Md_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_No= object {
       sphere {<0.0, 0.0, 0.0> No_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Lr= object {
       sphere {<0.0, 0.0, 0.0> Lr_RAD }
       texture {
        finish {Shiny }
        pigment {
         color MidnightBlue
         quick_color MidnightBlue
       }
  }
}
/* clear atoms */



#declare Atom_Glass_H= object {
       sphere {<0.0, 0.0, 0.0> H_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color White filter 0.95
         quick_color White
       }
  }
}

#declare Atom_Glass_He= object {
       sphere {<0.0, 0.0, 0.0> He_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Orange filter 0.95
         quick_color Orange
       }
  }
}

#declare Atom_Glass_Li= object {
       sphere {<0.0, 0.0, 0.0> Li_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Be= object {
       sphere {<0.0, 0.0, 0.0> Be_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Orange filter 0.95
         quick_color Orange
       }
  }
}

#declare Atom_Glass_B= object {
       sphere {<0.0, 0.0, 0.0> B_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Orange filter 0.95
         quick_color Orange
       }
  }
}

#declare Atom_Glass_C= object {
       sphere {<0.0, 0.0, 0.0> C_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_N= object {
       sphere {<0.0, 0.0, 0.0> N_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Blue filter 0.95
         quick_color Blue
       }
  }
}

#declare Atom_Glass_O= object {
       sphere {<0.0, 0.0, 0.0> O_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Red filter 0.95
         quick_color Red
       }
  }
}

#declare Atom_Glass_F= object {
       sphere {<0.0, 0.0, 0.0> F_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Ne= object {
       sphere {<0.0, 0.0, 0.0> Ne_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Orange filter 0.95
         quick_color Orange
       }
  }
}

#declare Atom_Glass_Na= object {
       sphere {<0.0, 0.0, 0.0> Na_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Mg= object {
       sphere {<0.0, 0.0, 0.0> Mg_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Al= object {
       sphere {<0.0, 0.0, 0.0> Al_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Si= object {
       sphere {<0.0, 0.0, 0.0> Si_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Scarlet filter 0.95
         quick_color Scarlet
       }
  }
}

#declare Atom_Glass_P= object {
       sphere {<0.0, 0.0, 0.0> P_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Yellow filter 0.95
         quick_color Yellow
       }
  }
}

#declare Atom_Glass_S= object {
       sphere {<0.0, 0.0, 0.0> S_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Yellow filter 0.95
         quick_color Yellow
       }
  }
}

#declare Atom_Glass_Cl= object {
       sphere {<0.0, 0.0, 0.0> Cl_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Ar= object {
       sphere {<0.0, 0.0, 0.0> Ar_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Orange filter 0.95
         quick_color Orange
       }
  }
}

#declare Atom_Glass_K= object {
       sphere {<0.0, 0.0, 0.0> K_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Ca= object {
       sphere {<0.0, 0.0, 0.0> Ca_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Sc= object {
       sphere {<0.0, 0.0, 0.0> Sc_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Scarlet filter 0.95
         quick_color Scarlet
       }
  }
}

#declare Atom_Glass_Ti= object {
       sphere {<0.0, 0.0, 0.0> Ti_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_V= object {
       sphere {<0.0, 0.0, 0.0> V_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color BlueViolet filter 0.95
         quick_color BlueViolet
       }
  }
}

#declare Atom_Glass_Cr= object {
       sphere {<0.0, 0.0, 0.0> Cr_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Mn= object {
       sphere {<0.0, 0.0, 0.0> Mn_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Fe= object {
       sphere {<0.0, 0.0, 0.0> Fe_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Scarlet filter 0.95
         quick_color Scarlet
       }
  }
}

#declare Atom_Glass_Co= object {
       sphere {<0.0, 0.0, 0.0> Co_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ni= object {
       sphere {<0.0, 0.0, 0.0> Ni_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Cu= object {
       sphere {<0.0, 0.0, 0.0> Cu_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Zn= object {
       sphere {<0.0, 0.0, 0.0> Zn_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ga= object {
       sphere {<0.0, 0.0, 0.0> Ga_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ge= object {
       sphere {<0.0, 0.0, 0.0> Ge_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_As= object {
       sphere {<0.0, 0.0, 0.0> As_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color PaleGreen filter 0.95
         quick_color PaleGreen
       }
  }
}

#declare Atom_Glass_Se= object {
       sphere {<0.0, 0.0, 0.0> Se_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color SpringGreen filter 0.95
         quick_color SpringGreen
       }
  }
}

#declare Atom_Glass_Br= object {
       sphere {<0.0, 0.0, 0.0> Br_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Green filter 0.95
         quick_color Green
       }
  }
}

#declare Atom_Glass_Kr= object {
       sphere {<0.0, 0.0, 0.0> Kr_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Orange filter 0.95
         quick_color Orange
       }
  }
}

#declare Atom_Glass_Rb= object {
       sphere {<0.0, 0.0, 0.0> Rb_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Sr= object {
       sphere {<0.0, 0.0, 0.0> Sr_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Y= object {
       sphere {<0.0, 0.0, 0.0> Y_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Yellow filter 0.95
         quick_color Yellow
       }
  }
}

#declare Atom_Glass_Zr= object {
       sphere {<0.0, 0.0, 0.0> Zr_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Nb= object {
       sphere {<0.0, 0.0, 0.0> Nb_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Mo= object {
       sphere {<0.0, 0.0, 0.0> Mo_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Tc= object {
       sphere {<0.0, 0.0, 0.0> Tc_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ru= object {
       sphere {<0.0, 0.0, 0.0> Ru_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Rh= object {
       sphere {<0.0, 0.0, 0.0> Rh_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Pd= object {
       sphere {<0.0, 0.0, 0.0> Pd_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ag= object {
       sphere {<0.0, 0.0, 0.0> Ag_RAD }
       texture {Silver_Texture}
}

#declare Atom_Glass_Cd= object {
       sphere {<0.0, 0.0, 0.0> Cd_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_In= object {
       sphere {<0.0, 0.0, 0.0> In_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Sn= object {
       sphere {<0.0, 0.0, 0.0> Sn_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Sb= object {
       sphere {<0.0, 0.0, 0.0> Sb_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Te= object {
       sphere {<0.0, 0.0, 0.0> Te_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_I= object {
       sphere {<0.0, 0.0, 0.0> I_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Xe= object {
       sphere {<0.0, 0.0, 0.0> Xe_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Cs= object {
       sphere {<0.0, 0.0, 0.0> Cs_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ba= object {
       sphere {<0.0, 0.0, 0.0> Ba_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_La= object {
       sphere {<0.0, 0.0, 0.0> La_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ce= object {
       sphere {<0.0, 0.0, 0.0> Ce_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Pr= object {
       sphere {<0.0, 0.0, 0.0> Pr_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Nd= object {
       sphere {<0.0, 0.0, 0.0> Nd_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Pm= object {
       sphere {<0.0, 0.0, 0.0> Pm_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Sm= object {
       sphere {<0.0, 0.0, 0.0> Sm_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color DarkGreen filter 0.95
         quick_color DarkGreen
       }
  }
}

#declare Atom_Glass_Eu= object {
       sphere {<0.0, 0.0, 0.0> Eu_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Gd= object {
       sphere {<0.0, 0.0, 0.0> Gd_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Tb= object {
       sphere {<0.0, 0.0, 0.0> Tb_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Dy= object {
       sphere {<0.0, 0.0, 0.0> Dy_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ho= object {
       sphere {<0.0, 0.0, 0.0> Ho_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Er= object {
       sphere {<0.0, 0.0, 0.0> Er_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Tm= object {
       sphere {<0.0, 0.0, 0.0> Tm_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Yb= object {
       sphere {<0.0, 0.0, 0.0> Yb_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Maroon filter 0.95
         quick_color Maroon
       }
  }
}

#declare Atom_Glass_Lu= object {
       sphere {<0.0, 0.0, 0.0> Lu_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Hf= object {
       sphere {<0.0, 0.0, 0.0> Hf_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ta= object {
       sphere {<0.0, 0.0, 0.0> Ta_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Wb= object {
       sphere {<0.0, 0.0, 0.0> Wb_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Re= object {
       sphere {<0.0, 0.0, 0.0> Re_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color Red filter 0.95
         quick_color Red
       }
  }
}

#declare Atom_Glass_Os= object {
       sphere {<0.0, 0.0, 0.0> Os_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ir= object {
       sphere {<0.0, 0.0, 0.0> Ir_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Pt= object {
       sphere {<0.0, 0.0, 0.0> Pt_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Au= object {
       sphere {<0.0, 0.0, 0.0> Au_RAD }
       texture {Gold_Texture}
}

#declare Atom_Glass_Hg= object {
       sphere {<0.0, 0.0, 0.0> Hg_RAD }
       texture {Brass_Texture}
}

#declare Atom_Glass_Tl= object {
       sphere {<0.0, 0.0, 0.0> Tl_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Pb= object {
       sphere {<0.0, 0.0, 0.0> Pb_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Bi= object {
       sphere {<0.0, 0.0, 0.0> Bi_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Po= object {
       sphere {<0.0, 0.0, 0.0> Po_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_At= object {
       sphere {<0.0, 0.0, 0.0> At_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Rn= object {
       sphere {<0.0, 0.0, 0.0> Rn_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Fr= object {
       sphere {<0.0, 0.0, 0.0> Fr_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ra= object {
       sphere {<0.0, 0.0, 0.0> Ra_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Ac= object {
       sphere {<0.0, 0.0, 0.0> Ac_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Th= object {
       sphere {<0.0, 0.0, 0.0> Th_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Pa= object {
       sphere {<0.0, 0.0, 0.0> Pa_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color PaleGreen filter 0.95
         quick_color PaleGreen
       }
  }
}

#declare Atom_Glass_U= object {
       sphere {<0.0, 0.0, 0.0> U_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Np= object {
       sphere {<0.0, 0.0, 0.0> Np_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Pu= object {
       sphere {<0.0, 0.0, 0.0> Pu_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Am= object {
       sphere {<0.0, 0.0, 0.0> Am_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Cm= object {
       sphere {<0.0, 0.0, 0.0> Cm_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Bk= object {
       sphere {<0.0, 0.0, 0.0> Bk_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Cf= object {
       sphere {<0.0, 0.0, 0.0> Cf_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Es= object {
       sphere {<0.0, 0.0, 0.0> Es_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Fm= object {
       sphere {<0.0, 0.0, 0.0> Fm_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Md= object {
       sphere {<0.0, 0.0, 0.0> Md_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_No= object {
       sphere {<0.0, 0.0, 0.0> No_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}

#declare Atom_Glass_Lr= object {
       sphere {<0.0, 0.0, 0.0> Lr_RAD }
       texture {
        finish {my_glass_finish }
        pigment {
         color MidnightBlue filter 0.95
         quick_color MidnightBlue
       }
  }
}
/* the bond */

#declare White_Bond = texture 
{
  finish {Shiny }
  pigment {
           color VLightGrey filter 0.95
           quick_color VLightGrey
          }
}

#version Atoms_Inc_Temp
