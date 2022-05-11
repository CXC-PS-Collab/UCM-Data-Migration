# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 14:03:18 2022

@author: ashimis3
"""

#Getting all the Directory Number
import time
from zeep.exceptions import Fault
import os
import sys
sys.path.append("../")
from adapter.appcore import *

start = time.time()

siteCode = ucmSourceContent["siteCode"]

directory = f"../ConfigExports/{siteCode}"

tagfilter = {"pattern": "",
             "routePartitionName": ""}

directoryNumber = ucm_source.get_directory_numbers(tagfilter)
allDirectoryNumber = []
pattern = []
cleanedData = []
# print(directoryNumber)
for dn in directoryNumber:
    tempCleanedData = cleanObject(dn)
    tempCleanedData = {"pattern": tempCleanedData["pattern"],
                       "routePartitionName": tempCleanedData["routePartitionName"]}
    cleanedData.append(tempCleanedData)
    del tempCleanedData

locLen = len(cleanedData)
end = time.time()

write_results(directory, directoryNumber, "minimaldirectorynumber")

if not os.path.exists(directory):
    os.makedirs(directory)

print(f"\nFound {locLen} directory Number in {round(end - start,2)} seconds")

save = 0

for loc in tqdm(cleanedData,
                desc="Loading directory Number",
                ascii=False, ncols=75):
    save += 1
    try:
        try:
            data = ucm_source.get_directory_number(**loc)["return"]["line"]
        except Exception as e:
            print(str(e))

        if type(data) != Fault:
            data = cleanObject(data)
            if "id" in data:
                del data["id"]
            if "sequence" in data:
                del data["sequence"]
            allDirectoryNumber.append(data)

    except Exception as e:
        print("Error while fetching directory Number: " +
              str(loc) + " : " + str(e))

allDirectoryNumber = [cleanObject(entry)
                                    for entry in allDirectoryNumber]
for dn in allDirectoryNumber:
    if "externalPresentationInfo" in dn and dn["externalPresentationInfo"] != None:
        # Expanding _raw_elements
        if "_raw_elements" in dn["externalPresentationInfo"]:
            configsDict = {
                entry.tag: entry.text
                for entry in dn["externalPresentationInfo"]["_raw_elements"]
            }

            del dn["externalPresentationInfo"]["_raw_elements"]
            # print(dn["externalPresentationInfo"])
            # print(type(dn["externalPresentationInfo"]))
            # print(configsDict)
            dn["externalPresentationInfo"].update(configsDict)
write_results(directory, allDirectoryNumber, "directorynumber")
