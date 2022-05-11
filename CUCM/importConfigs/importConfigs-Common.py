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

def addGatewayPorts(gatewayPortdata):
    #Manual Authorization is given in this- Look out for this otherwise will give authentication error.
    result = []
    gatewayPortdata = tqdm(gatewayPortdata)
    for gwport in gatewayPortdata:
        cleanedInput = gwport
        gatewayPortdata.set_description(f"Processing Gateway Ports : {cleanedInput['domainName']} :")

        ## Removing keys not needed
        FLAGSCCP = False
        del cleanedInput["endpoint"]["confidentialAccess"]
        del cleanedInput["endpoint"]["ctiid"]
        if "protocol" in cleanedInput["endpoint"] and cleanedInput["endpoint"]["protocol"] == "SCCP":
            FLAGSCCP = True
        if "port" in cleanedInput["endpoint"] and cleanedInput["endpoint"]["port"] != None:
            cleanedInput["endpoint"]["port"]["sigDigits"] = {"0"}
        if "subscribeCallingSearchSpaceName" in cleanedInput["endpoint"] and cleanedInput["endpoint"]["subscribeCallingSearchSpaceName"] == None:
            cleanedInput["endpoint"]["subscribeCallingSearchSpaceName"] = ""
        if "vendorConfig" in cleanedInput["endpoint"]:
            del cleanedInput["endpoint"]["vendorConfig"]
        PAUSE = True
        requestMethod = ""
        while(PAUSE == True):
            ERROR = False
            try:
                if "endpoint" in cleanedInput and 'name' in cleanedInput["endpoint"] and cleanedInput["endpoint"]['name'] != None:
                    gPortName = "Gateway- " +cleanedInput['domainName']+" : "+cleanedInput["endpoint"]['name']
                else:
                    gPortName = cleanedInput['domainName']
                if FLAGSCCP:
                    resp = ucm_destination.add_gateway_sccp_port(cleanedInput)
                else:
                    try:
                        if "digital" in cleanedInput["endpoint"]["protocol"].lower():
                            if "t1" in cleanedInput["endpoint"]["protocol"].lower():
                                requestMethod = "addGatewayEndpointDigitalAccessT1"
                                resp = ucm_destination.add_gateway_digital_access_t1(cleanedInput)
                            if "pri" in cleanedInput["endpoint"]["protocol"].lower():
                                requestMethod = "addGatewayEndpointDigitalAccessPri"
                                resp = ucm_destination.add_gateway_digital_access_pri(cleanedInput)
                            if "bri" in cleanedInput["endpoint"]["protocol"].lower():
                                requestMethod = "addGatewayEndpointDigitalAccessBri"
                                resp = ucm_destination.add_gateway_digital_access_bri(cleanedInput)
                        else:
                            requestMethod = "addGatewayEndpointAnalogAccess"
                            resp = ucm_destination.add_gateway_analog_port(cleanedInput)
                    except Exception as e:
                        traceback.print_exc()
                        resp = str(e)
                        ERROR = True
                    # Update Logic
                # if type(resp) and "duplicate value" in str(resp):
                #     cleanedInput = {"name": cleanedInput["endpoint"]["name"],"endpoint":cleanedInput["endpoint"]}

                #     if FLAGSCCP:
                #         resp = ucm_destination.update_gateway_sccp_port(cleanedInput)
                #         print(str(resp))

                #     else:
                #         resp = ucm_destination.update_gateway_analog_port(cleanedInput)

                ## Making adjustments for Correcting the Analog Ports due to sigDigits error
                if ((type(resp) == Fault) and ("union value 'NotSet'" in str(resp))) or ERROR:
                    ERROR = True
                    logPrint(f"{str(resp)}: Attempting again using Request Method:")
                    ver = ucmDestinationContent["version"]
                    if FLAGSCCP:
                        headers = {
                            "Content-Type": "text/xml",
                            "SOAPAction": "CUCM:DB ver="+ver+" addGatewaySccpEndpoints",
                            #"Authorization": HTTPBasicAuth(ucmDestinationContent["username"], ucmDestinationContent["password"]),#"Basic Y2NtdmFkbWluOkMxc2MwQDEyMyE=",
                        }
                    else:
                        headers = {
                            "Content-Type": "text/xml",
                            "SOAPAction": "CUCM:DB ver="+ver+" "+requestMethod,
                            #"Authorization": HTTPBasicAuth(ucmDestinationContent["username"], ucmDestinationContent["password"]),#"Basic Y2NtdmFkbWluOkMxc2MwQDEyMyE=",
                        }

                    payload = str(
                        etree.tostring(
                            ucm_destination.history.last_sent["envelope"],
                            encoding="unicode",
                        )
                    )

                if ERROR:
                    payload = payload.replace(
                        "<sigDigits>NotSet</sigDigits>", "<sigDigits>0</sigDigits>"
                    )
                    try:
                        cucm = ucmDestinationContent["cucm"]

                        response = requests.request(
                            "POST",
                            f"https://{cucm}:8443/axl/",
                            headers=headers,
                            data=payload,
                            auth = HTTPBasicAuth(ucmDestinationContent["username"], ucmDestinationContent["password"]),
                            verify=False,
                        )

                    except Exception as reqEx:
                        logPrint(f"{str(reqEx)}: {gPortName}")
                        In = input("\n Error Occured, Want to retry? (y/n)")
                        if In == "n" or In == "N":
                            PAUSE = False

                        result.append(False)
                    else:
                        result.append(True)
                        logPrint(f"Processed {gPortName} Log-")
                        if "new row - duplicate value" in response.text:
                            logPrint( f" {gPortName} already exist")  
                        else:                     
                            logPrint(f"\t {response.text}")
                        PAUSE = False
                    # logPrint (f"{str(resp)}: {cleanedInput['domainName']}")
                elif "duplicate" in str(resp) or "exists" in str(resp) or "Uniqueness check" in str(resp):#or "Uniqueness check" in str(resp):
                    logPrint(
                        f"{gPortName} already exist"
                    )
                    PAUSE = False
                    continue
                elif type(resp) == Fault:
                    result.append(False)
                    logPrint(f"{str(resp)}: {gPortName}")
                    In = input("\n Error Occured, Want to retry? (y/n)")
                    if In == "n" or In == "N":
                        PAUSE = False

                else:
                    result.append(True)
                    PAUSE = False
                    logPrint(f"added {gPortName}")
            except Exception as ex:
                logPrint("Failed "+gPortName+" : Error :"+str(ex))
                In = input("\n Error Occured, Want to retry? (y/n)")
                if In == "n" or In == "N":
                    PAUSE = False
                result.append(False)

    if all(result):
        return True
    else:
        return False

status = []
def updateConfigs(ConfigPath, dynamicLogicJson):
    for datafieldskey, datafieldsvalue in dynamicLogicJson.items():
        GLOBAL_PAUSE = True

        while(GLOBAL_PAUSE):
            count = already = failed = succeed = 0

            if "exception" not in datafieldsvalue.keys():
                filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                try:
                    dataentries = json.load(open(filename))
                    logPrint(f"Adding {datafieldskey}")
                    print(f"\nAdding {datafieldskey}")
                except:
                    GLOBAL_PAUSE = False
                    continue
                count = len(dataentries)
                dataentries = tqdm(dataentries)
                for entry in dataentries:
                    cleanedInput = cleanObject(entry)
                    PAUSE = True
                    while(PAUSE == True):
                        try:
                            #Removing keys per entry in entries
                            cleanedInput = removeKeys(datafieldsvalue, cleanedInput)
                        except Exception as removeExe:
                            print(removeExe)
                            logPrint(f"Cannot remove any header: {removeExe}")
                            traceback.print_exc()

                            failed += 1
                            dataentries.set_description(f"Processing {datafieldskey} : Failed Header : {cleanedInput[datafieldsvalue['output']]} :")
                            if STOP_IMPORT_PAUSE:
                                PAUSE = False
                                continue

                            In = input("\n Error Occured, Want to retry? (y/n): ")
                            if In == "n" or In == "N":
                                PAUSE = False
                            continue
                        try:
                            resp = getattr(ucm_destination, datafieldsvalue["axlMethod"])(
                                cleanedInput
                            )
                            if "duplicate" in str(resp) or "exists" in str(resp) or "Uniqueness check" in str(resp):#or "Uniqueness check" in str(resp):
                                logPrint(
                                    f"{cleanedInput[datafieldsvalue['output']]} already exist"
                                )
                                already += 1
                                PAUSE = False
                                dataentries.set_description(f"Processing {datafieldskey} : Duplicate : {cleanedInput[datafieldsvalue['output']]} :")
                                continue
                            elif type(resp) == Fault:
                                if "User Id" in str(resp):
                                    logPrint(
                                        f"Exception occured: {resp} : userId- {cleanedInput['ownerUserName']} : while adding: {cleanedInput[datafieldsvalue['output']]} : {str(resp)}"
                                    )
                                else:
                                    logPrint(
                                        f"Exception occured: {resp} while adding: {cleanedInput[datafieldsvalue['output']]} : {str(resp)}"
                                    )
                                failed += 1
                                dataentries.set_description(f"Processing {datafieldskey} : Failed : {cleanedInput[datafieldsvalue['output']]} :")
                                if STOP_IMPORT_PAUSE:
                                    PAUSE = False
                                    continue
                                In = input("\n Error Occured, Want to retry? (y/n): ")
                                if In == "n" or In == "N":
                                    PAUSE = False
                                continue
                            else:
                                logPrint(
                                    f"added {cleanedInput[datafieldsvalue['output']]}")
                                succeed += 1
                                PAUSE = False
                                dataentries.set_description(f"Processing {datafieldskey} : Added : {cleanedInput[datafieldsvalue['output']]} :")

                        except Exception as ex:
                            failed += 1
                            logPrint(
                                "Error in "+datafieldsvalue["file"]+" -Exception in AXL Request: "+str(ex))
                            dataentries.set_description(f"Processing {datafieldskey} : Major Issue : {cleanedInput[datafieldsvalue['output']]} :")
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
            else:
                if datafieldsvalue["file"] == "gatewayports.json":
                    #Pending for modification
                    filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                    if os.path.exists(filename):
                        logPrint("Adding gateway ports")
                        dataentries = json.load(open(filename))
                        if addGatewayPorts(dataentries):
                            logPrint("Gateway Ports Added")
                        else:
                            logPrint("Error occured while adding Ports")
                    if STOP_IMPORT_PAUSE:
                        GLOBAL_PAUSE = False
                    else:
                        In = input(f"\n Completed  {datafieldskey}. Want to continue (Y) or retry (N) (y/n): ")
                        if In == "y" or In == "Y":
                            GLOBAL_PAUSE = False
                else:
                    GLOBAL_PAUSE = False


importLogicContent = IMPORT_LOGIC
#Removing mrgl for REMOVE_MRGL_FROM_DEVICE - One Time Patch, Not needed in Future- Customer Specific
if REMOVE_MRGL_FROM_DEVICE:
    importLogicContent["Phones"]["headersToRemove"].append("mediaResourceListName")

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
