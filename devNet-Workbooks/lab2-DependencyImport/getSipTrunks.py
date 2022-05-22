import sys

sys.path.append("../")
from ciscoaxl import axl
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from collections import OrderedDict
import json
import os

ucmSourceFile = f"../inputs/sourceCluster.json"
ucmSourceContent = json.load(open(ucmSourceFile))
ucm_source = axl(
    username=ucmSourceContent["username"],
    password=ucmSourceContent["password"],
    cucm=ucmSourceContent["sourceCUCM"],
    cucm_version=ucmSourceContent["version"],
)

## Base Functions
def cleanObject(data):
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


def write_results(directory, data, dtype):
    cleanedData = [cleanObject(entry) for entry in data]

    if cleanedData:
        jsonString = json.dumps(serialize_object(cleanedData), indent=4)
        jsonFile = open(f"{directory}/{dtype}.json", "w")
        jsonFile.write(jsonString)
        print(f"Saved {dtype}.json")
        jsonFile.close()
    return True


directory = f"./ConfigExports/sipTrunk-{ucmSourceContent['siteCode']}"
if not os.path.exists(directory):
    os.makedirs(directory)
## Export and Import SIP Trunks
## Get List of all SIP Trunks
allSipTrunksdata = ucm_source.get_sip_trunks()
allSipTrunks = []

if type(allSipTrunksdata) != Fault:
    for siptr in allSipTrunksdata:
        trFound = ucm_source.get_sip_trunk(name=siptr["name"])
        if type(trFound) != Fault:
            allSipTrunks.append(trFound["return"]["sipTrunk"])
else:
    print(allSipTrunksdata)


## Write Results
write_results(directory, allSipTrunks, "siptrunk")
