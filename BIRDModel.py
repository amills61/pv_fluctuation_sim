#!/usr/bin/python

"""
Bird Clear Sky Model: Developed from Excel Spreadsheet implementation of 
Daryl Myers:  http://rredc.nrel.gov/solar/models/clearsky/

Bird, R. E., and R. L. Hulstrom, Simplified Clear Sky Model for Direct and 
Diffuse Insolation on Horizontal Surfaces, Technical Report No. SERI/TR-642-761, 
Golden, CO: Solar Energy Research Institute, 1981

For questions on original Excel model, contact: 
Daryl R. Myers
National Renewable Energy Laboratory
1617 Cole Blvd. MS 3411
Golden CO 80401
(303)-384-6768 e-mail daryl_myers@nrel.gov

For questions on python module based on Excel:
Andrew Mills
Lawrence Berkeley National Laboratory
(510) 486-4059
ADMills@lbl.gov
"""

import numpy as np 
import pdb

def clearsky(doy, hr, minute, params):
    """
    clearsky()
    Returns the direct normal (idn), global horizontal (ghz)
    and diffuse horizontal (difhz) insolation for clear sky conditions 
    using the Bird model
    
    Inputs are: 
    Day of year (local standard time) - doy [vector]
    Hour of day (local standard time) - hr  [vector]
    Minute of the hour - minute (0-59)      [vector]
    Latitude of site  - lat
    Longitude of site - lon
    Time zone offset to GMT - GMTOffset
    Pressure at staion (mB) - press
    Total column ozone thickness in cm (0.3 cm default) - ozone
    Total column water vapor in cm (1.5 cm default) - water
    Aerosol Optical Depth at 0.380 um (380 nm) (default 0.15 ) - aod380
    Aerosol Optical Depth at 0.500 um (500 nm) (default 0.1 ) - aod500
    Forward scattering parameter, Bird recommends 0.85 for rural - ba
    Ground reflectance (defalut 0.2) - albedo
    """
    #### Unpack the singe value parameters 
    lat, lon, GMTOffset, press, ozone, water, aod380, aod500, ba, albedo = params

    hr = hr + minute/60.
    
    etr = ETR(doy)
    dangle = DANGLE(doy)

    decl = DECL(dangle)
    eqt = EQT(dangle)

    hangle = HANGLE(GMTOffset, lon, eqt, hr)
    
    zangle = ZANGLE(decl,lat, hangle)

    am = AM(zangle)
    
    taua = TAUA(aod380, aod500)
    taerosol = TAEROSOL(am,taua)
    twater = TWATER(am, water)
    tgases = TGASES(am, press)
    trayliegh = TRAYLIEGH(am, press)
    tozone = TOZONE(am, ozone)

    idn = IDN(am, etr, taerosol, twater, tgases, tozone, trayliegh)

    idhz = IDHZ(idn, zangle)
    
    taa = TAA(am, taerosol)
    ias = IAS(am, zangle, etr, tozone,tgases, twater,taa, trayliegh, ba, taerosol)

    rs = RS(am, taerosol, ba, taa)

    ghz = GHZ(am, idhz, ias, albedo, rs)

    difhz = DIFHZ(ghz, idhz)


    return idn, ghz, difhz
#--------------------
#--------------------
#--------------------

def ETR(doy):
    """
    ETR(doy)
    Extraterrestrial Direct Beam intensity, W/m2,
    corrected for earth-sun distance variations, for DOY (day of year)
    """
    
    etr = 1367.*(1.00011+0.034221*np.cos(2.*np.pi*(doy-1.)/365.)+0.00128*np.sin(2.*np.pi*(doy-1.)/365.)+0.000719*np.cos(2.*(2.*np.pi*(doy-1.)/365.))+0.000077*np.sin(2.*(2.*np.pi*(doy-1)/365.)))

    return etr
#-----------------

def DANGLE(doy):
    """
    DANGLE(doy) (radians)
    Day Angle; representing position of Earth in orbit around the sun
    for the DOY (day of year) 
    """
    dangle = 6.283185*(doy-1.)/365.
    return dangle
#-----------------

def DECL(dangle):
    """
    DECL(dangle)
    Solar Declination as a fucntion of day angle (radians)
    """
    decl = (0.006918-0.399912*np.cos(dangle)+0.070257*np.sin(dangle)-0.006758*np.cos(2.*dangle)+0.000907*np.sin(2.*dangle)-0.002697*np.cos(3.*dangle)+0.00148*np.sin(3.*dangle))*(180/3.14159)

    return decl
#-----------------

def EQT(dangle):
    """
    EQT(dangle)
    Equation of Time for the sun based on day angle
    """
    eqt = (0.0000075+0.001868*np.cos(dangle)-0.032077*np.sin(dangle)-0.014615*np.cos(2.*dangle)-0.040849*np.sin(2.*dangle))*(229.18)
    
    return eqt
#-----------------

def HANGLE(GMTOffset, lon, eqt, hr):
    """
    HANGLE(GMTOffset, lon, eqt, hr)
    Hour angle of the sun with respect to 0= azimuth of 180 degrees 
    based on GMTOffset (<0 for west), Lon (<0 for west), EQT, and hour of day (HB local standard time)

    """
    #hangle = 15.*(hr-12.5)+(lon)-(GMTOffset)*15.+eqt/4

    #### IN ORDER TO ACCEPT DECIMAL HOURS, GET RID OF 30 MIN OFFSET
    hangle = 15.*(hr-12)+(lon)-(GMTOffset)*15.+eqt/4.

    return hangle

#------------------

def ZANGLE(decl,lat, hangle):
    """
    ZANGLE(decl,lat, hangle)
    Zenith angle of Sun, complement of solar elevation
    as a function of solar declination, latitude, and hour angle
    """

    zangle = np.arccos(np.cos(decl/(180/3.14159))*np.cos(lat/(180/3.14159))*np.cos(hangle/(180/3.14159))+np.sin(decl/(180/3.14159))*np.sin(lat/(180/3.14159)))*(180/3.14159)
    
    return zangle
#--------------------

def AM(zangle):
    """
    AM(zangle)
    GEOMETRICAL Air Mass = 1/np.cos(zenith), 
    NOT CORRECTED FOR SITE PRESSURE
    represents the relative path length through the atmosphere. 
    AM 1.0=> sun overhead at seas level
    """
    am = np.zeros(zangle.shape)
    mask = zangle < 89
    am[mask] = 1./(np.cos(zangle[mask]/(180/3.14159))+0.15/(93.885-zangle[mask])**1.25)

    #if zangle < 89:
    #    am = 1/(np.cos(zangle/(180/3.14159))+0.15/(93.885-zangle)**1.25)
    #else:
    #    am = 0

    return am
#---------------------

def TRAYLIEGH(am, press):
    """
    TRAYLIEGH(am, press)
    am is geometric air mass
    press is station pressure in millibar (840 mB default)
    """
    trayliegh = np.zeros(am.shape)
    mask = am > 0
    trayliegh[mask] = np.exp(-0.0903*(press*am[mask]/1013.)**0.84*(1.+press*am[mask]/1013.-(press*am[mask]/1013.)**1.01))
 
#    if am > 0:
#        trayliegh = np.exp(-0.0903*(press*am/1013.)**0.84*(1+press*am/1013.-(press*am/1013.)**1.01))
#    else:
#        trayliegh = 0;

    return trayliegh
#---------------------

def TOZONE(am, ozone):
    """
    TOZONE(am, ozone)
    am is geometric air mass
    ozone is total column ozone thickness in cm (0.3 cm default)
    """
    tozone = np.zeros(am.shape)
    mask = am > 0
    tozone[mask] = 1-0.1611*(ozone*am[mask])*(1+139.48*(ozone*am[mask]))**-0.3034-0.002715*(ozone*am[mask])/(1+0.044*(ozone*am[mask])+0.0003*(ozone*am[mask])**2)

#    if am > 0:
#        tozone = 1-0.1611*(ozone*am)*(1+139.48*(ozone*am))**-0.3034-0.002715*(ozone*am)/(1+0.044*(ozone*am)+0.0003*(ozone*am)**2)
#    else:
#        tozone = 0

    return tozone
#---------------------

def TGASES(am, press):
    """
    TGASES(am, press)
    am is geometric air mass
    press is station pressure in millibar (840 mB default)
    """
    tgases = np.zeros(am.shape)
    mask = am > 0
    tgases[ mask] = np.exp(-0.0127*(am[mask]*press/1013.)**0.26)

    # if am > 0:
    #     tgases = exp(-0.0127*(am*press/1013.)**0.26)
    # else:
    #     tgases = 0

    return tgases
#---------------------

def TWATER(am, water):
    """
    TWATER(am, water)
    am is geometric air mass
    water is total column water vapor in cm (1.5 cm default)  
    """
    twater = np.zeros(am.shape)
    mask = am > 0
    twater[ mask ] = 1-2.4959*am[mask]*water/((1+79.034*water*am[mask])**0.6828+6.385*water*am[mask])

    # if am > 0:
    #     twater = 1-2.4959*am*water/((1+79.034*water*am)**0.6828+6.385*water*am)
    # else:
    #     twater = 0

    return twater
#---------------------

def TAUA(aod380, aod500):
    """
    TAUA(aod380, aod500)
    This is an intermediate computation of the broadband aerosol optical depth.
    Typical values should range from 0.02 to 0.5
    aod380 is the Aerosol Optical Depth at 0.380 um (380 nm). 
    Typical values range from 0.1 to 0.5
    aod500 typical values range from 0.02 to 0.5. 
    Values>0.5 represent clouds and volcanic dust, etc.
    """

    taua = 0.2758*aod380+0.35*aod500

    return taua
#---------------------

def TAEROSOL(am,taua):
    """
    TAEROSOL(am,taua)
    taua is intermediate calculation
    am is geometric air mass
    """

    taerosol = np.zeros(am.shape)
    mask = am > 0
    taerosol[ mask ] = np.exp(-(taua**0.873)*(1+taua-taua**0.7088)*am[mask]**0.9108)

    # if am > 0:
    #     taerosol = exp(-(taua**0.873)*(1+taua-taua**0.7088)*am**0.9108)
    # else:
    #     taerosol = 0

    return taerosol
#---------------------

def TAA(am, taerosol):
    """
    TAA(am)
    intermediate result based on am - geometric air mass
    and taerosol
    """

    taa = np.zeros(am.shape)
    mask = am > 0
    taa[ mask ] = 1.-0.1*(1.-am[mask] + am[mask]**1.06)*(1.-taerosol[mask])

    # if am > 0:
    #     taa = 1-0.1*(1-am+am**1.06)*(1-taerosol)
    # else:
    #     taa = 0
    
    return taa
#---------------------

def RS(am, taerosol, ba, taa):
    """
    RS(am, taerosol, ba, taa)
    am is geometric air mass, 
    taerosol is intermediate funtion
    ba - this factor prescribes what proportion of scattered radiation 
    is sent off in the same direction as the incoming radiation
    ("forward scattering"). Bird recommends a value of 0.85 for rural aerosols
    """

    rs = np.zeros(am.shape)
    mask = am > 0
    rs[ mask ] = 0.0685+(1-ba)*(1-taerosol[mask]/taa[mask])

    # if am > 0:
    #     rs = 0.0685+(1-ba)*(1-taerosol/taa)
    # else:
    #     rs = 0

    return rs
#---------------------

def IDN(am, etr, taerosol, twater, tgases, tozone, trayliegh):
    """
    IDN(am, etr, taerosol, twater, tgases, tozone, trayliegh)
    idn is Direct Beam radiation (W/m^2)
    etr is Extraterrestrial Direct Beam intensity, W/m2
    am is geometric air mass
    """

    idn = np.zeros(am.shape)
    mask = am > 0
    idn[ mask ] = 0.9662*etr[mask]*taerosol[mask]*twater[mask]*tgases[mask]*tozone[mask]*trayliegh[mask]

    # if am > 0:
    #     idn = 0.9662*etr*taerosol*twater*tgases*tozone*trayliegh
    # else:
    #       idn = 0
    
    return idn
#---------------------

def IDHZ(idn, zangle):
    """
    IDHZ(idn, zangle):
    idhz is Direct Horizontal radiation (W/m^2)
    idn is Direct Normal radiation (W/m^2)
    zangle is the zenith angle
    """

    idhz = np.zeros(zangle.shape)
    mask = zangle < 90
    idhz[ mask ] = idn[mask]*np.cos(zangle[mask]/(180./3.14159))

    # if zangle < 90:
    #     idhz = idn*np.cos(zangle/(180./3.14159))
    # else:
    #     idhz = 0
    
    return idhz
#---------------------

def IAS(am, zangle, etr, tozone,tgases, twater,taa, trayliegh, ba, taerosol):
    """
    IAS(am, zangle, etr, tozone,tgases, twater,taa, trayliegh, ba, taerosol)
    ias is intermediate calculation 
    am is geometric air mass
    zangle is zenith angle
    etr is Extraterrestrial Direct Beam intensity, W/m2
    ba - this factor prescribes what proportion of scattered radiation 
    is sent off in the same direction as the incoming radiation
    ("forward scattering"). Bird recommends a value of 0.85 for rural aerosols 
    """

    ias = np.zeros(am.shape)
    mask = am > 0
    ias[ mask ] = etr[mask]*np.cos(zangle[mask]/(180./3.14159))*0.79*tozone[mask]*tgases[mask]*twater[mask]*taa[mask]*(0.5*(1-trayliegh[mask])+ba*(1-(taerosol[mask]/taa[mask])))/(1-am[mask]+(am[mask])**1.02)

    # if am > 0:
    #     ias = etr*np.cos(zangle/(180./3.14159))*0.79*tozone*tgases*twater*taa*(0.5*(1-trayliegh)+ba*(1-(taerosol/taa)))/(1-am+(am)**1.02)
    # else:
    #     ias = 0
    
    return ias
#---------------------

def GHZ(am, idhz, ias, albedo, rs):
    """
    GHZ(am, idhz, ias, albedo, rs)
    ghz is Global Horizontal radiation (W/m^2)
    am is geometric air mass
    idhz is Direct Horizontal radiation (W/m^2)
    ias is intermediate calculation 
    albedo is the ground reflectance. Albedo is used 
    to compute effect of multiple reflections between 
    the ground and the sky. Typical value for earth is 
    0.2, snow 0.9, vegetation 0.25
    rs is intermediate calculation
    """

    ghz = np.zeros(am.shape)
    mask = am > 0
    ghz[ mask ] = (idhz[mask]+ias[mask])/(1.-albedo*rs[mask])

    # if am > 0:
    #     ghz = (idhz+ias)/(1-albedo*rs)
    # else:
    #     ghz = 0
        
    return ghz
#---------------------

def DIFHZ(ghz, idhz):
    """
    DIFHZ(ghz, idhz)
    difhz is Diffuse Horizontal radiation (W/m^2)
    ghz is Global Horizontal radiation (W/m^2)
    idhz is Direct Horizontal radiation (W/m^2)
    """
    difhz = ghz - idhz

    return difhz

def main():
        """
        params = [lat, lon, GMTOffset, etr, press, ozone, water, aod380, aod500,
                  ba, albedo]
        clearsky(doy, hr, minute, params) 
        
        """
        params = [40, -105, -7, 840, 0.3, 1.5, 0.15, 0.1, 0.85, 0.2] 
        idn, ghz, difhz = clearsky([2], [2], [10], params)

        print "Direct Normal Isolation: %4.1f W/m^2 => should be 0" % idn
        print "Global Horizontal Isolation: %4.1f W/m^2  => should be 0" % ghz
        print "Diffuse Horizontal Isolation: %4.1f W/m^2  => should be 0" % difhz

#Self test code if run in stand alone mode
if __name__ == '__main__':
    main()

