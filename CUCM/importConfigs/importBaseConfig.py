import datetime
from sys import exit
import os
from lxml import etree
import json
from collections import OrderedDict
from zeep.helpers import serialize_object
from zeep.exceptions import Fault
import sys
import requests
from requests.auth import HTTPBasicAuth
import traceback
from zeep import exceptions
import copy
sys.path.append("../")
from adapter.appcore import *


# import logging
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG) # process everything, even if everything isn't logPrinted
# fh = logging.FileHandler('importLogs.log')
# fh.setLevel(logging.DEBUG) # or any level you want
# logger.addHandler(fh)
#For phone button template changing minOccurs for basephonetemplate to 0
# Line no. 10791 in AXLSoap.xsd
# <xsd:element maxOccurs="1" minOccurs="0" name="basePhoneTemplateName" type="axlapi:XFkType"/>

ExceptionList = []
catchExceptionWords = ["exception", "error", "failed", "axl", "fault", "zeep", "Item not valid"]
Sites = IMPORT_SITES

#Deleting Log Files
#Creating Log Folder
logFolder = "logs/"+Sites[0] + "/"
os.makedirs("logs", exist_ok=True)

os.makedirs(logFolder, exist_ok=True)
sampleLogs = logFolder + Sites[0] +'-logs.txt'
errorLogs = logFolder + Sites[0] +'-logs-error.txt'
statLogs = logFolder + Sites[0] +'-stats.txt'

with open(sampleLogs, 'w') as f:
    ct = datetime.datetime.now()
    print(ct, ":::", "Process Started", file=f)

with open(errorLogs, 'w') as f:
    ct = datetime.datetime.now()
    print(ct, ":::", "Process Started", file=f)

with open(statLogs, 'w') as f:
    ct = datetime.datetime.now()
    print(ct, ":::", "Process Started", file=f)


def logPrint(msg, stat = False):
    #Currently support name of one site only
    if stat:
        with open(statLogs, 'a') as f:
            print(msg, file=f)
        return
    with open(sampleLogs, 'a') as f:
        ct = datetime.datetime.now()
        #Logging errors in separate file
        if any(err in str(msg).lower() for err in catchExceptionWords):
            with open(errorLogs, 'a') as ef:
                print(ct, ":::", msg, file=ef)
            # print(msg)

        print(ct, ":::", msg, file=f)
        # Commenting Message Printing
        # print(msg)



def removeKeys(datafieldsvalue, data):
    dataDict = copy.deepcopy(datafieldsvalue)
    for remove in dataDict["headersToRemove"]:
        if type(remove) == list:
            if type(data) == list and isinstance(data[0],dict):
                for val in data:
                    if remove[0] in val:
                        if len(remove) == 1:
                            del val[remove[0]]
                        else:
                            keyToRemove = remove.pop(0)
                            val[keyToRemove] = removeKeys({"headersToRemove":remove}, val[keyToRemove])
            elif data == None:
                break
            if remove[0] in data:
                if len(remove) == 1:
                    del data[remove[0]]
                else:
                    keyToRemove = remove.pop(0)
                    data[keyToRemove] = removeKeys({"headersToRemove":[remove]}, data[keyToRemove])
        elif data == None:
            break
        elif remove in data:
            del data[remove]
            ## Exception for MRGL
    if "file" in dataDict and dataDict["file"] == "mediaresourcegrouplist.json":
        data["members"] = []
    # if "name" in data and data["name"] == "bmara00_EMP":
    #     print(data)
    return data


def cleanObject(data):
    if data != None:
        if type(data) != str:
            dictData = dict(serialize_object(data))
            returnedDict = dictData
            if "uuid" in dictData:
                del dictData["uuid"]
            for key, value in dictData.items():
                if type(value) == str:
                    continue
                elif type(value) == OrderedDict:
                    if "_value_1" in value.keys():
                        returnedDict[key] = value["_value_1"]
                    else:
                        returnedDict[key] = cleanObject(value)
                elif type(value) == list:
                    tempdataList = []
                    for entries in value:
                        tempdataList.append(cleanObject(entries))
                    returnedDict[key] = tempdataList
            return returnedDict
        else:
            return data
    else:
        # logPrint(data)
        if type(data) == str:
            return data


status = []
def updateConfigs(ConfigPath, dynamicLogicJson):
    for datafieldskey, datafieldsvalue in dynamicLogicJson.items():
        GLOBAL_PAUSE = True

        while(GLOBAL_PAUSE):
            count = already = failed = succeed = 0
            if "exception" not in datafieldsvalue:
                filename = f"{ConfigPath}/{datafieldskey}.json"
                try:
                    dataentries = json.load(open(filename))
                    logPrint(f"Adding {datafieldskey}")
                    print(f"\nAdding {datafieldskey}")
                except Exception as e:
                    # print(str(e))
                    GLOBAL_PAUSE = False
                    continue
                try:
                    resp = getattr(ucm_destination.client, "list"+datafieldskey)(
                        datafieldsvalue[0], returnedTags=datafieldsvalue[1]
                    )
                except Fault as e:
                    resp = str(e)
                    print(resp)

                if type(resp) != Fault and resp["return"] != None:
                    nameListDest = [ entity[datafieldsvalue[3]] for entity in resp["return"][datafieldsvalue[2]]]
                    tempData = []
                    for entity in dataentries:
                        if entity[datafieldsvalue[3]] not in nameListDest:
                            tempData.append(entity)
                    print(f"Found {len(tempData)} new data items for {datafieldskey}")
                    dataentries = tempData

                count = len(dataentries)
                dataentries = tqdm(dataentries)
                for entry in dataentries:
                    cleanedInput = cleanObject(entry)
                    PAUSE = True
                    while(PAUSE == True):
                        try:
                            if len(datafieldsvalue) < 5:
                                datafieldsvalue.append([])
                            #Removing keys per entry in entries
                            cleanedInput = removeKeys({"headersToRemove":datafieldsvalue[4]}, cleanedInput)
                        except Exception as removeExe:
                            print(removeExe)
                            logPrint(f"Cannot remove any header: {removeExe}")
                            traceback.print_exc()

                            failed += 1
                            dataentries.set_description(f"Processing {datafieldskey} : Failed Header : {cleanedInput[datafieldsvalue[4]]} :")
                            if STOP_IMPORT_PAUSE:
                                PAUSE = False
                                continue

                            In = input("\n Error Occured, Want to retry? (y/n): ")
                            if In == "n" or In == "N":
                                PAUSE = False
                            continue
                        try:
                            try:
                                resp = getattr(ucm_destination.client, "add"+datafieldskey)(
                                    cleanedInput
                                )
                            except Fault as e:
                                resp = str(e)
                                # print("Responser",resp)
                            if "duplicate" in str(resp) or "exists" in str(resp) or "Uniqueness check" in str(resp):#or "Uniqueness check" in str(resp):
                                logPrint(
                                    f"{cleanedInput[datafieldsvalue[3]]} already exist"
                                )
                                already += 1
                                PAUSE = False
                                dataentries.set_description(f"Processing {datafieldskey} : Duplicate : {cleanedInput[datafieldsvalue[3]]} :")
                                continue
                            elif type(resp) == Fault or "return" not in str(resp):
                                if "User Id" in str(resp):
                                    logPrint(
                                        f"Exception occured: {resp} : userId- {cleanedInput['ownerUserName']} : while adding: {cleanedInput[datafieldsvalue[3]]} : {str(resp)}"
                                    )
                                else:
                                    logPrint(
                                        f"Exception occured: {resp} while adding: {cleanedInput[datafieldsvalue[3]]} : {str(resp)}"
                                    )
                                failed += 1
                                dataentries.set_description(f"Processing {datafieldskey} : Failed : {cleanedInput[datafieldsvalue[3]]} :")
                                if STOP_IMPORT_PAUSE:
                                    PAUSE = False
                                    continue
                                In = input("\n Error Occured, Want to retry? (y/n): ")
                                if In == "n" or In == "N":
                                    PAUSE = False
                                continue
                            else:
                                # print(resp)
                                logPrint(
                                    f"added {cleanedInput[datafieldsvalue[3]]}")
                                succeed += 1
                                PAUSE = False
                                dataentries.set_description(f"Processing {datafieldskey} : Added : {cleanedInput[datafieldsvalue[3]]} :")

                        except Exception as ex:
                            failed += 1
                            logPrint(
                                "Error in "+datafieldsvalue["file"]+" -Exception in AXL Request: "+str(ex))
                            dataentries.set_description(f"Processing {datafieldskey} : Major Issue : {cleanedInput[datafieldsvalue[3]]} :")
                            if STOP_IMPORT_PAUSE:
                                PAUSE = False
                            else:
                                In = input("\n Error Occured, Want to retry? (y/n): ")
                                if In == "n" or In == "N":
                                    PAUSE = False

                #Statistics count
                integrity = count == (failed + succeed + already)

                statStr = "\n"+"*"*50
                statStr += "\nFound "+str(count)+" "+str(datafieldskey)
                statStr += "\nAlready Exists: "+str(already)
                statStr += "\nFailed: "+str(failed)
                statStr += "\nSucceed: "+str(succeed)
                statStr += "\nIntegrity Check: "+str(integrity)+"\n"
                statStr += "*"*50
                status.append(statStr)
                dataentries.set_description(f"Processing {datafieldskey} : Process Halted")
                if STOP_IMPORT_PAUSE:
                    GLOBAL_PAUSE = False
                else:
                    In = input(f"\n Completed  {datafieldskey}. Want to continue (Y) or retry (N) (y/n): ")
                    if In == "y" or In == "Y":
                        GLOBAL_PAUSE = False
            # else:
            #     if datafieldsvalue["file"] == "gatewayports.json":
            #         #Pending for modification
            #         filename = f"{ConfigPath}/{datafieldsvalue['file']}"
            #         if os.path.exists(filename):
            #             logPrint("Adding gateway ports")
            #             dataentries = json.load(open(filename))
            #             if addGatewayPorts(dataentries):
            #                 logPrint("Gateway Ports Added")
            #             else:
            #                 logPrint("Error occured while adding Ports")
            #         if STOP_IMPORT_PAUSE:
            #             GLOBAL_PAUSE = False
            #         else:
            #             In = input(f"\n Completed  {datafieldskey}. Want to continue (Y) or retry (N) (y/n): ")
            #             if In == "y" or In == "Y":
            #                 GLOBAL_PAUSE = False
            #     else:
            #         GLOBAL_PAUSE = False


importLogicContent = IMPORT_LOGIC_BASE

## iterate over each site folder and push the configurations
for site in Sites:
    #CUCM Connectivity check
    if not ucm_destination.check_cucm():
        print("CUCM AXL Connectivity issue: \n\t1. Check Credentials\n\t2. Check AXL Connectivity\n\t3. Check Account locked status.")
        exit()
    directory = f"../ConfigExports/{site}"
    logPrint(directory)
    if os.path.exists(directory):
        logPrint(
            f"Starting Import for Site: {site} on CUCM: {ucmDestinationContent['cucm']}"
        )
        try:
            userAccept = input("Do you want to proceed (Y/n)? ")
        except KeyError:
            logPrint("Invalid input. Existing..")
            exit()
        else:
            if userAccept == "Y" or userAccept == "y":
                try:
                    updateConfigs(directory, importLogicContent)
                except Exception as importExe:
                    logPrint(f"Error Occured while Importing: {importExe}")
                else:
                    logPrint(
                        f"Data Import completed for site: {site}. Proceeding...")
            else:
                logPrint("Invalid response received. Exiting...")
                exit()
    else:
        logPrint(f"Error: {site} - Directory does not exists.")

for stats in status:
    logPrint(stats, True)
