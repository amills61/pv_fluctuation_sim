"""
Inputs:
- PV site location
- PV plant configuration/technology and size
- Year

Internal data/ Key parameters: 
- BIRD Model parameters 

Outputs: 
- 1 hour PV production timeseries 
- 1 hour average clearsky index 
- 1-min clearsky PV production

To test on Becquerel use: C:\Python27_32bit\python.exe due to SAM limitations for 
running on a 64-bit build 
"""

#### Load the functions required to build the EPW files for SAM runs 
import GenerateInsolationFiles as gif
import datetime
import numpy as np
import pandas as pd
import BIRDModel as bm
import os
import pdb


## Only include the sam module if it is the Becquerel computer
try:
    import PVSAMSim as sam
except OSError:
    print "Not able to load SAM modules, PVSAMSim is not enabled!!"


GMTOFFSET = -7 # Mountain Standard Time, Change this if sites are not located in 
               # Mountain Standard Time zone

DC_AC_RATIO = 1/0.83 # Ratio of AC nameplate of PV platn to peak DC rating 
LEAP_YEARS = ["2000", "2004", "2008", "2012", "2016"]

##################################################
#
# MAIN FUNCTIONS
#
##################################################


def main(year, lat, lon, site_id, w_id, w_name, w_state, cap_ac, config):
    """
    Input:
    year - Historical year used for solar insolation and weather data
    lat - Latitude in decimal degrees with positive values for N
    lon - Longitude in decimal degrees with positive values for E
    site_id - PV site identification number for naming stored files 
    w_id - Weather station id (e.g., 722784)
    w_name - Weather station name  (e.g., Phoexnix-Deer.Valley.AP.)
    w_state - Weather station state (e.g., AZ)
    cap_ac - Nameplate capacity of PV plant in MW
    config - string defining of PV plant configuration (res, comm, usf, or ust)
    
    Output:
    pv_prod_hr - 1 hour average PV plant production TimeSeries object with 'val'
                 and indexed by 'date_time' in LST labeled on the half hour 
    clr_idx_hr - 1 hour average clearsky index TimeSeries object with 'val' 
                 and indexed by 'date_time' in LST labeled on the half hour
    clr_prod_min - 1-min clearsky production TimeSeries object with 'val' and 
                 indexed by 'date_time' in LST
    """

    #### Validate input data
    lat = str(lat)
    lon = str(lon)
    site_id = str(site_id)
    year = str(year)
    w = {"year": year,
         "id": str(w_id),
         "name": str(w_name),
         "state": str(w_state)}
    cap_ac = float(cap_ac)
    if config not in ["res", "comm", "usf", "ust"]:
        raise ValueError ("%s is not a valid configuration!" %config)

    #### Create insolation file for hourly PV production time series (pv_prod_hr)
    pv_insolation_file = gif.build_historical_insolation_file(w, lat, lon, site_id)
    
    #### Create 1-min and 1 hour clearsky insolation time series 
    print "Building 1-min time series of clearsky data"
    clr_insol_min, cosz_min = bird_model_minute(year, lat, lon)
    clr_insol_hr = get_hourly_average(clr_insol_min)
    cosz_hr = get_hourly_average(cosz_min)

    #### Create insolation file for hourly clearsky PV production time series 
    ## Set the column order as global, direct, diffuse and get the values 
    clr_insol = clr_insol_hr[['ghz','dni','dfhi']].values 
    clr_insolation_file = gif.build_clearksy_insolation_file(w, site_id, clr_insol)
    
    #### Ensure that there is no insolation around the midnight hours, if there is 
    #### then something went wrong, go into debug mode
    if clr_insol[:3].sum() > 0.0:
        pdb.set_trace()

    #### Create the PV production and clearsky production from the insolation files 
    #### using the SAM model 
    try:
        pv_prod_hr = pv_plant_model(cap_ac, lat, config, year, pv_insolation_file)
        clr_prod_hr = pv_plant_model(cap_ac, lat, config, year, clr_insolation_file)
    except AssertionError:
        #### If the pv_plant_model cannot calculate the PV production then go into 
        #### debug mode to figure out the cause
        pdb.set_trace() 

    #### Create hourly clearness index time series (clr_idx_hr)
    clr_idx_hr = pv_prod_hr/clr_prod_hr

    #### Set the clearness index to NaN where the cosz for the hour is less than 
    #### 0.25 (or less than about 15 degrees above the horizon)
    clr_idx_hr[cosz_hr < 0.25] = None

    ## Identify the hours where the clearsky index is above the level in the 
    ## DOE ARM Network database
    clr_idx_hr[clr_idx_hr > 1.2] = None 
    
    #### Set the clearsky index to the daily average clearsky index 
    #### where the clearsky production is not defined

    ## Get the average clearsky index for the day where the hourly data exists
    clr_idx_day = \
        (clr_idx_hr[clr_idx_hr.notnull()].tshift(-30,freq = 'min')
         ).resample('D', how = 'mean', closed = 'left', label = 'left')
    
    ## Resample it to hourly and make sure the time stamps line up with the hourly 
    ## clearsky index data
    clr_idx_day = clr_idx_day.resample('H', closed = 'right', fill_method = 'pad')
    last_day = pd.Series(clr_idx_day.ix[-1], 
                         index = pd.date_range('12/31/%s 01:00:00' % year, 
                                               periods=23, freq = 'H'))
    clr_idx_day = pd.concat([clr_idx_day, last_day])
    clr_idx_day = clr_idx_day.tshift(30, freq = 'min')
    
    ## Replace all the NaN values in the hourly clearsky with the daily average
    clr_idx_hr = clr_idx_hr.combine_first(clr_idx_day)

    #### Create 1-min clearsky PV producton time series (clr_prod_min)
    clr_prod_min = clearsky_production_minute(clr_insol_min, clr_insol_hr, 
                                             clr_prod_hr, config)
    #### Return output data
    return pv_prod_hr, clr_idx_hr, clr_prod_min

def test():
    """
    Run a test with the inputs, call the main function,
    output the results
    """
    year = 2004
    lat = 35.25
    lon = -111.45
    site_id = '20'
    w_id = '723783'
    w_name = 'Grand.Canyon.National.Park.AP.'
    w_state =  'AZ'
    cap_ac = 114.5
    config = "res"

    pv_prod_hr, clr_idx_hr, clr_prod_min = main(year, lat, lon, site_id, w_id, 
                                                          w_name, w_state,
                                                          cap_ac, config)

    return pv_prod_hr, clr_idx_hr, clr_prod_min


##################################################
#
# PRIMARY SUPPORT FUNCTIONS
#
##################################################

def pv_plant_model(cap_ac, lat, config, year, insolation_file):
    """
    Status:
    RUNS FINE, BUT PV PLANT OUTPUT SEEMS QUITE LOW
 
    Purpose:
    Use the Solar Advisor Model python code to simulate the output of a PV plant 
    with a given configuration and weather file

    Input:
    cap_ac - PV plant AC nameplate capacity in MW
    lat - PV site latitude in decimal degrees with positive in the North
    config - string defining configuration (res, comm, usf, or ust)
    year - year of data used to generate PV data 
    insolation_file - string spefifing the location of the *.epw weather file with 
                       the weather data and insolation data for the PV plant

    Output:
    prod_hr - TimeSeries object that specifies the hourly plant output in MW ('val')
               and is indexed by the 'date_time' in GMT labeled on the half-hour
    
    """
    configuration_dict = {"res":"residential",
                          "comm":"commercial",
                          "usf":"utility_scale_fixed",
                          "ust":"utility_scale_sat"}
    config = configuration_dict[config]

    #### Calcualte the PV plant DC capacity based on the assumed DC/AC ratio
    cap_dc = cap_ac * DC_AC_RATIO


    #### Generate an hourly time series of PV plant output starting at hour ending
    #### 01/01/YYYY 01:00:00 in LST
    hourly_pv_output = sam.simulate_pv(config, cap_dc, lat, insolation_file)

    ## Duplicate the last day of the year if it is a leap year since SAM cannot 
    ## deal with leap years 
    if year in LEAP_YEARS:
        hourly_pv_output = append_leap(hourly_pv_output)
        
    ## Create a date range for the datetime index where the label is on the half-hour
    start = datetime.datetime(int(year), 1,1,0, 30)
    end = datetime.datetime(int(year), 12, 31, 23,30)
    rng = pd.date_range(start, end, freq = 'H')
        
    ## Create Pandas TimeSeries object in LST
    try:
        prod_hr = pd.Series(hourly_pv_output, index = rng)
    except AssertionError:
        pdb.set_trace()

    return prod_hr 

def bird_model_minute(year, lat, lon):
    """
    Status:
    TESTS LOOK GOOD, MAY NEED TO TUNE PARAMETERS

    Purpose:
    Calculate the clearsky insolation based on date,time, and atmospheric param
    
    Input:
    year - the year for the simulation (str) 
    lat - Latitude in decimal degrees with positive values for N (str)
    lon - Longitude in decimal degrees with positive values for E (str)

    Output:
    clr_insol_min - 1-min clearsky insolation DataFrame of TimeSeries objects with 
                     direct normal insolation in W/m2 as 'dni', 
                     global horizontal insolation in W/m2 as 'ghz',
                     diffuse horizonal insolation in W/m2 as 'dfhi' 
                     indexed by 'date_time' in GMT
    cosz_min - 1-min TimeSeries object with cosine of the solar zenith
                angle (sun is up above horizon when this number
                is greater than 0 (use 0.15 to be sure it is up)
    
    """
    lat = float(lat)
    lon = float(lon)
    year = int(year)

    #### Get the clearsky parameters 
    press = 840;  ozone = 0.3;  water = 1.5; aod380 = 0.15; aod500 = 0.1; 
    ba = 0.85;  albedo = 0.2; gmtoffset = GMTOFFSET

    #### Create a 1-minte date range from the start to the end of the year
    start = datetime.datetime(int(year), 1,1,0,0)
    end = datetime.datetime(int(year), 12,31,23,59)
    rng = pd.date_range(start, end, freq = "min")

    #### For each minute, calculte the direct, global, and diffuse insolation 
    #### using the BIRD model
    bird_params = [lat, lon,gmtoffset, press, ozone, water, aod380, aod500, 
                   ba, albedo]

    dni, ghz, dfhi, cosz = bm.clearsky(rng.dayofyear, rng.hour, rng.minute, 
                                       bird_params)

    d = {'ghz': ghz, 'dni': dni, 'dfhi': dfhi} 
    clr_insol_min = pd.DataFrame(d, index = rng, columns = ['ghz','dni','dfhi'])

    cosz_min = pd.Series(cosz, index = rng)
    
    return clr_insol_min, cosz_min


def clearsky_production_minute(clr_insol_min, clr_insol_hr, clr_prod_hr, config):
    """
    Status:
    TESTING SEEMS OKAY

    Purpose:
    - Based on the 1-min insolation data and the ratio of
       hourly average production to hourly average insolation in a particular hour
       generate a 1-min time series of PV production
    - This assumes that there is a constant proportional relationship between
       PV production and PV insolation for any particular hour.  This should be 
       tested carefully

    Input:
    clr_insol_min - TimeSeries object with 1-min 'dni', 'ghz', 'dfhi' 
                     and 'date_time' in LST
    clr_insol_hr - TimeSeries object with hourly average of the insolation indexed 
                    by the GMT labeled on the half-hour
    clr_prod_hr - TimeSeries object with hourly average of the PV production indexed 
                    by the GMT labeled on the half-hour
    config - string that is res, comm, usf, or ust.  If ust then use 'dni' for 
             scaling parameter, 'ghz' otherwise

    Output:
    clr_prod_min - TimeSeries object with 1-min clearsky PV production in MW as'val'
                    indexd by the 'date_time' in LST
    """

    #### Get the average scaling parameter for the hour
    if config == 'ust':
        scaling = clr_prod_hr/clr_insol_hr['dni']
    else:
        scaling = clr_prod_hr/clr_insol_hr['ghz']

    #### Upsample the hourly data to minute time series 
    ## Upsample by interpolating across hours 
    scaling = scaling.resample('1Min')
    scaling = scaling.interpolate(method = 'time')

    ## Append the remaining minutes to get it to a full hour
    year = scaling.index[-1].year
    first_hour = pd.Series(index = pd.date_range('1/1/%s 00:00:00' % year, 
                                            periods=29, freq = 'min'))
    last_hour = pd.Series( index = pd.date_range('12/31/%s 23:31:00' % year, 
                                            periods=29, freq = 'min'))

    scaling = pd.concat([first_hour, scaling, last_hour])

    #### Calculate the minmute by minute clearsky production as proprtional to the 
    #### ratio of the hourly average between insolation and pv production
    if config == 'ust':
        clr_prod_min = scaling * clr_insol_min['dni']
    else:
        clr_prod_min = scaling * clr_insol_min['ghz']
    
    #### Replace any Not a number (nan) values with a zero production 
    clr_prod_min = clr_prod_min.fillna(0)

    return clr_prod_min



##################################################
#
# SECONDARY SUPPORT FUNCTIONS
#
##################################################

def get_hourly_average(min_ts):
    """
    Purpose:
    - convert a minute TimeSeries object into an hourly average TimeSeries object
    
    Input:
    min_ts - TimeSeries object with 1-min time stamps 

    Output:
    hr_ts - TimeSeries object with hourly averages with time stamp on the half hour
    
    """
    #### First resample to the full hourly average, with the label as 
    #### hour beginning 
    hr_ts = min_ts.resample('H', closed = 'left', label = 'left', how = 'mean')

    #### Then shift the label to the middle of the hour 
    hr_ts = hr_ts.tshift(30, freq = 'min')
    
    return hr_ts

def append_leap(ts):
    """
    Purpose:
    Append the last day of SAM output to the time series to account for leap years, 
     which SAM otherwise ignores 

    Input:
    ts - array or list of 8760 hourly values 

    Output:
    ts - array or list of 8784 values
    """
    if type(ts) == list:
        ts += ts[-24:]
    elif type(ts) == np.ndarray:
        ts = list(ts)
        ts += ts[-24:]
        ts = np.array(ts)
    else:
        raise TypeError('ts must be a list or np.array object')
    return ts




##################################################
#
# SECONDARY TEST FUNCTIONS 
#
##################################################

def test_preloaded():
    """
    Test the main function but with pre-loaded Test data (much quicker)
    """
    import cPickle
    year = 2004
    lat = 33.45
    lon = -111.95
    site_id = '1'
    cap_ac = 24.6
    root_dir = os.path.join(os.pardir, 'pv_fluctuation_sim_data', 'test', '%s' )
    pv_insolation_file = root_dir % "historical_1_2004.epw"
    
    pv_prod_hr = cPickle.load(open(root_dir % 'pv_prod_hr.pkl', 'rb'))
    clr_insol_min = cPickle.load(open(root_dir % 'clr_insol_min.pkl', 'rb'))
    
    clr_insol_hr = get_hourly_average(clr_insol_min)

    clr_insolation_file = root_dir % "clearsky_1_2004.epw"
    clr_prod_hr = cPickle.load(open(root_dir % 'clr_prod_hr.pkl', 'rb'))

    clr_idx_hr = pv_prod_hr/clr_prod_hr
    clr_idx_hr[clr_prod_hr < 0.15*clr_prod_hr.max()] = 0.95

    clr_idx_hr[(clr_prod_hr < 0.25*clr_prod_hr.max()) & (clr_idx_hr > 1) ] = 0.95   

    clr_prod_min = clearsky_production_minute(clr_insol_min, clr_insol_hr, 
                                              clr_prod_hr)
    
    return pv_prod_hr, clr_idx_hr, clr_prod_min


def test_bird():
    """
    Test the BIRD model to generate clearsky insolation data
    """
    clr_insol_min = bird_model_minute("2004", "33.45", "-111.95")
    import cPickle
    root_dir = os.path.join(os.pardir, 'pv_fluctuation_sim_data', 'test', '%s' )
    output = open(root_dir % 'clr_insol_min.pkl', 'wb')
    cPickle.dump(clr_insol_min, output)
    output.close()
    
    return clr_insol_min

def test_pv_plant_model():
    """
    Test the PV plant output with historical insolation data
    """
    root_dir = os.path.join(os.pardir, 'pv_fluctuation_sim_data', 'test', '%s' )
    insolation_file = root_dir % "historical_1_2005.epw"

    print insolation_file

    prod_hr = pv_plant_model(24.6, "33.45", "comm", "2004", insolation_file)

    import cPickle
    output = open(root_dir % 'pv_prod_hr.pkl', 'wb')
    cPickle.dump(prod_hr, output)
    output.close()

    return prod_hr 

def test_clr_plant_model():
    """
    Test the PV plant output with clearsky insolation data
    """
    root_dir = os.path.join(os.pardir, 'pv_fluctuation_sim_data', 'test', '%s' )
    insolation_file = root_dir % "clearsky_2_2004.epw"

    prod_hr = pv_plant_model(13.1, "33.55", "ust", "2004", insolation_file)

    import cPickle
    output = open(root_dir % 'clr_prod_hr.pkl', 'wb')
    cPickle.dump(prod_hr, output)
    output.close()

    return prod_hr 


if __name__ == '__main__':
    """
    """
#    clr_insol_min = test_bird()
#    pv_prod_hr = test_pv_plant_model()
#    clr_prod_hr = test_clr_plant_model()
#    pv_prod_hr, clr_idx_hr, clr_prod_min = test_preloaded()
    pv_prod_hr, clr_idx_hr, clr_prod_min = test()
