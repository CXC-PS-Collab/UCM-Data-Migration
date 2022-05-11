# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 14:18:34 2021

@author: ashimis3
"""

# -*- coding: utf-8 -*-
#Getting all the Service Parameter
import sys
sys.path.append("../")
import os
from zeep.exceptions import Fault
from adapter.appcore import *

import time

start = time.time()

siteCode = ucmSourceContent["siteCode"]

directory = f"../ConfigExports/{siteCode}"

serviceParams = ucm_source.get_service_parameters()
allServiceParams = []
cpgData = []
cleanedData = []

for sP in serviceParams:
    tempCleanedData = cleanObject(sP)
    tempCleanedData = {"processNodeName":tempCleanedData["processNodeName"],"name":tempCleanedData["name"],"service":tempCleanedData["service"]}
    if tempCleanedData not in cleanedData:
        cleanedData.append(tempCleanedData)
serviceParams = cleanedData
locLen = len(serviceParams)
end = time.time()

if not os.path.exists(directory):
    os.makedirs(directory)

print(f"\nFound {locLen} Service Parameters in {round(end - start,2)} seconds")

save = 0

for loc in tqdm (serviceParams,
               desc="Loading service Parameters..",
               ascii=False, ncols=75):
    save += 1
    try:
        try:
            data = ucm_source.get_service_parameter(**loc)["return"]["serviceParameter"]
        except Exception as e:
            print(str(e))

        if type(data) != Fault:
            data = cleanObject(data)
            if "id" in data:
                del data["id"]
            if "sequence" in data:
                del data["sequence"]
            allServiceParams.append(data)

    except Exception as e:
        print("Error while fetching Service Parameters: "+ str(loc) + " : " + str(e))

write_results(directory, allServiceParams, "serviceparameter")

