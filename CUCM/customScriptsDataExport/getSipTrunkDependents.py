import sys

sys.path.append("../")
from zeep.exceptions import Fault
import json
from adapter.appcore import *

## Export and Import SIP Trunks
## Get List of all SIP Trunks
allSipTrunksdata = ucm_source.get_sip_trunks()
allSipTrunks = []
dependentCSS = []
dependentDP = []
dependentloc = []
dependentMRGL = []
dependentSIPProfile = []

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
        if trFound["return"]["sipTrunk"]["sipProfileName"]["_value_1"] != None:
            dependentSIPProfile.append(
                trFound["return"]["sipTrunk"]["sipProfileName"]["_value_1"]
            )


## Fetching and
dependentConfigs = {
    f"sipTrunkDependent-{ucmSourceContent['siteCode']}": {
        "CSSList": list(set(dependentCSS)),
        "SiteMRGList": list(set(dependentMRGL)),
        "transcoderNames": [],
        "locationNames": list(set(dependentloc)),
        "DevicePoolList": list(set(dependentDP)),
        "SIPProfile":  list(set(dependentSIPProfile))
    }
}
# print(dependentConfigs)

dataFilterDict_JSONobject = json.dumps(dependentConfigs, indent=4)
jsonFile = open(f"../dataJSONS/getDataFilter.json", "w")
jsonFile.write(dataFilterDict_JSONobject)
jsonFile.close()
