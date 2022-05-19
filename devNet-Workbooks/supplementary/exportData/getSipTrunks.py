import sys

sys.path.append("../")
from zeep.exceptions import Fault
import os
from adapter.appcore import *

directory = f"../ConfigExports/sipTrunk-{ucmSourceContent['siteCode']}"
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
            trFound = trFound["return"]["sipTrunk"]
            trFound = cleanObject(trFound)
            if "externalPresentationInfo" in trFound and trFound["externalPresentationInfo"] != None:
                # Expanding _raw_elements
                if "_raw_elements" in trFound["externalPresentationInfo"]:
                    configsDict = {
                        entry.tag: entry.text
                        for entry in trFound["externalPresentationInfo"]["_raw_elements"]
                    }

                    del trFound["externalPresentationInfo"]["_raw_elements"]
                    # print(trFound["externalPresentationInfo"])
                    # print(type(trFound["externalPresentationInfo"]))
                    # print(configsDict)
                    try:
                        trFound["externalPresentationInfo"].update(configsDict)
                    except Exception as e:
                        print(e)

            allSipTrunks.append(trFound)
else:
    print(allSipTrunksdata)

# print(allSipTrunks)


## Write Results
write_results(directory, allSipTrunks, "siptrunk")
