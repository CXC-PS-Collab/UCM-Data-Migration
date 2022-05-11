# -*- coding: utf-8 -*-
"""
Created on Tue Nov 25 14:18:34 2021

@author: ashimis3
"""

# -*- coding: utf-8 -*-
#Getting all the callPickupGroup
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

callPickupGroups = ucm_source.get_call_pickup_groups(tagfilter)
allCallPickupGroups = []
cpgName = []
cleanedData = []

for cpg in callPickupGroups:
    tempCleanedData = cleanObject(cpg)
    tempCleanedData = {"name":tempCleanedData["name"]}
    cleanedData.append(tempCleanedData)
    del tempCleanedData
    if cpg["name"] not in cpgName:
        cpgName.append(cpg["name"])
cPGs = cleanedData
locLen = len(cpgName)
end = time.time()

if not os.path.exists(directory):
    os.makedirs(directory)

print(f"\nFound {locLen} call pickup groups in {round(end - start,2)} seconds")

save = 0

for loc in tqdm (cPGs,
               desc="Loading call pickup group",
               ascii=False, ncols=75):
    save += 1
    try:
        try:
            data = ucm_source.get_call_pickup_group(**loc)["return"]["callPickupGroup"]
        except Exception as e:
            print(str(e))

        if type(data) != Fault:
            data = cleanObject(data)
            if "id" in data:
                del data["id"]
            if "sequence" in data:
                del data["sequence"]
            allCallPickupGroups.append(data)

    except Exception as e:
        print("Error while fetching call pickup groups: "+ str(loc) + " : " + str(e))

write_results(directory, allCallPickupGroups, "callpickupgroup")

