# -*- coding: utf-8 -*-
"""
Created on Tue Nov 23 17:18:34 2021

@author: ashimis3
"""

# -*- coding: utf-8 -*-
#Getting all the locations -
import sys
sys.path.append("../")
import os
from zeep.exceptions import Fault
from adapter.appcore import *

import time

start = time.time()

siteCode = ucmSourceContent["siteCode"]

directory = f"../ConfigExports/{siteCode}"

tagfilter = {'name': ''}

locations = ucm_source.get_locations(tagfilter)
allLocations = []
locName = []
cleanedData = []

for loc in locations:
    tempCleanedData = cleanObject(loc)
    tempCleanedData = {"name":tempCleanedData["name"]}
    cleanedData.append(tempCleanedData)
    del tempCleanedData
    if loc["name"] not in locName:
        locName.append(loc["name"])
locations = cleanedData
locLen = len(locName)
end = time.time()

if not os.path.exists(directory):
    os.makedirs(directory)

print(f"\nFound {locLen} locations in {round(end - start,2)} seconds")

save = 0

for loc in tqdm (locations,
               desc="Loading locations…",
               ascii=False, ncols=75):
    save += 1
    try:
        try:
            data = ucm_source.get_location(**loc)["return"]["location"]
        except Exception as e:
            print(str(e))

        if type(data) != Fault:
            data = cleanObject(data)
            if "id" in data:
                del data["id"]
            if "sequence" in data:
                del data["sequence"]
            allLocations.append(data)

    except Exception as e:
        print("Error while fetching location: "+ str(loc) + " : " + str(e))



write_results(directory, allLocations, "alllocations")

# if not os.path.exists(directory):
#     os.makedirs(directory)
# write_results(directory, allUsers, "allUsers")
