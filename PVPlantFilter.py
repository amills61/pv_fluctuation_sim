"""
Inputs:
- 1-min clearsky index
- 1-min clearsky production
- PV plant AC capacity
- Hourly average wind speed (or a single annual average wind speed estimate) at the 
  cloud height
- configuration to determine if a broader area smoothing shold be applied (for 'res'
   and 'comm'

Internal data/ Key parameters: 
- Conversion from plant AC capacity to plant area 

Outputs: 
- 1-min plant PV plant output 
"""
import pandas as pd
import numpy as np
import pdb

##################################################
#
# MAIN FUNCTIONS
#
##################################################


def main(clr_idx_min, clr_prod_min, cap_ac, wind_speed, config):
    """
    Status:
    TESTS LOOK GOOD, HAVE NOT TRIED HOURLY WIND SPEED

    Purpose:
    Convert the 1-min clearsky index estimated at a point location to the 1-min 
    PV production for a PV plant accounting for any within-plant smoothing based 
    on a first order linear filter
    
    Input:
    clr_idx_min - Timeseries of 1-min clearsky index at the site of the PV plant
    clr_prod_min - Timeseries of 1-min PV plant production assuming the sky were 
                    clear
    cap_ac - Plant AC nameplate in MW
    wind_speed - wind speed at the cloud height in m/s, either as a TimeSeries or as 
                 an anual average value (scalar)
    config - string of 'res', 'comm', or other  to determine if capacity or region
              should be used to set area
    Output:
    pv_prod_min - TimeSeries of 1-min PV plant output in MW accounting for the 
                   within plant smoothing
    """
    #### Get the plant smoothing paramter based on the wind speed and plant size
    ####  or the area of the region
    alpha = filter_param(cap_ac, wind_speed, config)

    if type(alpha) == float or type(alpha) == int:
        alpha = pd.Series(alpha, index = clr_idx_min.index)

 
    #### Initialize the filter with  the first minute clearsky index
    clr_idx_prev = clr_idx_min.ix[0]

    #### Initialize the smoothed output timeseries 
    clr_idx_min_smooth = pd.Series(index = clr_idx_min.index, dtype = float)

    #### Apply an exponential filter to the 1-min TimeSeries 
    for dt in clr_idx_min.index:
        smooth_clr_idx = alpha[dt] * clr_idx_min[dt] + (1- alpha[dt]) * clr_idx_prev
        clr_idx_min_smooth[dt] = smooth_clr_idx 
        clr_idx_prev = smooth_clr_idx 

    #### Convert the smooted clearsky index into PV plant output
    pv_prod_min = clr_idx_min_smooth * clr_prod_min

    return pv_prod_min


##################################################
#
# SUPPORT FUNCTIONS
#
##################################################

def filter_param(cap_ac, u, config):
    """
    Status:
    TESTS LOOK GOOD

    Purpose:
    Treat PV plant power output as the signal output of a first order, low pass 
    filter where the input signal is the clearsky index at a point.  Baased on:

    Marcos, J., L. Marroyo, E. Lorenzo, D. Alvira, and E. Izco. 2011. "From
     Irradiance to Output Power Fluctuations: The PV Plant as a Low Pass Filter." 
     Progress in Photovoltaics: Research and Applications:
     doi:10.1002/pip.1063.

    From http://en.wikipedia.org/wiki/Low-pass_filter:
       Where:
        Tc = cutoff period by which everything of longer period can pass
        dt = time step (1-min)
        alpha = dt/(Tc/(2*pi) + dt)

    Input:
    cap_ac - PV plant capacity in MW
    u - wind speed in m/s either as a scalar value or as timeseries of 
                 for the same year as the clearsky data hourly values 
    config - if 'res' or 'comm' then set the area to be the area of a region, not the
              plant
    Output:
    alpha - exponential smoothing parameter based on the plant size and wind speed 
             at cloud height as a TimeSeries indexed by the given index  
    """
    #### Determine the plant area (m^2) based on an assumed relationship between PV 
    #### PV capacity and area from Marcos et al 2011
    if config == 'res' or config == 'comm':
        #### 11 km X 11km or about 0.1 degree X 0.1 degree at 35 deg lat
        area = 123. * 10**6 
    else:
        area = cap_ac * 69897.  # cap_ac in MW,  area in m^2 from Marcos et al
    l = area ** 0.5 

    #### Calcualte the cut-off-period for the plant area and the wind speed in min
    #### Based on the relationship derived from Marcos et al. 2011 where the wind 
    #### speed that they used was 2 m/s
    Tc = l/u / 60. # min

    #### Calcualte the alpha parameter 
    alpha = 1./(Tc/(2*np.pi) + 1.)

    #### Upscale from hourly values to minute values by interpolatiing (using time)
    ####  between hours 
    if type(alpha) == float or type(alpha) == int:
        pass
    else:
        alpha = alpha.resample('1Min')
        alpha = alpha.interpolate(method = 'time')

    return alpha

def test():
    """
    Run a test with the inputs, call the main function,
    output the results
    """
    index = pd.date_range('1/1/2004', periods = 240, freq = 'min')
    clr_idx_min = pd.Series(np.array(
        [ 1.00063,  0.9975 ,  0.98988,  1.02008,  1.02952,  1.01241,
        1.01953,  1.0209 ,  1.01291,  1.01404,  1.02363,  1.01276,
        1.03243,  1.02151,  1.02456,  1.02803,  1.01291,  0.99095,
        0.99672,  0.99197,  0.98858,  0.99332,  0.98275,  0.99769,
        1.     ,  1.00305,  1.01676,  1.01922,  1.01298,  1.007  ,
        0.99893,  1.01283,  0.99845,  0.99936,  0.99848,  1.01085,
        1.00234,  1.00044,  0.9973 ,  0.99216,  0.98916,  0.98131,
        0.98873,  0.99733,  0.99458,  0.98624,  0.97213,  1.00089,
        0.99829,  1.00044,  0.9909 ,  0.96809,  0.99173,  0.99211,
        0.99414,  0.97276,  0.95965,  0.98732,  0.98428,  0.97724,
        0.39691,  0.51477,  0.56079,  0.69835,  0.92897,  0.88393,
        1.01855,  0.87536,  0.94079,  1.06371,  1.07845,  1.18492,
        1.17048,  1.08599,  0.94911,  0.9576 ,  0.96402,  1.02143,
        0.98122,  0.99717,  0.97206,  0.84265,  0.91006,  0.73243,
        0.77595,  0.96373,  0.90875,  0.42486,  0.8998 ,  1.0251 ,
        1.11459,  1.01363,  1.10762,  1.1104 ,  0.97884,  0.97081,
        0.93537,  0.90928,  0.95678,  0.91058,  0.83884,  0.98424,
        0.99875,  1.08503,  0.98239,  0.87172,  0.77907,  0.94938,
        0.89601,  0.89378,  0.87376,  0.81427,  0.77143,  0.91517,
        0.7656 ,  0.63538,  0.3789 ,  0.48124,  0.95734,  0.97053,
        0.77743,  0.88582,  0.75336,  0.97451,  0.78734,  0.63057,
        0.39944,  0.51566,  0.97246,  0.99342,  0.86167,  0.87698,
        0.92629,  0.79529,  0.76548,  0.74589,  0.58864,  0.58349,
        0.40569,  0.59799,  0.76899,  0.79739,  0.9076 ,  0.70346,
        0.39725,  0.41413,  0.94814,  1.0378 ,  0.99277,  0.88582,
        1.01713,  0.99772,  0.85507,  0.83331,  0.67978,  0.83715,
        0.92479,  0.94541,  0.91175,  1.047  ,  1.09218,  0.80525,
        1.03568,  1.19302,  0.93361,  0.97451,  1.19001,  0.97593,
        1.13227,  0.96183,  1.05414,  1.12106,  0.91034,  0.76658,
        0.35422,  0.28938,  0.25496,  0.42582,  0.54407,  0.58035,
        0.93589,  0.67692,  0.9306 ,  0.82776,  0.94215,  0.94263,
        0.97902,  1.02085,  0.96984,  0.9814 ,  1.02269,  0.9541 ,
        1.04796,  0.99455,  0.99639,  1.07867,  1.00442,  0.92445,
        0.78406,  0.79914,  0.78675,  0.67692,  0.70393,  0.63978,
        0.91502,  0.969  ,  0.94135,  0.93589,  0.93805,  0.9541 ,
        0.93649,  0.92251,  0.89238,  0.92445,  0.94435,  0.96815,
        0.97111,  0.99829,  0.98243,  0.98256,  0.97995,  1.00075,
        1.0538 ,  0.96415,  0.95329,  1.00373,  1.00613,  0.96015,
        1.01809,  1.07408,  1.0359 ,  0.98091,  0.98417,  0.98619,
        0.97238,  1.02508,  0.99184,  1.01483,  0.91317,  0.92113]), index = index)
    
    cap_ac = 150 # MW                        
    clr_prod_min = pd.Series([cap_ac]*240, index = index)
    wind_speed = 2 # m/s
    pv_prod_min = main(clr_idx_min, clr_prod_min, cap_ac, wind_speed)
    
    plt.plot(clr_idx_min.index, clr_idx_min * clr_prod_min, 'r', 
             label = 'Unfiltered')
    plt.plot(pv_prod_min.index, pv_prod_min, 'b', label = 'Filtered: %s MW' % cap_ac)
    plt.legend()
    plt.show()
    
    return pv_prod_min


if __name__ == '__main__':
    """
    """
    test()

