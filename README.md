# scisca


## Sensor Count In Sensor Community Archive

This (not so) quick and dirty script retrieves the CSV files from the Sensor Community [archive](http://archive.sensor.community) and counts the number of dust sensors for a given date in the specified country.

### step 1
Script retrieves a country boundary rectangle (country boundary box) from Openstreetmap's Nominatim service for the specified iso country code. (eg. hu, de, be or at, etc.)
### step2 
Then it retrieves the list of CSV files from the SC archive for the given date. (this step takes a while)
### step 3
Retrieve each CSV and if the geo coordinate (lat, lon) in the CSV is outside the boundary box the sensor ID gets stored in a file: NOT_IN_RECT_IDS.
To ease the load on the archive the CSVs for these sensor IDs will not be checked for future retrievals for other dates, as we know they're in other country.

This means that the first date takes a lot of time and once we know what to ignore the additional dates are going to be much faster.

(Well, that means that the ID is going to be ignored even if the sensor has moved to the specified country at any later time.)


### step 4
If the coordinate is within the rectangle, script initiates a Nominatim reverse lookup with the lat-lon pair to check the actual country code.
#### step 4.1
If country code is the specified country, it counts and stores the id the data file MY_DATA_FILE.
#### step 4.2
  If country code is not the specified country, it stores the id in NOT_IN_RECT_IDS file.


  __Usage:__ scisca \<iso-county_code\> \<YYYY-MM-DD\>


  __Example:__ scisca hu 2020-09-17
