from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from collections import OrderedDict
import json
import os


def cleanObject(data):
    # print(data)
    if type(data) == str:
        return data
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


def updateMRGL(mrgldata,ucm_destination):
    result = []
    for mgrl in mrgldata:
        cleanedInput = mgrl
        try:
            resp = ucm_destination.update_media_resource_group_list(
                name=cleanedInput["name"], members=cleanedInput["members"]
            )
            if "duplicate value" in str(resp) or "exists" in str(resp):
                result.append(True)
                continue
            elif type(resp) == Fault:
                result.append(False)
                continue
            else:
                print(f"updated {cleanedInput['name']}")
                result.append(True)
        except Exception as ex:
            result.append(False)
            print(ex)
    if all(result):
        return True
    else:
        return False


def updateConfigs(ConfigPath, ucm_destination,dynamicLogicJson):

    for datafieldskey, datafieldsvalue in dynamicLogicJson.items():
        if "exception" not in datafieldsvalue.keys():
            filename = f"{ConfigPath}/{datafieldsvalue['file']}"
            try:
                dataentries = json.load(open(filename))
                print(f"Adding {datafieldskey}")
            except:
                continue
            for entry in dataentries:
                cleanedInput = cleanObject(entry)
                try:
                    for toRemove in datafieldsvalue["headersToRemove"]:
                        del cleanedInput[toRemove]
                    ## Exception for MRGL
                    if datafieldsvalue["file"] == "mediaresourcegrouplist.json":
                        cleanedInput["members"] = []
                except Exception as removeExe:
                    print(f"Cannot remove any header: {removeExe}")
                    continue
                try:
                    resp = getattr(ucm_destination, datafieldsvalue["axlMethod"])(
                       cleanedInput
                    )
                    if "duplicate value" in str(resp) or "exists" in str(resp):
                        print(
                            f"{cleanedInput[datafieldsvalue['output']]} already exist"
                        )
                        continue
                    elif type(resp) == Fault:
                        print(
                            f"Exception occured: {resp} while adding: {cleanedInput[datafieldsvalue['output']]}"
                        )
                        continue
                    else:
                        print(f"added {cleanedInput[datafieldsvalue['output']]}")
                except Exception as ex:
                    print(f"Exception in AXL Request: {ex}")
        else:
            ## Updating MRGL Members:
            try:
                if datafieldsvalue["file"] == "mediaresourcegrouplist.json":
                    print(f"{datafieldskey} members")
                    filename = f"{ConfigPath}/{datafieldsvalue['file']}"
                    if os.path.exists(filename):
                        dataentries = json.load(open(filename))
                        if updateMRGL(dataentries,ucm_destination):
                            print("MRGL Updated")
                        else:
                            print("Error occured while updating")
            except Exception as ex:
                print(f"Exception occured: {ex}")