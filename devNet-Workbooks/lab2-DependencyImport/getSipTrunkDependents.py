import sys

sys.path.append("../")
from ciscoaxl import axl
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from collections import OrderedDict
import json

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


## Export and Import SIP Trunks
## Get List of all SIP Trunks
allSipTrunksdata = ucm_source.get_sip_trunks()
allSipTrunks = []
dependentCSS = []
dependentDP = []
dependentloc = []
dependentMRGL = []

for siptr in allSipTrunksdata:
    trFound = ucm_source.get_sip_trunk(name=siptr["name"])
    if type(trFound) != Fault:
        allSipTrunks.append(trFound["return"]["sipTrunk"])
        if trFound["return"]["sipTrunk"]["callingSearchSpaceName"]["_value_1"] != None:
            dependentCSS.append(
                trFound["return"]["sipTrunk"]["callingSearchSpaceName"]["_value_1"]
            )
        if trFound["return"]["sipTrunk"]["devicePoolName"]["_value_1"] != None:
            dependentDP.append(
                trFound["return"]["sipTrunk"]["devicePoolName"]["_value_1"]
            )
        if trFound["return"]["sipTrunk"]["locationName"]["_value_1"] != None:
            dependentloc.append(
                trFound["return"]["sipTrunk"]["locationName"]["_value_1"]
            )
        if trFound["return"]["sipTrunk"]["mediaResourceListName"]["_value_1"] != None:
            dependentMRGL.append(
                trFound["return"]["sipTrunk"]["mediaResourceListName"]["_value_1"]
            )


## Fetching and
dependentConfigs = {
    f"sipTrunkDependent-{ucmSourceContent['siteCode']}": {
        "CSSList": list(set(dependentCSS)),
        "SiteMRGList": list(set(dependentMRGL)),
        "transcoderNames": [],
        "locationNames": list(set(dependentloc)),
        "DevicePoolList": list(set(dependentDP)),
    }
}
# print(dependentConfigs)

dataFilterDict_JSONobject = json.dumps(dependentConfigs, indent=4)
jsonFile = open(f"getDataFilter.json", "w")
jsonFile.write(dataFilterDict_JSONobject)
jsonFile.close()
