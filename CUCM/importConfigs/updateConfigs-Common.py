import datetime
from sys import exit
import os
from lxml import etree
import json
from collections import OrderedDict
from zeep.helpers import serialize_object
import pandas as pd
from zeep.exceptions import Fault
import requests
import sys
import copy

from zeep import exceptions

sys.path.append("../")
from adapter.appcore import *

# Index

# Update MRGL
# Update CTIRP
# Update Device Pool
# Update DN Partition
# Update Phone
# Update Gateway
# Update Users
# changeDnPartition

# import logging
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG) # process everything, even if everything isn't logPrinted
# fh = logging.FileHandler('importLogs.log')
# fh.setLevel(logging.DEBUG) # or any level you want
# logger.addHandler(fh)

ExceptionList = []
catchExceptionWords = ["exception", "error", "failed", "axl", "fault", "zeep",  "Item not valid"]

Sites = IMPORT_SITES


#Deleting Log Files
#Creating Log Folder
os.makedirs("logs", exist_ok=True)

logFolder = "logs/"+Sites[0] + "/"
os.makedirs(logFolder, exist_ok=True)
sampleLogs = logFolder + Sites[0]+'-update-logs.txt'
errorLogs = logFolder + Sites[0]+'-update-logs-error.txt'
with open(sampleLogs, 'w') as f:
    ct = datetime.datetime.now()
    print(ct, ":::", "Process Started", file=f)

with open(errorLogs, 'w') as f:
    ct = datetime.datetime.now()
    print(ct, ":::", "Process Started", file=f)


def logPrint(msg):
    #Currently support name of one site only

    with open(sampleLogs, 'a') as f:
        ct = datetime.datetime.now()
        #Logging errors in separate file
        if any(err in str(msg).lower() for err in catchExceptionWords):
            with open(errorLogs, 'a') as ef:
                print(ct, ":::", msg, file=ef)

        print(ct, ":::", msg, file=f)
        print(msg)


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
            elif remove[0] in data:
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
    # if "file" in dataDict and dataDict["file"] == "mediaresourcegrouplist.json":
    #     data["members"] = []
    # if "name" in data and data["name"] == "bmara00_EMP":
    #     print(data)
    return data



def updateMRGL(mrgldata, datafieldsvalue):
    result = []
    for mgrl in mrgldata:
        cleanedInput = cleanObject(mgrl)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        try:
            resp = ucm_destination.update_media_resource_group_list(
                name=cleanedInput["name"], members=cleanedInput["members"]
            )
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating MRGL: "+cleanedInput["name"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {cleanedInput['name']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            logPrint(ex)
    if all(result):
        return True
    else:
        return False

def updateMRG(mrgdata, datafieldsvalue):
    result = []
    for mgr in mrgdata:
        cleanedInput = cleanObject(mgr)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        try:
            resp = ucm_destination.update_media_resource_group(
                name=cleanedInput["name"], members=cleanedInput["members"]
            )
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating MRGL: "+cleanedInput["name"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {cleanedInput['name']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            logPrint(ex)
    if all(result):
        return True
    else:
        return False


def updateCtiRp(ctiRpData, datafieldsvalue):
    result = []
    #Keywords to remove for successful update (Added Master method to remove for reference)
    keyWords = ["model", "product", "class"]
    for ctiRp in ctiRpData:
        cleanedInput = cleanObject(ctiRp)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
            ctiRp = cleanedInput
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        for header in keyWords:
            if header in ctiRp:
                del ctiRp[header]
        try:
            #Calling AXL after cleaning data
            resp = ucm_destination.update_cti_route_point(**ctiRp)
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating ctiRp: "+ctiRp["name"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {ctiRp['name']}")
                result.append(True)
        except Exception as ex:
            # Needs to change for updating multiple CTI RP
            result.append(False)
            logPrint("Error occured while updating CTI RP "+str(ctiRp['name']))
            logPrint("Detailed error- "+str(ex))
    if all(result):
        return True
    else:
        return False


def updateDP(dpData, datafieldsvalue):
    result = []
    for dp in dpData:
        #Keywords to remove for successful update (Added Master method to remove for reference)
        # keyWords = ["model","product","class"]
        # for header in keyWords:
        #     if header in dp:
        #         del dp[header]
        cleanedInput = cleanObject(dp)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        try:
            resp = ucm_destination.update_device_pool(**cleanedInput)
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating device pool: "+dp["name"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {cleanedInput['name']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            logPrint(str(ex))
    if all(result):
        return True
    else:
        return False


def updatePhone(phoneData, datafieldsvalue):
    result = []
    for pd in phoneData:
        #Keywords to remove for successful update (Added Master method to remove for reference)
        # keyWords = ["model","product","class"]
        # for header in keyWords:
        #     if header in dp:
        #         del dp[header]
        cleanedInput = cleanObject(pd)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        try:
            #Removing mrgl for REMOVE_MRGL_FROM_DEVICE - One Time Patch, Not needed in Future- Customer Specific
            if REMOVE_MRGL_FROM_DEVICE:
                if "mediaResourceListName" in cleanedInput and cleanedInput["mediaResourceListName"] != None:
                    cleanedInput["mediaResourceListName"] = ""

            resp = ucm_destination.update_phone(**cleanedInput)
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating phone: "+pd["name"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {cleanedInput['name']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            logPrint("Error in updating phone: "+pd["name"]+" "+str(ex))
    if all(result):
        return True
    else:
        return False

def updateGateway(gatewayData, datafieldsvalue):
    result = []
    for pd in gatewayData:
        #Keywords to remove for successful update (Added Master method to remove for reference)
        # keyWords = ["model","product","class"]
        # for header in keyWords:
        #     if header in dp:
        #         del dp[header]
        #Getting only desired key
        updateKeys = ["domainName", "newDomainName", "description", "product", "protocol","callManagerGroupName","vendorConfig"]
        tempPd = {}
        for key in updateKeys:
            if key in pd:
                tempPd[key] = pd[key]

        pd = tempPd

        cleanedInput = cleanObject(pd)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        try:
            resp = ucm_destination.update_gateway(**cleanedInput)
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating Gateway: "+pd["domainName"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {cleanedInput['domainName']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            logPrint("Error in updating Gateway: "+pd["domainName"]+" "+str(ex))
    if all(result):
        return True
    else:
        return False


def updateUsers(userData, datafieldsvalue):
    result = []
    for user in userData:
        #Keywords to remove for successful update (Added Master method to remove for reference)
        # keyWords = ["model","product","class"]
        # for header in keyWords:
        #     if header in dp:
        #         del dp[header]
        #Getting only desired key
        # updateKeys = ["domainName", "newDomainName", "description", "product", "protocol","callManagerGroupName","vendorConfig"]
        # tempPd = {}
        # for key in updateKeys:
        #     if key in pd:
        #         tempPd[key] = pd[key]

        # pd = tempPd

        cleanedInput = cleanObject(user)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        try:
            resp = ucm_destination.update_user(**cleanedInput)
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating User: "+user["userid"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {cleanedInput['userid']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            logPrint("Error in updating User: "+user["userid"]+" "+str(ex))
    if all(result):
        return True
    else:
        return False


def changeDnPartition(dnData, datafieldsvalue):
    result = []
    for index, row in dnData.iterrows():
        try:
            e164AltNum = {"advertiseGloballyIls": row[3]}
            resp = ucm_destination.update_line(
                pattern=row[0], routePartitionName=row[1], newRoutePartitionName=row[2],e164AltNum= e164AltNum )
            logPrint("Modified DN: "+str(row[0]))
        except Exception as ex:
            result.append(False)
            logPrint("DN Change Partition failed for- " +
                     str(row[0])+" : Error: "+str(ex))
    if all(result):
        return True
    else:
        return False

def updateDirn(dirnData, datafieldsvalue):
    result = []
    count = 0
    for dirn in dirnData:
        #Keywords to remove for successful update (Added Master method to remove for reference)
        # keyWords = ["model","product","class"]
        # for header in keyWords:
        #     if header in dp:
        #         del dp[header]
        #Getting only desired key
        # updateKeys = ["domainName", "newDomainName", "description", "product", "protocol","callManagerGroupName","vendorConfig"]
        # tempPd = {}
        # for key in updateKeys:
        #     if key in pd:
        #         tempPd[key] = pd[key]

        # pd = tempPd
        cleanedInput = cleanObject(dirn)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        try:

            if isinstance(cleanedInput.get("enterpriseAltNum", None), dict) or cleanedInput.get("usage", None) == "Device Intercom":
                if cleanedInput.get("usage", None) == "Device Intercom":
                    pass
                elif "numMask" in cleanedInput["enterpriseAltNum"] and isinstance(cleanedInput["enterpriseAltNum"]["numMask"],str):
                    pass
                else:
                    continue
            if "usage" in cleanedInput:
                del cleanedInput["usage"]
            count += 1
            resp = ucm_destination.update_line(**cleanedInput)
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating Directory Number: "+dirn["pattern"]+" "+dirn["routePartitionName"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {cleanedInput['pattern']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            logPrint("Error in updating Directory Number: "+dirn["pattern"]+" "+dirn["routePartitionName"]+" "+str(ex))
    print("Updated- ",count,"DNs")
    if all(result):
        return True
    else:
        return False


def updateCSS(cssData, datafieldsvalue):
    result = []
    for css in cssData:
        cleanedInput = cleanObject(css)
        try:
            #Removing keys per entry in entries
            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
        except Exception as removeExe:
            logPrint(f"Cannot remove any header: {removeExe}")
            continue
        try:
            resp = ucm_destination.update_calling_search_space(**cleanedInput)
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                logPrint("Error in updating CSS: "+css["name"]+" "+str(resp))
                continue
            else:
                logPrint(f"updated {cleanedInput['name']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            logPrint("Error in updating Directory Number: "+css["name"]+" "+str(ex))
    if all(result):
        return True
    else:
        return False


def updateConfigs(ConfigPath, dynamicLogicJson):
    for datafieldskey, datafieldsvalue in dynamicLogicJson.items():
        if "exception" in datafieldsvalue.keys():
            ## Updating MRGL Members:
            if datafieldsvalue["file"] == "mediaresourcegrouplist.json" and UPDATE_MRGL:
                logPrint(f"{datafieldskey} members")
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = json.load(open(filename))
                    if updateMRGL(dataentries, datafieldsvalue):
                        logPrint("All MRGL Updated")
                    else:
                        logPrint("Error occured while updating mrgl.")

            elif datafieldsvalue["file"] == "ctiroutepoint.json":
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = json.load(open(filename))
                    if updateCtiRp(dataentries, datafieldsvalue):
                        logPrint("CTI Route points Updated")
                    else:
                        logPrint("Error occured while updating CTI RP")

            elif datafieldsvalue["file"] == "devicepool.json" and UPDATE_DEVICE_POOL:
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = json.load(open(filename))
                    if updateDP(dataentries, datafieldsvalue):
                        logPrint("All Device Pool Updated")
                    else:
                        logPrint("Error occured while updating devicePool.")

            elif datafieldsvalue["file"] == "directorynumber.json" and UPDATE_DIRN:
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = json.load(open(filename))
                    if updateDirn(dataentries, datafieldsvalue):
                        logPrint("All Directory Number Updated")
                    else:
                        logPrint("Error occured while updating Directory Number.")

            elif datafieldsvalue["file"] == "changepartition.csv":
                #CSV File to Dataframe
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = pd.read_csv(filename)
                    if changeDnPartition(dataentries, datafieldsvalue):
                        logPrint(
                            "All DN Change Partition successfully executed")
                    else:
                        logPrint("Error occured while changing DN partition.")


            elif datafieldsvalue["file"] == "phone.json":
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = json.load(open(filename))
                    if updatePhone(dataentries, datafieldsvalue):
                        logPrint(
                            "All Phones successfully updated")
                    else:
                        logPrint("Error occured while updating vendor config in phone.")


            elif datafieldsvalue["file"] == "gateways.json" and UPDATE_GATEWAY:
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = json.load(open(filename))
                    if updateGateway(dataentries, datafieldsvalue):
                        logPrint(
                            "All Gateways successfully updated")
                    else:
                        logPrint("Error occured while updating vendor config in gateways.")


            elif datafieldsvalue["file"] == "user.json" and UPDATE_USER:
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = json.load(open(filename))
                    if updateUsers(dataentries, datafieldsvalue):
                        logPrint(
                            "All Users successfully updated")
                    else:
                        logPrint("Error occured while updating users.")

            elif datafieldsvalue["file"] == "css.json" and UPDATE_CSS:
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                if os.path.exists(filename):
                    dataentries = json.load(open(filename))
                    if updateCSS(dataentries, datafieldsvalue):
                        logPrint(
                            "All CSS successfully updated")
                    else:
                        logPrint("Error occured while updating CSS.")


## Reading import Logic Sheet
importLogicContent = IMPORT_LOGIC

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
