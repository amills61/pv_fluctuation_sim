"""
Store two primary functions:
1) Generate a historical EPW weather file for use in SAM for a particular site
2) Generate a clearsky EPW weather file for use in SAM for a particular site 
"""

from zipfile import ZipFile
from StringIO import StringIO
import tarfile
import urllib
import csv
import re
import gzip
import pdb 
import os

REPO_NAME = 'pv_fluctuation_sim'

WEATHER_DIR = os.path.join(os.pardir, REPO_NAME + '_data', 
                           'weather', '%s' )

TEMP_DIR = os.path.join(os.pardir, REPO_NAME + '_data', 
                           'weather', 'temp', '%s' )

TEMP2_DIR = os.path.join(os.pardir, REPO_NAME + '_data', 
                           'weather', 'temp')

##################################################
#
# MAIN FUNCTIONS
#
##################################################

def build_historical_insolation_file(w, lat, lon, site_id):
    """
    TESTING COMPLETE

    Purpose:
    Create an EPW formatted file that extracts the historical insolation estimated 
    for a given latitude and longitude and the historical weather for a nearby 
    weather station

    Input:
    w - dictionary with the following elements: 
        w['year'] - year for historical insolation and weather data
        w['id'] - Weather station id (e.g., 722784)
        w['name'] - Weather station name (e.g., Phoexnix-Deer.Valley.AP.)
        w['state'] - Weather station state (e.g., AZ)
    lat - insolation site latiude in decimal degrees with positive in N
    lon - insolation site longitude in decimal degrees with positive in E
    site_id - unique identifier that links the data files to a particular site

    Output:
    pv_insolation_file - file name where EPW file with historical insolation 
                          is stored

    """
    print "Loading Weather Data...."
    weather_file = weather_data(w)
    
    print "Loading Actual Historical Insolation Data...."
    pv_insolation_file = historical_insolation(w['year'], weather_file, lat, 
                                               lon, site_id)

    return pv_insolation_file   

def build_clearksy_insolation_file(w, site_id, clr_insol):
    """
    INCOMPLETE TESTING - RUN WITH INPUT DATA
    Purpose:
    Input:
    clr_insol - numpy array of clearsky insolation data in order from Hour Ending 
                01/01/YY 01:00:00 LST with columns of global, direct, diffuse 
                insolation in W/m2 in that order
    Output:
    
    """
    print "Loading Weather Data...."
    weather_file = weather_data(w)
    
    print "Loading Clearsky Insolation Data...."
    clearsky_insolation_file = clearsky_insolation(w['year'], weather_file, site_id,
                                                   clr_insol)

    return clearsky_insolation_file

def test_historical():
    """
    Build the historical insolation file and store it at:
    WEATHER_DIR/historical_1_2004.epw
    """
    w = {"year": "2004",
         "id": '722784',
         "name": 'Phoenix-Deer.Valley.AP.',
         "state": 'AZ'}
    lat = "33.45"
    lon = "-111.95"
    site_id = "1"

    pv_insolation_file = build_historical_insolation_file(w, lat, lon, site_id)
    print pv_insolation_file

def test_clearsky():
    """
    Build a clearsky insolation EPW file and store it as:
    
    """
    w = {"year": "2004",
         "id": '722784',
         "name": 'Phoenix-Deer.Valley.AP.',
         "state": 'AZ'}
    site_id = "1"
    
    clearsky_insolation_file = build_clearksy_insolation_file(w, site_id, clr_insol)

    print clearsky_insolation_file

##################################################
#
# SUPPORT FUNCTIONS
#
##################################################

def weather_data(w):
    """
    Purpose:
    Bring particular year weather data into an EPW data file for a particualr 
    weather station

    Input:
    w - dictionary with the following elements: 
        w['year'] - year for historical insolation and weather data
        w['id'] - Weather station id (e.g., 722784)
        w['name'] - Weather station name (e.g., Phoexnix-Deer.Valley.AP.)
        w['state'] - Weather station state (e.g., AZ)
    
    Output:
    epw_file_name - location of EPW file with historcial weather data (str)

    """ 

    #### Identify the location of the weather file that will be created
    epw_file_name = WEATHER_DIR % ("weather_"+ w['id'] + "_" + w['year'] + ".epw")

    #### If the file already exists, then use it and exit 
    try:
        weather_file = open(epw_file_name) 
        print "\tWeather file already exists! Using existing weather file!"
        return epw_file_name
    except IOError:
       weather_file = open(epw_file_name, 'wb')
 
    writer = csv.writer(weather_file)

    #### Locate the TMY template that will be updated with the historic year data
    url = "http://apps1.eere.energy.gov/buildings/energyplus/weatherdata/" + \
        "4_north_and_central_america_wmo_region_4/1_usa/"

    weather_file_name = "USA_" + w['state'] + "_" + w['name'] + w['id'] + "_TMY3"
    url += weather_file_name + ".zip"

    print url

    #### Open the TMY template and load it into a tmy_reader object
    obj = urllib.urlopen(url)
    zipfile = ZipFile(StringIO(obj.read()))
    f = zipfile.open(weather_file_name + ".epw")
    tmy_reader = csv.reader(f)
      
    #### Write the EPW file header
    for row in range(8):  # Eight rows in original header  
        writer.writerow(tmy_reader.next()) 

    #### Swap out the TMY weather data with historic weather data
    try:
        writer, tmy_reader = swap_weather(writer, tmy_reader, w) 

    except KeyError:
        print "\nWARNING: No Historical weather file was available, using TMY" 
        writer, tmy_reader = pass_weather(writer, tmy_reader) 

    weather_file.close()
    
    return epw_file_name

def swap_weather(writer, tmy_reader, w):
    """
    Code to take the TMY weather data and swap it out with 
    weather data from a historic year 
    """
    #### Get the replacement weather data
        
    url = "ftp://ftp3.ncdc.noaa.gov/pub/data/nsrdb/" + w['id'] + ".tar.gz"

    historic_file = urllib.urlretrieve(url, TEMP_DIR % (w['id'] + ".tar.gz"))
    
    tar = tarfile.open(TEMP_DIR % (w['id'] +".tar.gz"), 'r')
   
    #### Extract the historic weaather data from the compressed archive 
    tar.extract(w['id'] + "/" + w['id'] + "_" + w['year'] + ".csv", 
                path = TEMP2_DIR)
        
    hist_reader = csv.reader(open(\
            TEMP_DIR % os.path.join(w['id'], (w['id'] + "_" + w['year'] + ".csv")), 
            "r"))

    #### Drop the header
    hist_reader.next()
        
    #### Step through the TMY data template row by row - 
    ####  Replace the correct columns and write the data to the output TMY3 file 
    hist_columns = [25,27,29,31,4,5,35,33,21,23,37,39]
    tmy_columns = [6,7,8,9,10,11,20,21,22,23,24,25]
    swap = zip(hist_columns, tmy_columns)

    for tmy_row in tmy_reader:
        #### Grab the row for the historic weather data
        hist_row = hist_reader.next()
        
        #### Scale the column 31 in the historic data 
        ####  (multily by 100 to convert from mbar to Pa)
        ####  and column 37 (divide by 1000 to convert from m to km)

        hist_row[31] = str(float(hist_row[31])*100)
        hist_row[37] = str(float(hist_row[37])/float(1000))
        
        #### Take columns from the historic  weather file and insert them into the 
        #### TMY weather template

        for pair in swap:
            tmy_row[pair[1]] = hist_row[pair[0]]
           
        writer.writerow(tmy_row) # Write out the revised TMY row

    return writer, tmy_reader 
    
def pass_weather(writer, tmy_reader):
    """
    If a historic weather year does not exist, then just pass the TMY data
    into the output weather file. 
    """

    for tmy_row in tmy_reader:
        writer.writerow(tmy_row)
        
    return writer, tmy_reader

def historical_insolation(year, weather_file, lat, lon, site_id):
    """

    Purpose:
    After the EPW weather file template has been updated, add the historical
    insolation data to the weather file

    Input:
    year - Year of historical weather data and historical insolation
    weather_file - location of EPW file with historical weather data
    lat - insolation site latiude in decimal degrees with positive in N
    lon - insolation site longitude in decimal degrees with positive in E
    site_id - unique identifier that links the data files to a particular site

    Output:
    pv_insolation_file_name - location of EPW file with historical insolation data

    """
        
    #### Identify the location of the  file that will be created
    pv_insolation_file_name = WEATHER_DIR % ("historical_"+ site_id + "_" + \
                                                 year + ".epw")

    pv_insolation_file = open(pv_insolation_file_name, 'wb')
    writer = csv.writer(pv_insolation_file)

    #### Extract the historical insolation data

    ## Use lat/lon to format the directory name (lonlat)
    dir_name = str(int(round((abs(float(lon))+1)/2)*2)) + \
        str(int(round((float(lat)-1)/2)*2))

    ##  Convert lat/lon into the format for the file name
    lat = str(int(round((float(lat)*100)/5))*5)

    ## lon needs to have three digits, hundreds place is zero if absolute 
    ## value is less than 100
    if abs(float(lon)) < 100:
        lon = "0" + str(int(round((abs(float(lon))*100)/5))*5)
    else:
        lon = str(int(round((abs(float(lon))*100)/5))*5)

    ## Create the URL for the actual historical insolation
    print "Lat: %s; Lon: %s" %(lat, lon)  
    url ="ftp://ftp.ncdc.noaa.gov/pub/data/nsrdb-solar/SUNY-gridded-data/"
    url += dir_name + "/SUNY_" + lon + lat + ".csv.gz"
    print url

    ## Open the zip file and grab the solar data
    compressed_file = urllib.urlretrieve(url, TEMP_DIR % "temp.gz")
    a_reader = csv.reader(gzip.open(TEMP_DIR % "temp.gz", 'rb'))

    ## Get the replacement solar insolation data, clean off all hours 
    ## where the year is too early

    ## Step through the file until the year matches
    match_year = False
    while not match_year: 
        row = a_reader.next()
        match_year = re.match(r'^' + year + '.', row[0])

    a_row = row #initialize with first row that matches

    #### Open the historic weather file 
    weather_read_file = open(weather_file, 'rb')
    weather_reader = csv.reader(weather_read_file)

    ## Write the header to the forecast output file
    for row in range(8):  #eight rows in original header   
        writer.writerow(weather_reader.next()) 
    
    #### Step through the TMY data row by row - 
    #### replace the correct columns and write the data to the output TMY3 file 
   
    ## Define the columns of the replacement solar data file to bring 
    ## into the orignal TMY3 file
    a_columns = [6,7,8]    #    Sglo, Sdir, Sdif

    # Define the columns of the original TMY3 file with the 
    # solar insolation data to replace 
    weather_columns = [13,14,15]    # (i.e. the lRevCol)  --- 
                                    # Get columns N,O,P 
                                    # (Global, Direct, Diffuse)

    swap = zip(a_columns, weather_columns)

    counter = 0
    for weather_row in weather_reader:
        if counter == 0:
            # Already grabbed the first row when matching years, use that first
            pass
        else:
            # Grab the row for the replacement forecast data 
            try:
                a_row = a_reader.next()
            except StopIteration: 
                # If exception and the file is next to the last hour
                if counter == 8759:
                    a_row = a_row  # Just use the previous hour's data
                    print "Could not read last row for site ID:" + \
                        "%s!! Used previous row" % (site_id)
                else:
                    print "ERROR: could not read a row in the solar data " + \
                        "that should be there.  Check the solar data file"
                    raise Exception
        counter +=1;
               
        # Replace the generic weather file solar data with the site's historical solar
        for pair in swap:
            weather_row[pair[1]] = a_row[pair[0]]

        # Write out the revised weather_row
        writer.writerow(weather_row) 
                                 
    pv_insolation_file.close()

    return pv_insolation_file_name

def clearsky_insolation(year, weather_file, site_id, clr_insol):
    """
    Purpose:
    Create an EPW file with clearsky insolation data in the solar insolation 
    columns and historical weather parameters in all other columns

    Input:
    year - Year of historical weather data 
    weather_file - location of historical weather file in EPW format
    site_id - Side identification used to store the clearsky EPW file 
    clr_insol - numpy array of clearsky insolation data in order from Hour Ending 
                01/01/YY 01:00:00 LST with columns of global, direct, diffuse 
                insolation in W/m2 in that order

    Output:
    clearsky_insolation_file_name - filename and location of EPW file with clearsky
                                    insolation data
    """
        
    #### Identify the location of the clearsky EPW file that will be created
    clearsky_insolation_file_name = WEATHER_DIR % ("clearsky_"+ site_id + "_" + \
                                                       year + ".epw" )
    clearsky_file = open(clearsky_insolation_file_name, 'wb') 
    writer = csv.writer(clearsky_file)
    
    #### Open the historic EPW weather file 
    weather_read_file = open(weather_file, 'rb')
    weather_reader = csv.reader(weather_read_file)

    #### Write the header to the clearsky EPW output file
    for row in range(8):  # eight rows in original header   
        writer.writerow(weather_reader.next()) 
    
    #### Step through the historical weather file data row by row - 
    #### replace the correct columns and write the data to the output EPW file 
   
    ## Define the columns of the replacement clearsky solar data file to bring 
    ## into the historical weather file
    clr_columns = [0,1,2]    # global, direct, diffuse

    ## Define the columns of the historical weather file with the 
    ## solar insolation data to replace 
    weather_columns = [13,14,15]    # (i.e. the lRevCol)  --- 
                                    # Get columns N,O,P 
                                    # (Global, Direct, Diffuse)

    swap = zip(clr_columns, weather_columns)

    counter = 0
    for weather_row in weather_reader:

        # Grab the row for the replacement clearsky insolation data 
        clr_row = clr_insol[counter]
                
        # Replace the solar insolation data
        for pair in swap:
            weather_row[pair[1]] = clr_row[pair[0]]

        # Write out the revised weather file with the forecast data row
        writer.writerow(weather_row) 
        # Advance to the next row of the clearsky insolation array
        counter += 1                         
    clearsky_file.close()

    return clearsky_insolation_file_name

if __name__ == '__main__':
    """
    """
#    test_clearsky()
    test_historical()
    
