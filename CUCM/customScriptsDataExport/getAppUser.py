# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 14:18:34 2021

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

tagfilter = {'userid': ''}

appUsers = ucm_source.list_app_user(tagfilter)
allUsers = []
userId = []
cleanedData = []

for aU in appUsers:
    tempCleanedData = cleanObject(aU)
    tempCleanedData = {"userid":tempCleanedData["userid"]}
    cleanedData.append(tempCleanedData)
    del tempCleanedData
    if aU["userid"] not in userId:
        userId.append(aU["userid"])
appU = cleanedData
locLen = len(userId)
end = time.time()

if not os.path.exists(directory):
    os.makedirs(directory)

print(f"\nFound {locLen} Application User in {round(end - start,2)} seconds")

save = 0

for loc in tqdm (appU,
               desc="Loading Application Users",
               ascii=False, ncols=75):
    save += 1
    try:
        try:
            data = ucm_source.get_app_user(**loc)["return"]["appUser"]
        except Exception as e:
            print(str(e))

        if type(data) != Fault:
            data = cleanObject(data)
            if "id" in data:
                del data["id"]
            if "sequence" in data:
                del data["sequence"]
            allUsers.append(data)

    except Exception as e:
        print("Error while fetching App User: "+ str(loc) + " : " + str(e))

write_results(directory, allUsers, "appusers")

