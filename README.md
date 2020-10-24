# scisca
Sensor Count In Sensor Community Archive

Retrieves Country boundary rectangle from openstreetmap's Nominatim service
and retrieves CSV files from the SC archive to check a station's geo coordinate.

If the coordinate is outside the area, the id gets stored in a file: NOT_IN_RECT_IDS

If the coordinate is within the rectangle, script initiates a Nominatim reverse lookup
with the lat-lon pair for the country code.

  If country code is the specified country, it counts and stores the id the data file MY_DATA_FILE.

  If country code is not the specified country, it stores the id in NIR file.


  Usage: scisca \<iso-county_code\> \<YYYY-MM-DD\>


  Example: scisca hu 2020-09-17
