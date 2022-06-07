"""
Consists of Base Functions required for Labs
Author: Saurabh Khaneja
Version: 0.1
"""

from zeep.helpers import serialize_object
from collections import OrderedDict
import json
from datetime import datetime

## Base Functions
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
        return data

def write_results(directory, data, dtype):
    if dtype in ["callpark", "directedcallpark"]:
        cleanedData = []
        for entry in data:
            uuid = entry["uuid"]
            tempCleanedData = cleanObject(entry)
            tempCleanedData["uuid"] = uuid
            cleanedData.append(tempCleanedData)
            del tempCleanedData
    else:
        if dtype == "hcnf":
            cleanedData = [cleanObject(entry) for entry in data]
        else:
            cleanedData = [cleanObject(entry) for entry in data]

    if cleanedData:
        jsonString = json.dumps(serialize_object(cleanedData), indent=4)
        jsonFile = open(f"{directory}/{dtype}.json", "w")
        jsonFile.write(jsonString)
        print(f"Saved {dtype}.json")
        jsonFile.close()
    return True

with open('logs.txt', 'w') as f:
    ct = datetime.now()
    print(ct, ":::", "Process Started", file=f)


def logPrint(msg):
    with open('logs.txt', 'a') as f:
        ct = datetime.now()
        print(ct, ":::", msg, file=f)
        print(msg)


def cleanObjectImport(data):
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