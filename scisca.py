#!/usr/bin/env python3
#
# SCISCA - Sensor Count In Sensor Community Archive
#
# Retrieves Country boundary rectangle from openstreetmap's Nominatim service
# and retrieves CSV files from the SC archive to check a station's geo coordinate.
# If the coordinate is outside the area, the id gets stored in a file: NOT_IN_RECT_IDS
# If the coordinate is within the rectangle, script initiates a Nominatim reverse lookup
# with the lat-lon pair for the country code.
#
#   If country code is the specified country, it counts and stores the id in the
#    data file MY_DATA_FILE.
#	If country code is not the specified country, it stores the id in NIR file.
#
#  Usage: scisca <iso-county_code> <YYYY-MM-DD>
#
#  Example: scisca hu 2020-09-17

import os
import requests
import re
import json
import sys
from pathlib import Path

DEL = "," # list delimiter
FILE_PATH = "sc/" # Has to end with a slash
FILE_NAME = "data.csv"
MY_DATA_FILE = Path(f"{FILE_PATH}{FILE_NAME}")
RECT_REQ = "https://nominatim.openstreetmap.org/search.php?q="
RECT_XY = [ # Lat Lon of the rectangle around Hungary 45.737128, 48.585257, 16.1138866, 22.8977094
	45.737128, 48.585257, # coordinate X
	16.1138866, 22.8977094  # coordinate Y
]
# TEST_LATLON = [46.076,18.372]
NOT_IN_RECT_IDS = "nirids.csv" # list of those IDs that are not within the rectangle
ROOT_URL = "http://archive.sensor.community/" # Has to end with a slash
DAYS = [6, 19] # Days of month, on which we request the data files
NOMI_URL = "https://nominatim.openstreetmap.org/reverse.php" # add lat=XX&lon=YY&zoom=3&format=jsonv2
DATES = [f"2019-{str(month).zfill(2)}-{str(day).zfill(2)}" for month in range(1, 13) for day in DAYS]     # {YEAR}-month-{DAYS} days in every month of the year
COUNTRY = "hu"


def get_country_boundaries(country):
	global RECT_XY
	country_json = 0
	req_string = f"{RECT_REQ}{country}&format=jsonv2"
	try:
		country_response = requests.get(req_string)
	except:
		print(f"[ERROR] Nominatim request failed for \"{country}\"\.")
		return
	nomi = country_response.json()
	RECT_XY = [float(i) for i in nomi[0]["boundingbox"]]
	print(f"[OK] Bounding box for {country.upper()} is set to {RECT_XY}")
	return

def get_lat_lon(my_file_url):  # id: result[0], lat: result[1], lon: result[2]
	sensor_data_file = ""
	try:
		sensor_data_file = requests.get(my_file_url).text
	except:
		print(f"[WARNING] Request failed for \"{datedir}\"\. Folder is either not accessible or does not exist. Skipping \"{date}\"")
		return
	location_result = sensor_data_file.split("\n")[1].split(";")  # take only the first [1] line after the header in the file and split to fields
	location_result = [location_result[i] for i in range(len(location_result)) if i in [0, 3, 4]]   # columns: #0: sensor_id, #3: lat, #4: lon
	return location_result

def nominatim_lookup(my_lat, my_lon, *args): # Nominatim reverse lookup> lat,lon --> country
	my_nomi_request = f"{NOMI_URL}?lat={my_lat}&lon={my_lon}&zoom=3&format=jsonv2"
	nomi_result = 0
	try:
		nomi_result = requests.get(my_nomi_request).text
	except:
		print(f"[ERROR] Nominatim request {my_nomi_request} failed.")
		return
	nomi = json.loads(str(nomi_result))
#	print(nomi["address"]["country_code"])
	try:
		return str(nomi["address"]["country_code"])
	except:
		print(f"[WARNING] Nominatim reverse lookup did not return a country_code for {my_lon},{my_lat}")
		return

def get_nirids(): # read previously logged Not-In-Range ids into nir_ids
	nir_file = 0
	try:
		nir_file = open(f"{FILE_PATH}{COUNTRY}_{NOT_IN_RECT_IDS}", "r")
	except:
		print(f"[WARNING] Can't open Not-In-Range (NIR) file {FILE_PATH}{COUNTRY}_{NOT_IN_RECT_IDS}")
		result = []
		return result
	nir_result = []
	for line in nir_file:
		nir_result.append(line.split(","))
	nir_file.close()
	nir_result = [nir_result[i][1] for i in range(len(nir_result))]
	print(f"[OK] NIR file loaded: {len(nir_result)} IDs")
#	print(result)
	return nir_result

def get_data(date):
	HU_COUNT = 0
	datedir = f"{ROOT_URL}{date}/"
	print(f"[OK] Processing folder \"{date}\". Waiting for archive response...")
	try:
		sensor_csv_files = requests.get(datedir).text # Getting the file list
	except:
		print(f"[WARNING] Request failed for \"{datedir}\"\. Folder is either not accessible or does not exist. Skipping \"{date}\"")
		return
	match = re.findall("href=\"(.+?_(?:sds011|sps30|pms\d003|ppd42ns|hpm)_sensor_(\d+)(?:_indoor)?\.csv)\">", sensor_csv_files) # Get file names and ids in a list, RE groups
	print(f"[OK] Found {len(match)} dust sensors")
	get_country_boundaries(COUNTRY)
	nir_ids = get_nirids()  # read previously logged Not-In-Range ids into nir_ids
	with open(f"{FILE_PATH}{FILE_NAME}", "a") as hu_datafile, open(f"{FILE_PATH}{COUNTRY}_{NOT_IN_RECT_IDS}", "a") as nirfile:
		print(f"[OK] Reading files in folder \"{date}\"...")
		for i in range(len(match)):
#			if i > 20: break                  # max amount of data in a day. For testing only, comment this out if you need all
			if match[i][1] in nir_ids: continue     # nir_ids to be created yet
			sensor_file = match[i][0]
			location_result = 0                 # to make sure the variable exists even after get_lat_lon fails
			location_result = get_lat_lon(datedir + sensor_file)
			lat = 0.0
			lon = 0.0
			try:
				lat = float(location_result[1])
				lon = float(location_result[2])
			except:
				print(f"\n[WARNING] id:{location_result[0]}: lat \"{location_result[1]}\" or lon \"{location_result[2]}\" could not be converted to float")
				continue # skip to next file
			percentage = round(i / len(match) * 10000)/100
			if not (RECT_XY[0] <= lat <= RECT_XY[1] and RECT_XY[2] <= lon <= RECT_XY[3]):
				print(f"[OK] {percentage}%\t{i}/{len(match)}\tid [{location_result[0]}] is outside of the defined area, adding to NIR file   ", end="\r", flush=True)
				nirfile.write(DEL.join([date]+location_result) + "\n")
				continue # skip to next file

			print(f"[OK] {percentage}%\t{i}/{len(match)}\tid [{location_result[0]}] is in the area.\tCountry lookup:", end = " ")
			nomi_country = nominatim_lookup(lat, lon)
			if nomi_country == COUNTRY:
				print(f"{nomi_country}               ")
				HU_COUNT += 1
				hu_datafile.write(DEL.join([date]+location_result+[nomi_country]) + "\n")
				hu_datafile.flush()  # to write to file immediately
			else:
				print(f"{nomi_country}, adding to NIR file")
				nirfile.write(DEL.join([date]+location_result+[nomi_country]) + "\n")
		print(f"\n[OK] Finished reading date \"{date}\", found {HU_COUNT} sensors in {country}.")

def main():
	global COUNTRY
	current_path = os.getcwd()
	if not os.path.exists(FILE_PATH):
		print(f"[OK] Creating data folder {current_path}/{FILE_PATH}")
		os.mkdir(FILE_PATH)
	if MY_DATA_FILE.is_file():
		pass
	else:
		with open(MY_DATA_FILE, "w") as file:
			file.write(f"date{DEL}id{DEL}lat{DEL}lon{DEL}country\n")
			print(f"[INFO] Creating data file: {MY_DATA_FILE}") # test before replace file open in get_data
#	for date in DATES:			# run through all dates in DATES
#		get_data(date)
#	get_data("2019-06-19")     # to test a specific date

	if len(sys.argv) <= 2:
		print(f"usage: {sys.argv[0]} <iso-county_code> <YYYY-MM-DD>")
	else:
		COUNTRY = sys.argv[1]
		get_data(sys.argv[2])

if __name__ == "__main__":
    main()
