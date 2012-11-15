"""
Purpose:
For a selection of PV sites, generate 1-min timeseries of each site both for 
PV production and clearksky production 

Input:
- Site data in an Excel (*.xls) file describing each site 
  (ASSUMES lon has been put in as a POSITIVE NUMBER RATHER THAN THE NEGATIVE IT 
  SHOULD BE)
        

Output:
- csv files containing the 1-min clearsky PV data and the 1-min production data for 
  each site 
- A csv file for the clearsky production and actual PV production for all sites 
- a dictionary of solar sites objects containing all the site specific data 
  with the key being the site id 

"""

import PVHistoricalData as historical
import SolarSynthesis as synth
import PVPlantFilter as filt
import cPickle
from matplotlib import pyplot as plt
import pdb
import os

IS_TEST = False

BUILD_HISTORICAL = True
RUN_NEW_SIMULATIONS = True

REPO_NAME = 'pv_fluctuation_sim'
PV_PROD_DIR = os.path.join(os.pardir, REPO_NAME + '_data', 
                           'pv_production', '%s' )
SITE_DIR = os.path.join(os.pardir, REPO_NAME + '_data', 
                           'site_config', '%s' )


WIND_SPEED = 2 # m/s from Marcos et al 2011 paper with PV plants in Spain
               # Impacts the effectiveness of the area of the PV plant for smoothing 
               # fluctuations

def main(year):

    #### Initialize the sites as SolarSite objects 
    ssites = build_solar_sites(year)
    if IS_TEST:
        ssites = {'1': ssites['1'], '18': ssites['18'], 
                  '23': ssites['23'], '17': ssites['17'],
                  '16': ssites['16'], '21': ssites['21'],
                  '22': ssites['22'], '18': ssites['18'],
                  '19': ssites['19'], '24': ssites['24']}

    if BUILD_HISTORICAL:
        #### For each site generate the hourly PV production, hourly clearsky index 
        #### and 1-min clearsky production, attach it to the SolarSite object
        print "\n.... Building historical PV production and clearsky datafiles...\n"
 
        for id in ssites:
            #### Build the historical PV production and clearsky data 
            pv_prod_hr, clr_idx_hr, clr_prod_min = \
                historical.main(ssites[id].year, ssites[id].lat, ssites[id].lon, 
                                ssites[id].id,
                                ssites[id].w_id, ssites[id].w_name, 
                                ssites[id].w_state, 
                                ssites[id].cap_ac, ssites[id].config)

            #### Attach the data to the solar site object 
            ssites[id].pv_prod_hr = pv_prod_hr
            ssites[id].clr_idx_hr = clr_idx_hr 
            ssites[id].clr_prod_min = clr_prod_min
            ssites[id].has_historical = True

            #### Save the site data to a file
            historical_file_name = PV_PROD_DIR % \
                                 (ssites[id].id + '_' + year + '_historical.pkl')

            save_file = open(historical_file_name,'wb')
            cPickle.dump(ssites[id], save_file)
            save_file.close()

    else:
        #### Load the historical data from saved files 
        for id in ssites:
            print "...Loading site %s" % id
            historical_file_name = PV_PROD_DIR % \
                (ssites[id].id + '_' + year + '_historical.pkl')

            ssites[id] = cPickle.load(open(historical_file_name,'rb'))

    #### Using all sites synthesize correlated 1-min clearsky index timeseres 
    ####  for each site 
    if RUN_NEW_SIMULATIONS:
        print "\n.... Synthesizing correlated 1-min clearsky index data ...\n"
        ss_list = []
        for id in ssites:
            s = synth.SolarSite(ssites[id].id, ssites[id].lat, 
                                ssites[id].lon, ssites[id].clr_idx_hr)
            ss_list.append(s)

        ## Call the main function
        ss_list = synth.main(ss_list)
    
        ## Store the 1-min clearsky index with the relevant SolarSite object
        print ".... Attaching the 1-min clearsky index data to the SolarSite " +\
            "objects..."
        for ss in ss_list:
            ssites[ss.id].clr_idx_min = ss.clr_idx_min

        #### For each site filter the 1-min clearsky index data and produce the 1-min
        ####  PV plant output 
        print "\n.... Filtering clearsky index and convering to 1-min " +\
            "PV production...\n"
        for id in ssites:    
            pv_prod_min = filt.main(ssites[id].clr_idx_min, ssites[id].clr_prod_min, 
                                    ssites[id].cap_ac, WIND_SPEED, ssites[id].config)
            ssites[id].pv_prod_min = pv_prod_min
            ssites[id].has_synth = True

            #### Save the site data to a file 
            complete_file_name = PV_PROD_DIR % \
                (ssites[id].id + '_' + year + '_complete.pkl')

            save_file = open(complete_file_name,'wb')
            cPickle.dump(ssites[id], save_file)
            save_file.close()

    else:
        #### Load the historical data from saved files 
        for id in ssites:
            complete_file_name = PV_PROD_DIR % \
                (ssites[id].id + '_' + year + '_complete.pkl')

            ssites[id] = cPickle.load(open(complete_file_name,'rb'))
        
    return ssites

def test():
    IS_TEST = True
    solar_sites = main('2004')
    return solar_sites


class SolarSite:
    """
    Purpose:
     Object that is used to keep track of the location and hourly clearsky
     data for each individual site.  
    
    Input:
    site_id - uniqe site identifier that can be used to keep track of the 
              individual sites
    lat - latitde of site in decimal degrees 
    lon - longitude of site in decimal degrees 
    year - year of the historical data for simulation (2004 or 2005)
    w_id - Weather station id (e.g., 722784)
    w_name - Weather station name  (e.g., Phoexnix-Deer.Valley.AP.)
    w_state - Weather station state (e.g., AZ)
    cap_ac - Nameplate capacity of PV plant in MW
    config - string defining of PV plant configuration (res, comm, usf, or ust)

    Data:
    site_id, lat, lon, clr_idx_hr
    clr_idx_min - 1-min TimeSeries object with clearsky index for the site over 
                   a full year indexed by the date_time in LST 

    Methods:
    __init__(site_id, year lat, lon, ) - initialize the object, add the data 
                                              
    """
    def __init__(self, site_id, year, lat, lon, w_id, w_name, w_state, cap_ac, 
                 config):
        """
        Purpose:
         Initizalize the SolarSite object 

        Input:
        site_id - uniqe site identifier that can be used to keep track of the 
              individual sites
        lat - latitde of site in decimal degrees 
        lon - longitude of site in decimal degrees 
        year - year of the historical data for simulation (2004 or 2005)
        w_id - Weather station id (e.g., 722784)
        w_name - Weather station name  (e.g., Phoexnix-Deer.Valley.AP.)
        w_state - Weather station state (e.g., AZ)
        cap_ac - Nameplate capacity of PV plant in MW
        config - string defining of PV plant configuration (res, comm, usf, or ust)
        """

        #### Validate the input data
        self.id = str(site_id)
        self.year = str(year)
        self.lat = float(lat)
        self.lon = float(lon)
        self.w_id = str(w_id)
        self.w_name = str(w_name)
        self.w_state = str(w_state)
        self.cap_ac = float(cap_ac) 
        self.config = str(config)
        self.has_historical = False
        self.has_synth = False

    def __str__(self):
        describe = "\nSite id: '%s'" % self.id
        describe += "\nYear: %s" % self.year
        describe += "\nLocation: %s lat, %s lon" % (self.lat, self.lat)
        describe += "\nAC Capacity: %4.1f MW" % self.cap_ac
        describe += "\nConfiguration: '%s'\n" % self.config
        #### Add information about what data has been added to the object?
        if self.has_historical:
            describe += "\nIncludes the following data:"
            describe += "\nclr_idx_min: %s pts" % len(self.clr_idx_min) 
            describe += "\nclr_prod_min: %s pts" % len(self.clr_prod_min)
            describe += "\nclr_idx_hr: %s pts" % len(self.clr_idx_hr) 
            describe += "\npv_prod_hr: %s pts" % len(self.pv_prod_hr) 
        if self.has_synth:
            describe += "\npv_prod_min: %s pts" % len(self.pv_prod_min) 
        
        return describe
        
def build_solar_sites(year):
    from xlrd import open_workbook,cellname
    from xlwt import Workbook
    site_config_file = SITE_DIR % 'pv_site_data.xls'

    def site_meta_data(row_index):
        """
        For a given row, put all of the relvant site data into a dictionary 
        """
        site_id = str(int(sheet.cell(row_index, 0).value))
        cap_ac = float(sheet.cell(row_index, 1).value)
        config = str(sheet.cell(row_index, 2).value)
        lat = str(sheet.cell(row_index, 3).value)
        lon = str(sheet.cell(row_index, 4).value * -1)
        weather_id = str(int(sheet.cell(row_index, 5).value))
        weather_name = str(sheet.cell(row_index, 6).value)
        weather_state = str(sheet.cell(row_index, 7).value)
        
        meta_data = {'site_id':site_id,
                     'cap_ac': cap_ac, 
                     'config': config,
                     'lat': lat,
                     'lon': lon,
                     'w_id': weather_id, 
                     'w_name': weather_name,
                     'w_state':weather_state}

        return meta_data

    # Open the site info file 
    book = open_workbook(site_config_file)
    sheet = book.sheet_by_name('Site_Info')

    # Identify the number of sites
    sites = range(1,sheet.nrows)

    #### Initialize the dictionary that will contain the solar_site objects 
    solar_sites = {}
    # For each site, get the site info
    for site_index in sites:
        info  = site_meta_data(site_index)
        s  = SolarSite(info['site_id'], year, info['lat'], info['lon'], info['w_id'],
                       info['w_name'], info['w_state'], info['cap_ac'], 
                       info['config'])
        solar_sites[s.id] = s
    
    return solar_sites 
 
def sum_sites(ss, data_name):
    for id in ss:
        try:
            sum_data = getattr(ss[id], data_name) + sum_data 
        except NameError:
            sum_data = getattr(ss[id], data_name)
    return sum_data

def plot_prod(ss):
    pv_prod_hr = sum_sites(ss, 'pv_prod_hr')
    pv_prod_min = sum_sites(ss, 'pv_prod_min')
    clr_prod_min = sum_sites(ss, 'clr_prod_min')
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(pv_prod_hr.index, pv_prod_hr, 'k', label = 'PV: hour')
    ax.plot(pv_prod_min.index, pv_prod_min, 'r', label = 'PV: min')
    ax.plot(clr_prod_min.index, clr_prod_min, 'b', label = 'Clear: min')
    fig.autofmt_xdate()
    plt.legend()
    plt.show()

def test_build():
    solar_sites = build_solar_sites('2004')
    return solar_sites 

if __name__ == '__main__':
    """
    """
    ss = test()
    plot_prod(ss)
