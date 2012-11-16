"""
Purpose:
Based on the geographic location of different solar sites, generate 
correlated time-series of 1-min clearsky index at each site with the magniude 
and distribution of the within-hour variability based on the hourly-average 
clearsky index a particular site.  

Inputs:
- Site locations in latiude and longitude 
- Hourly average clearsky indiex for each site 

Internal data/ Key parameters: 
- Correlation relationships as a function of distance and time-scale 
- Distributiuons of within-hour variability based on the hourly average clearsky
   index 
- Spectral magnitude of normalized [on a uniform distribution] clearsky index as 
   a function of the average clearsky index for the hour and the time-scale 

Outputs: 
- 1-min clearness index at each site (with proper representation of correlation 
   between sites) over a full year 
"""

import pandas as pd 
import pdb
from scipy.stats import norm
import math
import numpy as np
import cPickle
import datetime
from datetime import timedelta as tdelta
from multiprocessing import Pool
from joblib import Parallel, delayed
import os

ROOT_DIR = os.path.join(os.curdir, '%s')

##################################################
#
# MAIN FUNCTIONS
#
##################################################


def main(solar_sites):
    """
    Status:
    TESTS LOOK OKAY
    Purpose:
     Synthesize 1-min time series of clearsky index that accounts for correlation
      between sites using the geographic location of the sites and the hourly 
      average clearsky index for each site 

    Inputs:
    solar_sites - a list  of SolarSite objects that will be used for the 
                  syntheseis of the clearsky index data

    Outpus:
    solar_sites - the same list of SolarSite objects now containing the additional 
                   1-min clearsky index data attached to each SolarSite object
    """
    #### Calculate a distance matrix between each of the sites 
    dist_mtx = distance_matrix(solar_sites)
    
    #### Preload the Spectral amplitude with different frequencies as a function of
    ####  the hourly clearsky index
    try:
        #### Load from stored file 
        psd = cPickle.load(open(ROOT_DIR % 'clearsky_index_psd.pkl', 'rb'))
    except IOError:
        psd = power_spectral_density()

    #### Calculate the correlation matrix based on the distance between the sites 
    freqs = psd['1.00']['freq']
    cohere = coherence_matrix(dist_mtx, freqs)

    #### Preload the within-hour distribution of clearsky index lookup table
    try:
        #### Load from stored file 
        cdf = cPickle.load(open(ROOT_DIR % 'clearsky_index_cdf.pkl', 'rb'))
    except IOError:
        cdf = clearsky_index_distribution(psd.items.values)

    #### For each hour synthesize the 1-min timeseries:
    ## Get the index and initialize the final timeseries 
    hour_index = solar_sites[0].clr_idx_hr.index
    year_start = hour_index[0] - tdelta(seconds = hour_index[0].minute * 60)
    year_end = hour_index[-1] - tdelta(seconds = hour_index[-1].minute * 60) + \
        tdelta(seconds = 59*60)
    year_rng = pd.date_range(year_start, year_end, freq = 'min')

    synth_hr_args = [solar_sites, dist_mtx.index, cohere, cdf, psd, freqs]

#***** Single core version ****** NOT CURRENTLY USED
#    TS_list = []
#    for dt in hour_index:
#        #### Synthesize the 1-min time series for each hour
#        TS = synthesize_hour(dt, synth_hr_args)
#        TS_list.append(TS)
#---------------------------------------------------

#****** Parallel version ********* ACTIVE
#    
    TS_list = Parallel(n_jobs= -2, verbose = 5)(
        delayed(synthesize_hour)(dt, synth_hr_args) for dt in hour_index)
#----------------------------------------

    #### Stich all of the hours together and ensure that there are no
    ####  hour-to-hour seams issues 
    
    print "Inserting all of the 1-min data from " +\
        "%s hours into the TS_year dataframe" % len(TS_list)

    for TS in TS_list:  
        ## Check to make sure there are not Nan values in the timeseries (indicates 
        ##  a potential error earlier in the code
        for id in TS.columns:
            if pd.isnull(TS[id]).sum() >0:
                print "Final TS has Nan!!!"
        try:
            TS_year = pd.concat([TS_year, TS])
        except NameError: # If TS_year doesn't exist, then initialize it first
            TS_year = TS

    #### Attach the 1-min clearsky timeseries to each solar site 
    for site in solar_sites:
        site.clr_idx_min = TS_year[site.id]

    return solar_sites 

def test():
    """
    Run a test with the inputs, call the main function,
    output the results
    """
    t_rng = pd.date_range('1/1/2004', periods = 4, freq = 'H')
    
    ss1 = SolarSite('1', 33.45, -111.95, pd.Series([1., .9, .8, .95], index = t_rng))
    ss2 = SolarSite('2', 33.55, -112.95, pd.Series([.9, .5, .3, .8], index = t_rng))
    ss3 = SolarSite('3', 32.35, -112.85, pd.Series([.8, .6, .4, .9], index = t_rng))
    ss4 = SolarSite('4', 34.65, -112.45, pd.Series([.9, .8, .7, 1.1], index = t_rng))
    solar_sites = [ss1, ss2, ss3, ss4]
    soalr_sites = main(solar_sites)
    
    return solar_sites


##################################################
#
# PRIMARY SUPPORT FUNCTIONS
#
##################################################

class SolarSite:
    """
    Purpose:
     Object that is used to keep track of the location and hourly clearsky
     data for each individual site.  The main function returns these objects with 
     the 1-min time series of the clearsky index attached to it.
    
    Input:
    site_id - any identifier that can be used to keep track of the individual sites
               and index all of the matricies used to synthezie the solar data
    lat - latitde of site in decimal degrees 
    lon - longitude of site in decimal degrees 
    clr_idx_hr - average hourly clearsky index TimeSeries object for the site
                  indexed by the date_time in LST with label on the half-hour

    Data:
    site_id, lat, lon, clr_idx_hr
    clr_idx_min - 1-min TimeSeries object with clearsky index for the site over 
                   a full year indexed by the date_time in LST 

    Methods:
    __init__(site_id, lat, lon, clr_idx_hr) - initialize the object, add the data 
                                              
    """
    def __init__(self, site_id, lat, lon, clr_idx_hr):
        """
        Purpose:
         Initizalize the SolarSite object 

        Input:
        site_id - any identifier that can be used to keep track of the individual 
                   sites and index all of the matricies used to synthezie the
                   solar data
        lat - latitde of site in decimal degrees 
        lon - longitude of site in decimal degrees 
        clr_idx_hr - average hourly clearsky index TimeSeries object for the site
                      indexed by the date_time in LST with label on the half-hour
        """

        #### Validate the input data
        self.id = site_id
        self.lat = float(lat)
        self.lon = float(lon)
        self.clr_idx_hr = clr_idx_hr


def distance_matrix(solar_sites):
    """
    Purpose:
    Based on the latitude and longitude of each site build a matrix with the 
    distance between each site in km

    Input:
    solar_sites - list of SolarSite objects 

    Output:
    dm - a DataFrame indexed by the id of each solar site with columns also 
                the id of each solar site, having the distance between each site in 
                kilometers (km)
    """

    #### Get the list of ids of the solar sites 
    ids = [s.id for s in solar_sites]

    #### Build a lookup table for the the lat and lon of each site
    d = {'lat': [s.lat for s in solar_sites],
         'lon': [s.lon for s in solar_sites]}
    loc = pd.DataFrame(d, index = ids)
    
    #### Index the blank distance matrix by the site IDs 
    dm = pd.DataFrame(index = ids, columns = ids, dtype = float)
    
    #### Go through each possible pair of sites, calculate the distance, and store
    ####  the distance in the distance matrix
    for i in dm.columns:
        for j in dm.index:
            dm[i][j] = vdist(loc['lat'][i], loc['lon'][i], 
                             loc['lat'][j], loc['lon'][j]) # km
            if i == j:
                dm[i][i] = 0

    #### Impose a minimum distance of 1 km
    dm = dm.fillna(1) #km 

    return dm

def coherence_matrix(dist_mtx, frequencies):
    """
    Status:
    TESTS LOOK OKAY

    Purpose:
    Calculate the coherence between two sites as a function of distance and 
    frequency based on stored parameters 

    Input:
    dist_mtx - Dataframe with distance between two sites in km for each pair 
    frequencies - a list of frequncies in order of slowest freuqency to highest 
                   frequencies 

    Output:
    cohere - a Panel data item with items being the position of the corresponding 
              frequency in the frequencies list, indexed by the site id and columns
              with the site id from the distance matrix
              cohere[freq_idx][col site id][row site_id]
    """
    #### Stored parameters for the coherence function, these are derived from an
    #### analysis of insolation data from the DOE ARM network
    a1 = 84.64; a2 = 0.33361; b = 0.9011
    
    C = {}
    for f, i in zip(frequencies, range(len(frequencies))):
        #### For each frequency create a DataFrame with the coherence based on the 
        ####  distances between sites     
        C[i] = b * np.exp(-a1 * f * dist_mtx) + \
            (1 - b) * np.exp(-a2 * f * dist_mtx) 

    #### Convert it into a Panel organized as:
    ####  cohere[frequency list index][site column][site index]
    cohere = pd.Panel(C)

    return cohere

def power_spectral_density():
    """
    Status:
    TESTING LOOKS GOOD

    Purpose:
    Create a Panel object with the hourly average clearsky index as the items 
    then have the frequency as the index for each specral coefficient 
    
    Input:
    None

    Output:
    psd - a Panel object with the hourly clearsky index as the items, and columns 
           containing the spectral coefficient 'psd' for each frequency 'freq'

    """
    #### Specify the length of the samples used to create the PSD and the subset 
    #### of the clearsky index data that was used 
    N = 64; cos_min = 0.15

    #### The clearsky index is from 0 to 1.2 with 0.05 sized steps in between
    items = ["%3.2f" % (x/20.) for x in range(25)]

    #### Build the data dictonary by building up DataFrame objects 
    d = {}
    
    #### REPLACE THIS WITH A PICKLE OR CSV FILE THAT CAN BE LOADED BY ANY USER
    conn = opendbDict("synth")  
    cursor = conn.cursor ()

    for i in items:
        #### Call the PDS data for the particualr critera
        get_psd = """
          SELECT power_real as p_real, power_imag as p_imag, frequency as freq
          FROM psd WHERE kbar = %s and N = %s and cos_min = %s
          ORDER BY frequency ASC
          """ % (i, N, cos_min)
        cursor.execute(get_psd)
        tmp = pd.DataFrame(list(cursor.fetchall()))
        tmp = {'freq': tmp['freq'], 'psd': (tmp['p_real'] + tmp['p_imag']*1j)}
        d[i] = pd.DataFrame(tmp)
        
    #### Close the connection to the database
    cursor.close ()    
    conn.close ()
    
    #### Convert the data dictionary into a Panel object 
    psd = pd.Panel(d)
    
    #### Save the psd to a file 
    save_file = open(ROOT_DIR % 'clearsky_index_psd.pkl', 'wb')
    cPickle.dump(psd, save_file)
    save_file.close()

    return psd

def clearsky_index_distribution(clear_sky_index_list):
    """
    Status:
     TESTING LOOKS GOOD 

    Purpose:
    Load the stored CDF functions for the within-hour distribution of the clearsky
     index for a given hourly average clearsky index

    Input:
    clear_sky_index_list - list of hourly average clearsky index values for which 
                            there are unique PSDs and CDFs  
    Output:
    cdf - Dataframe object with columns corresponding to the hourly average 
           clearsky index for the particular hour, indexed by the cummulative
           probability distribution (F), and the clearsky index within the hour.
           
           For example when the hourly average clearsky index is '1.15' for the hour,
           95% of the time the clearsky index within that hour is less than: 
           cdf['1.15'][0.95] = 1.377 

    """
    #### Open a connection to the database
    conn = opendbDict("synth")  
    cursor = conn.cursor()
    
    for kbar in clear_sky_index_list: 
        #### Build the querey to the database, name the columns according to the 
        #### hourly average clearsky index for the particualr distribution
        get_cdf = """
         SELECT F, k as '%s' FROM cdf WHERE kbar = %s 
         ORDER BY F ASC
         """ % (kbar, kbar)
        cursor.execute(get_cdf)
        
        #### Grab the data for a particualr hourly average clearsky index, ensure 
        ####  that all of the return data are treated as floats
        d_kbar = list(cursor.fetchall())
        for i in range(len(d_kbar)):
            for key in d_kbar[i].keys():
                d_kbar[i][key] = max(float(d_kbar[i][key]),0)

        #### Convert the return data into a DataFrame with the cummulative 
        #### probability ('F') as the index 
        d_kbar = pd.DataFrame(d_kbar)
        d_kbar.set_index('F', inplace = True)
        
        #### Join the particular average clearsky value to the full Dataframe
        try:
            cdf = cdf.join(d_kbar)
        except UnboundLocalError:
            cdf = d_kbar
    
    #### Close the connection to the database 
    cursor.close ()    
    conn.close ()
    
    #### Save the cdf to a file 
    save_file = open(ROOT_DIR % 'clearsky_index_cdf.pkl', 'wb')
    cPickle.dump(cdf, save_file)
    save_file.close()

    return cdf

def synthesize_hour(dt, parameters):
    """"
    Purpose: 
    Wrap all of the steps needed to synthesize the 1-min correlated time series at 
    each site into one function so that it can be run in parallel

    """
    #### Unpack the parameters 
    solar_sites, site_index, cohere, cdf, psd, freqs = parameters

    #### Calculate the spectral amplitude matrix depending on the sites average
    ####  clearsky index for the hour and the correlation between sites

    ## Build a DataFrame object that has the hourly clearsky index for each site
    ## indexed by the site id
    kbars = [site.clr_idx_hr[dt] for site in solar_sites]
    kbars = pd.Series(kbars, index = site_index)

    ## Use this hourly average clearsky value to create a spectral magnitude mtx
    try:
        S = spectral_amplitude_matrix(kbars, cohere, psd)
    except KeyError:
        pdb.set_trace()

    #### Synthesize the 1-min time series or normalized clearksy index 
    ####  (on a uniform distribution) for each site for the hour
    TS_norm = synthysize_norm_TS(S, freqs)

    for id in TS_norm.columns:
        if pd.isnull(TS_norm[id]).sum() >0:
            print "TS_norm has Nan at " + str(dt) + " !!!"
            TS_norm[id] = TS_norm[id].fillna(0)

    #### For each site within the hour: 

    #### Get the actual distribution of the clearsky index for the hour
    ####  based on the hourly average clearsky index from the pre-loaded 
    ####  lookup table  
    kbars =  [("%3.2f") % (round(float(k)*20)/20) for k in kbars]
    kbars = pd.Series(kbars, index = site_index)
        
    #### De-normalize the time-series data using the distribution of the clearsky
    ####  index for the site and the hour
    ## Transform the time series into the normalized CDF
    TS_F = TS_norm.apply(norm.cdf).apply(np.round, args = (3,))
       
    #### Check for any null values - indicates a potnetial error
    for id in TS_F.columns:
        if pd.isnull(TS_F[id]).sum() >0:
            print "TS_F has Nan at " + str(dt) + " !!!"
            TS_F[id] = TS_F[id].fillna(0.5)

    ## For each site, look up the clearsky index at that particular probability
    ## level in the CDF for the site's hourly average clearsky index 
    d = {}
    for id in site_index:
        d[id] = cdf[kbars[id]][TS_F[id]].values[:60]

    #### Create a time series index that starts at the begining of the hour 
    #### (based on dt) and goes to the end of the hour
    start_dt = dt - datetime.timedelta(seconds = dt.minute * 60)
    hour_rng = pd.date_range(start_dt, periods=60, freq='min')
        
    #### Convert the clearsky index into a timeseries that starts at the
    #### beginning of the hour and coninutes to the end of the hour
    TS = pd.DataFrame(d, index = hour_rng)

    #### Check for any null values, if they exist it may indicate an error 
    for id in TS.columns:
        if pd.isnull(TS[id]).sum() > 0:
            TS[id] = TS[id].fillna(float(kbars[id]))

    return TS

def test_synthesize_norm_hour(dt, parameters):
    """ Test function used only to examine a full year of normalized output 
    Purpose:

    Replicate the function of synthesize_hour(), but direclty output the normalized 
    timeseries so that a full year can be checked for abnormal behaviour at the hour-
    to-hour seams.  

    Intput:
    Same as synthesize_hour()

    Output:
    TS_norm - normalized time series like TS from synthesize_hour()

    """

    #### Unpack the parameters 
    solar_sites, site_index, cohere, cdf, psd, freqs = parameters

    #### Calculate the spectral amplitude matrix depending on the sites average
    ####  clearsky index for the hour and the correlation between sites

    ## Build a DataFrame object that has the hourly clearsky index for each site
    ## indexed by the site id
    kbars = [site.clr_idx_hr[dt] for site in solar_sites]
    kbars = pd.Series(kbars, index = site_index)

    ## Use this hourly average clearsky value to create a spectral magnitude mtx
    try:
        S = spectral_amplitude_matrix(kbars, cohere, psd)
    except KeyError:
        pdb.set_trace()

    #### Synthesize the 1-min time series or normalized clearksy index 
    ####  (on a uniform distribution) for each site for the hour
    TS_norm = synthysize_norm_TS(S, freqs)

    for id in TS_norm.columns:
        if pd.isnull(TS_norm[id]).sum() >0:
            print "TS_norm has Nan at " + str(dt) + " !!!"
            TS_norm[id] = TS_norm[id].fillna(0)

    #### For each site within the hour: 
    d = {}
    for id in site_index:
        d[id] = TS_norm[id].values[:60]

    #### Create a time series index that starts at the begining of the hour 
    #### (based on dt) and goes to the end of the hour
    start_dt = dt - datetime.timedelta(seconds = dt.minute * 60)
    hour_rng = pd.date_range(start_dt, periods=60, freq='min')
        
    #### Convert the clearsky index into a timeseries that starts at the
    #### beginning of the hour and coninutes to the end of the hour
    TS_norm = pd.DataFrame(d, index = hour_rng)

    return TS_norm 



def spectral_amplitude_matrix(kbars, cohere, psd ):
    """
    Status:

    Purpose:
    Calculate the spectral amplitude matrix that accounts for the average clearsky
     index at each site and the correlation between sites
 
    Input:
    kbars - a Series object indexed by site id with each sites hourly average 
             clearsky index for the hour
    cohere - a Panel data item with items being the position of the corresponding 
              frequency in the frequencies list, indexed by the site id and columns
              with the site id from the distance matrix
              cohere[freq_idx][col site id][row site_id]
    psd - a Panel object with the hourly clearsky index as the items, and columns 
           containing the spectral coefficient for each frequency 

    Output:
    S - a Panel data item with items being the position of the corresponding 
         frequency in the frequencies list, indexed by the site id and columns
         with the site id from the distance matrix
         S[freq_idx][col site id][row site_id]

    """

    #### Build matrix S in the same shape and indcies as cohere 
    S = pd.Panel(items = cohere.items, major_axis = cohere.major_axis,
                 minor_axis = cohere.minor_axis, dtype = complex)

    ##Diagonal = PSD for that site
    for id in kbars.index:
        # Round kbar to nearest 0.05
        kbar =  ("%3.2f") % (round(float(kbars[id])*20)/20)

        #### Load PSD into diagonial 
        for freq_idx, freq in psd[kbar]['freq'].iteritems():
            ###---Make the any component with a freq ~< 1 per hour 0 
            ###   (include 1/64 min)??
            if freq < 1/3900.:
                S[freq_idx][id][id] = np.random.random()*10e-6
            else:
                S[freq_idx][id][id] = psd[kbar]['psd'][freq_idx]
       
    ## Off diagonal = use distance and frequency to calculate cohere, 
    ##  use that and diagonal to calculate S[i!=j]
    L = len(S.major_axis)
    for freq_idx, freq in psd[kbar]['freq'].iteritems():
        for i in range(L):
            for j in range(L):
                if i !=j: #off diagonal
                    coh = cohere[freq_idx].ix[i].ix[j]
                    ## Calculate the amplitude of the cross-spectrum from 
                    ## the coherence and the PSD's
                    S[freq_idx].ix[i].ix[j] = coh*(S[freq_idx].ix[i].ix[i] * \
                                                       S[freq_idx].ix[j].ix[j])**0.5
                    if freq_idx == 0:
                        S[freq_idx].ix[i].ix[j] = (S[freq_idx].ix[i].ix[j] - \
                                                       np.random.random()*10e-6)

    return S 

def synthysize_norm_TS(S, freqs):
    """
    Status:
    TESTS OKAY

    Generate N correlated time-series, TS(j in N, output with time),
    from a spectral matrix \em{S}
    Where each diagonal of \em{S[fm]} is the power spectral density at average 
    frequency of fm and each off diagonal is the cross-spectral density 
    """

    def invert(V, t):
        """
        Do inverse fourier transform of each element of the 
        N X 1 matrix of complex fourier coefficients (V)
        (V) musrt be in the format of the output of np.fft.rfft(TS[])
        """
        n = (len(V)-1)*2. 
        
        #### As described in calcPSD.segPSD, you need to multiply by the number 
        #### of points, n, to get correct inverse.  It also looks like it needs 
        #### division by sqrt(2) (emperical - can you find the reason?)
        TS = np.fft.irfft(V*n/2**0.5) 
        
        TS = pd.Series(TS, index = t)

        return TS

    def transform(S):
        """
        Populate a lower-trianglar matrix based on the spectral matrix S
        Based on a recursive formula
        Create the matrix H with the same dimensions as the spectral matrix S
        """
        # Number of rows
        rows = S.shape[0]
        # Number of cols
        cols = S.shape[1]
        H = np.zeros((rows,cols),dtype = complex)
        for k in range(cols):
            for j in range(rows):
                if k > j: 
                    H[j,k] = 0 #makes it lower triangular
                elif k == 0:
                    if j == 0:
                        H[j,k] = S.ix[k].ix[j]**0.5
                    else:
                        H[j,k] = S.ix[k].ix[j]/H[0,0]                   
                elif j == k:
                    sumH = 0 +0j
                    for l in range(k):
                        sumH += H[k,l]**2         
                        H[k,k] = (S.ix[k].ix[k] - sumH)**0.5
                else: # when j!=k  
                    sumH = 0 +0j
                    for l in range(k):
                        sumH += H[j,l] * H[k,l]
                    try:
                        H[j,k] = (S.ix[k].ix[j] - sumH)/H[k,k]
                    except:
                        print "ERROR in transform!! "+ \
                            "Division by zero -> for k = %s" % k

        #### Convert H into a DataFrame object 
        H = pd.DataFrame(H, columns = S.columns, index = S.index, dtype = complex)

        return H
    #----End transform

    def whitenoise(ids):
        """
        Create an N X N diagonal matrix, X, of whitenoise with unit-magnitude
        """
        #### Initialize the whitenoise matrix
        X = pd.DataFrame(index = ids, columns = ids, dtype = complex)

        for k in X.columns:
            for j in X.index:
                if j == k: # a diagnoal element
                    # generate uniform random number on [0,2pi]
                    theta = np.random.rand()*2*np.pi 
                    X[j][k] = np.exp(1j*theta) 
                else:
                    X[j][k] = 0

        return X 
    #----End whitenoise

    def four_coeff(H,X):
        """
        Estimate the complex fourier coefficients of the simulated wind speeds 
        """
        #### Create a vector of ones indexed by the site ids 
        ones = pd.Series(1, index = X.columns)
        #### Estimate the complex fourier coefficient for each site 
        V = H.dot(X).dot(ones)
        
        return V

    #----End four_coeff

    #### Initialize the N X M array of the Fouier coefficients of the simulated 
    ####  wind speeds for N
    ####  and time series of lenght M
    
    V = pd.DataFrame(index = freqs, columns = S[0].columns, dtype = complex)

    #### Calcualte the Fourier coefficients of the simulated wind speeds,
    ####  iterate over each average frequency

    for freq_idx, S_fm in S.iteritems():
        #### Calculate the lower-triangular transformation matrix (N X N) ,
        #### H(f_m), based on the 
        #spectral matrix for the average frequency, S_fm
        H_fm = transform(S_fm)

        #### Create a N X N diagonal matrix of unit-magnitude independent white 
        #### noise inputs (X)
        X = whitenoise(S_fm.columns)

        #Calculate the N X 1 matrix of the complex Fouier coefficients of 
        #the simulated wind speeds, where each N is a different site, j    
        V.ix[freq_idx] = four_coeff(H_fm,X)
    
    #### Initialize a DataFrame of with the time in minutes as the index and the 
    #### columns corresponding to the site ID 
    
    #### Calculate time stamp to go along with time series
    ##    last frequency is sampling frequency (Fs)/2
    sample_freq = freqs[freqs.index[-1]].real
    t = np.arange((len(freqs)-1)*2.)/(sample_freq*2.)/60.

    ## Turn it into integer minutes 
    t = np.round(t).astype(int)

    TS = pd.DataFrame(index = t , columns = S[0].columns, dtype = float )

    #### Get the time series for each of the N sites: 
    ####  initialize the time-series of length 2*(M-1) for each site j \in N   

    for id, V_j in V.iteritems():
        #### Do inverse fourier transform of each element, M, of the 
        ####  matrix of complex fourier coefficients (V) 
        TS[id] = invert(V_j, t)    

        #### Check for any Nan, if too many print a warning
        if pd.isnull(TS[id]).sum() > 20:
            error = "Warning!!! Too many Nan " +\
                "on site %s replacing with 0's and continuing..." % \
                (id)
            print error
            print V_J
#            raise Exception(error)
            
        #### Replace any Nan with zeros
        TS[id] = TS[id].fillna(0)

    return TS


##################################################
#
# SECONDARY SUPPORT FUNCTIONS
#
##################################################

def vdist(lat1, lon1, lat2, lon2):
    """
    VDIST - compute distance between points on the WGS-84 ellipsoidal Earth
    to within a few millimeters of accuracy using Vincenty's algorithm

    s = vdist(lat1,lon1,lat2,lon2)

    s = distance in kilommeters
    lat1 = GEODETIC latitude of first point (degrees)
    lon1 = longitude of first point (degrees)
    lat2, lon2 = second point (degrees)

    Original algorithm source:
    T. Vincenty, "Direct and Inverse Solutions of Geodesics on the Ellipsoid
    with Application of Nested Equations", Survey Review, vol. 23, no. 176,
    April 1975, pp 88-93

    Notes: 
    (1) Error correcting code, convergence failure traps, antipodal corrections,
    polar error corrections, WGS84 ellipsoid parameters, testing, and comments
    written by Michael Kleder, 2004.
    (2) Vincenty describes his original algorithm as precise to within
    0.01 millimeters, subject to the ellipsoidal model.
    (3) Essentially antipodal points are treated as exactly antipodal,
    potentially reducing accuracy by a small amount.
    (4) Failures for points exactly at the poles are eliminated by
    moving the points by 0.6 millimeters.
    (5) Vincenty's azimuth formulas are not implemented in this
    version, but are available as comments in the code.
    (6) The Vincenty procedure was transcribed verbatim by Peter Cederholm,
    August 12, 2003. It was modified and translated to English by Michael Kleder.
    Mr. Cederholm's website is http://www.plan.aau.dk/~pce/
    (7) Code to test the disagreement between this algorithm and the
    Mapping Toolbox spherical earth distance function is provided
    as comments in the code. The maximum differences are:
    Max absolute difference: 38 kilometers
    Max fractional difference: 0.56 percent
    """
    def sign(x):
        """
        Return the sign of x: if x<0 => -1, x>0 => 1, x = 0 => 0
        """
        if x == 0:
            y = 0
        else:
            y = x/(np.abs(x)* 1.)
        return y

    #Input check:
    if np.abs(lat1)>90 or abs(lat2)>90:
         print "Input latitudes must be between -90 and 90 degrees, inclusive."
         return

    #Supply WGS84 earth ellipsoid axis lengths in meters:
    a = 6378137 # definitionally
    b = 6356752.31424518 # computed from WGS84 earth flattening coeff. definition

    #convert inputs in degrees to radians:
    lat1 = lat1 * 0.0174532925199433
    lon1 = lon1 * 0.0174532925199433
    lat2 = lat2 * 0.0174532925199433
    lon2 = lon2 * 0.0174532925199433
    
    # Correct for errors at exact poles by adjusting 0.6 millimeters:
    if np.abs(np.pi/2-np.abs(lat1)) < 1e-10:
        lat1 = sign(lat1)*(np.pi/2-(1e-10)) # Check sign
        
    if np.abs(np.pi/2-np.abs(lat2)) < 1e-10:
        lat2 = sign(lat2)*(np.pi/2-(1e-10))

    f = (a-b)/a
    U1 = math.atan((1-f)*math.tan(lat1))
    U2 = math.atan((1-f)*math.tan(lat2))
    lon1 = np.mod(lon1,2*np.pi)
    lon2 = np.mod(lon2,2*np.pi)
    L = np.abs(lon2-lon1)
    if L > np.pi:
        L = 2*np.pi - L

    lambd = L
    lambdold = 0;
    itercount = 0;

    # Force at least one execution
    while itercount == 0 or np.abs(lambd-lambdold) > 1e-12:  
        itercount = itercount+1;
        if itercount > 50:
            print "Points are essentially antipodal. Precision may be " + \
                "reduced slightly"
            lambd = np.pi;
            break
        
        lambdold = lambd
        sinsigma = np.sqrt(
            (np.cos(U2) * np.sin(lambd))**2 + \
                (np.cos(U1) * np.sin(U2) - \
                     np.sin(U1) * np.cos(U2) * np.cos(lambd))**2) 

        cossigma = np.sin(U1)*np.sin(U2)+np.cos(U1)*np.cos(U2)*np.cos(lambd) 
        sigma = math.atan2(sinsigma,cossigma)
        alpha = math.asin(np.cos(U1)*np.cos(U2)*np.sin(lambd)/np.sin(sigma))
        cos2sigmam = np.cos(sigma)-2*np.sin(U1)*np.sin(U2)/np.cos(alpha)**2
        C = f/16*np.cos(alpha)**2*(4+f*(4-3*np.cos(alpha)**2))

        lambd = L+(1-C)*f*np.sin(alpha)*\
            (sigma + C*np.sin(sigma)*\
                 (cos2sigmam +C*np.cos(sigma)*(-1+2*cos2sigmam**2)))

        # Correct for convergence failure in the case of essentially antipodal points
        if lambd > np.pi:
            print "Points are essentially antipodal. Precision may " + \
                "be reduced slightly."
            lambd = np.pi
            break

    u2 = np.cos(alpha)**2*(a**2-b**2)/b**2
    A = 1+u2/16384*(4096+u2*(-768+u2*(320-175*u2)))
    B = u2/1024*(256+u2*(-128+u2*(74-47*u2)))
    deltasigma = B*np.sin(sigma)*\
        (cos2sigmam+B/4*(\
            np.cos(sigma)*(-1+2*cos2sigmam**2)-\
                B/6*cos2sigmam*(-3+4*np.sin(sigma)**2)*(-3+4*cos2sigmam**2)))
    s = b*A*(sigma-deltasigma)

    return s/1000.

##################################################
#
# TEMPORARY SUPPORT FUNCTIONS 
#
##################################################

def opendb(dbName):
    import MySQLdb
    conn = MySQLdb.connect (host = "localhost",
                            user = "root",                        
                            db = dbName)
    return conn

def opendbDict(dbName):
    import MySQLdb
    import MySQLdb.cursors
    conn = MySQLdb.connect (host = "localhost",
                            user = "root",
                            db = dbName,
                            cursorclass=MySQLdb.cursors.DictCursor)
    return conn

##################################################
#
# SECONDARY TEST FUNCTIONS
#
##################################################

def test_cdf():
    items = ["%3.2f" % (x/20.) for x in range(25)]
    cdf = clearsky_index_distribution(items)
    return cdf 


def test_cohere():
    import numpy as np
    tmp = np.array([[0,10,10,16], [10,0,12,10],[10,12,0,10],[16,10,10,0]])
    ids = ['01', '02', '03', '04']
    dist_mtx = pd.DataFrame(tmp, index = ids, columns = ids, dtype = float)
    psd = power_spectral_density()
    cohere = coherence_matrix(dist_mtx, psd['1.00']['freq'])
    return cohere 

def test_psd():
    psd = power_spectral_density()
    return psd 

def test_S():

    kbars = [1,0.95,0.7,1.05]
    kbars = pd.Series(kbars, index = dist_mtx.index)    
    psd = test_psd()
    cohere = test_cohere()
    S = spectral_amplitude_matrix(kbars, cohere, psd)
    return S
    
def test_TS():
    psd = test_psd()
    freqs = psd['1.00']['freq']
    cohere = test_cohere()
    S = test_S()
    TS = synthysize_norm_TS(S, freqs)
    return TS

def test_examine_spectrum(ss):
    """Examine the spectrum of each site to determine if there are abnormalities
    
    Purpose:
    Examine the spectrum from a full year of synthesized data in order to determine 
    if there is abnormal power in at the hour-to-hour seams 

    Input:
    ss - list of SolarSite objects with clr_idx_min attached to each site 
 
    Output:
    Plot showing spectrum

    """
    from matplotlib import pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for s in ss:
        y = s.clr_idx_min
        n = len(y) # length of the signal
        k = np.arange(n)
        T = n/(1/60.)
        frq = k/T # two sides frequency range
        frq = frq[range(n/2)] # one side frequency range
        Y = np.fft.rfft(y)/n # fft computing and normalization
        Y = Y[range(n/2)]
        ax.plot(frq,abs(Y)) # plotting the spectrum
        
    plt.xlabel('Freq (Hz)')
    plt.ylabel('|Y(freq)|')
        
    plt.show()

    
        
if __name__ == '__main__':
    """
    """
    solar_sites = test()

#    tmp = np.array([[0,10,10,16], [10,0,12,10],[10,12,0,10],[16,10,10,0]])
#    ids = ['01', '02', '03', '04']
#    dist_mtx = pd.DataFrame(tmp, index = ids, columns = ids, dtype = float)

#    kbars = [1,0.95,0.7,1.05]
#    kbars = pd.Series(kbars, index = dist_mtx.index)

#    psd = test_psd()
#    cohere = test_cohere()
#    cdf = test_cdf()
#    S = test_S()
#    TS = test_TS()
