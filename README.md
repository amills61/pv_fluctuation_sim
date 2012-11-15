pv_fluctuation_sim
==================

Python-based tools for generating 1-min timeseries of PV plant output between 
multiple sites accounting for correlations between sites. 


These tools consist of three main modules:

---------------------
PVHistoricalData.py:
---------------------
Inputs:
- PV site location
- PV plant configuration/technology and size
- Year

Internal data/ Key parameters: 
- BIRD Clearksky insolation model parameters 

Outputs: 
- 1 hour PV production timeseries 
- 1 hour average clearsky index 
- 1-min clearsky PV production


---------------------
SolarSynthesis.py:
---------------------
Inputs:
- Solar site locations
- 1 hour average clearsky index

Internal data/ Key parameters: 
- Correlation relationships as a function of distance 
- Distributions and spectral magnitude depending on hourly average 
   clearsky index

Outputs:
- 1-min clearsky index for a point location at each site over a year 

---------------------
PVPlantFilter.py
---------------------
Inputs:
- PV plant capacity
- 1 hour wind speed at cloud height
- 1-min clearsky production 
- 1-min clearsky index 

Internal data: 
- Relationship between plant capacity and plant area

Outputs:
- 1-min PV plant output

##########################################

It also uses several support files:

--------------------
GenerateInsolationFiles.py
--------------------
- Stores functions to build EPW files for SAM from either historical data or 
   using clearsky insolation

--------------------
PVSAMSim.py
--------------------
- Takes an EPW weather file, a DC nameplate capacity, a configuration, and a latitude
   to create an hourly set of PV plant production 

--------------------
msvcp100.dll
msvcr100.dll
ssc32.dll
pysam.py
--------------------
 - Support files for SAM in order to run SAM from a Python call

--------------------
BIRDModel.py
--------------------
- Calcualte the clearsky insolation based on time-of-day and atmospheric parameters


########################################
It also has a number of generic datafiles for use when the MySQL database is not 
available on the local machine

--------------------
clearsky_index_cdf.pkl
--------------------
Cummulative distribution function of the clearsky index based on the hourly clearsky
index from previous analysis of 1-min insolation at the DOE ARM Network

--------------------
clearsky_index_psd.pkl
--------------------
Power spectral density of the clearsky index based on the average hourly 
clearsky index from the DOE ARM Network

########################################

