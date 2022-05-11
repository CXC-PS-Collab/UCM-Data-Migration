# -*- coding: utf-8 -*-
"""
Created on Wed April  5 15:12:58 2021

@author: ashimis3
"""

import sys
sys.path.append("../")
import os
from adapter.appcore import *
from zeep.exceptions import Fault
from adapter.appcore import *
import time
from exportConfigs.excelJSONConversion import ConvertToExcel

# def logPrint(msg,msg2="",msg3="",msg4=""):
#     if msg2 != "":
#         msg = str(msg) + " " + str(msg2)
#     if msg3 != "":
#         msg = str(msg) + " " + str(msg3)
#     if msg4 != "":
#         msg = str(msg) + " " + str(msg2)
#     with open(CustomExportLogFile, 'a') as f:
#         ct = datetime.datetime.now()
#         print(ct, ":::", msg, file=f)
#         print(msg)

def allAdvertisedPattern(siteName, directory):
    start = time.time()
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    tagfilter = {'pattern': '', 'description': ''}
    searchCriteria = {'description': f'%{siteName}%'}

    try:
    # #After path append
    #     with open(CustomExportLogFile, 'w') as f:
    #         ct = datetime.datetime.now()
    #         logPrint(ct, ":::", "Process Started",f)

        advPattern = ucm_source.list_advertised_pattern(searchCriteria, tagfilter)
        if not isinstance(advPattern, Exception):
            allAdvPattern = []
            advName = []
            cleanedData = []

            for advP in advPattern:
                tempCleanedData = cleanObject(advP)
                tempCleanedData = {"pattern":tempCleanedData["pattern"]}
                cleanedData.append(tempCleanedData)
                del tempCleanedData
                if advP["pattern"] not in advName:
                    advName.append(advP["pattern"])
            advPattern = cleanedData
            advLen = len(advName)
            end = time.time()

            if not os.path.exists(directory):
                os.makedirs(directory)

            print(f"\nFound {advLen} advPattern in {round(end - start,2)} seconds")

            save = 0

            for advP in tqdm (advPattern,
                        desc="Loading Advertised Patterns...",
                        ascii=False, ncols=75):
                save += 1
                try:
                    try:
                        data = ucm_source.get_advertised_pattern(**advP)["return"]["advertisedPatterns"]
                    except Exception as e:
                        print(str(e))

                    if type(data) != Fault:
                        data = cleanObject(data)
                        if "id" in data:
                            del data["id"]
                        if "sequence" in data:
                            del data["sequence"]
                        allAdvPattern.append(data)

                except Exception as e:
                    print("Error while fetching Advertised Patterns: "+ str(advP) + " : " + str(e))


            print("Closing Processes...")
            write_results(directory, allAdvPattern, siteName)

            # if not os.path.exists(directory):
            #     os.makedirs(directory)
            # write_results(directory, allUsers, "allUsers")
        else:
            print("No Advertised Patterns found for: "+ str(siteName))

    except Exception as e:
        traceback.print_exc()

def driver():
    FolderName = ucmSourceContent["siteCode"]
    try:
        directory = os.path.join(CORE_PATH, 'ConfigExports', FolderName)
    except:
        directory = f"../ConfigExports/{FolderName}"
    
    siteCodes = ucmSourceContent["dataFilterJSONKeys"]#input("Enter sitecodes separated by comma: ").split(",")
    temp = []
    for site in siteCodes:
        site = site.strip()
        if site == "":
            pass
        else:
            temp.append(site)
    siteCodes = temp
    for site in siteCodes:
        try:
            allAdvertisedPattern(site, directory)
        except Exception as e:
            print(f"Error Occurred for- {site}- {str(e)}")
    ConvertToExcel([FolderName])

driver()