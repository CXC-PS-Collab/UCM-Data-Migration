# -*- coding: utf-8 -*-
"""
Created on Fri Dec 17 06:54:13 2021

@author: ashimis3
"""


# Replacing Names
import sys
import traceback
sys.path.append("../")
import shutil
from zeep.exceptions import Fault
from collections import OrderedDict
from zeep.helpers import serialize_object
import json
from ciscoaxl import axl
import os
from os import listdir
from os.path import isfile, join
from adapter.appcore import *

#For sipTrunkDependents
# siteCode = "sipTrunkDependent-BCKSTG_SITE1"
#For General codes
siteCode = ucmSourceContent["siteCode"]
orgFolder = f"../ConfigExports/{siteCode}-SanitizedData/"

genList = []

def changeName(entity, keyList, replaceMap):
    '''
    Parameters
    ----------
    entity : dict
        Recursion on dict object.
    keyList : list
        key list to check for.
    val : str
        Val to replace.
    replace : str
        Replacement value.

    Returns
    -------
    None.

    '''
    count = 0
    if isinstance(entity, dict):
        for k, v in entity.items():
            if k in keyList and v != None and isinstance(v, str):
                #Convex Statement
                for val, replace in replaceMap.items():
                    if val in v:
                        try:
                            entity[k] = entity[k].replace(val,replace)
                        except Exception as e:
                            print("Error Occured - Data- ",entity)
                            print("Key checked-",k)
                            print(str(e))
                            exit()

            elif isinstance(v, list):
                for i in range(len(v)):
                    if isinstance(v[i], dict):
                        v[i], tempcount = changeName(v[i], keyList, replaceMap)
                        count += tempcount
                    if isinstance(v[i], str):
                        #Convex Statement
                        for val, replace in replaceMap.items():
                            if val in v[i]:
                                # print(val)
                                count += v[i].count(val)
                                v[i] = v[i].replace(val,replace)
                                # print(Items)
            elif isinstance(v, dict):
                v, tempcount = changeName(v, keyList, replaceMap)
                count += tempcount
            elif isinstance(v, str):
                for val, replace in replaceMap.items():
                    if val in v:
                        if k not in keyList and k not in genList:
                            print("Found New Key: ",k,v,"for",val)
                            genList.append(k)
                        # entity[k].replace(val,replace)
    return [entity, count]



def driverMethod(scd = siteCode):
    Files = [f for f in listdir(orgFolder) if isfile(join(orgFolder, f))]
    replaceMap = {
        "SourceName":"DestName",
        "SourceName2":"DestName2",
    }

    keyList = ["description", "routePartitionName", "routePartition", "clause", "devicePoolName", "alertingName", "lastName", 
               "name", "locationName", "mediaResourceListName","voiceMailProfileName", "asciiAlertingName","dateTimeSettingName", "laapPartition",
               "srstName", "deviceName", "mediaResourceGroupName", "lineGroupName", "display", "displayAscii", "laapDescription",
               "devicePoolName", "callingSearchSpaceName", "routeGroupName", "subscribeCallingSearchSpaceName",
               "routeListName","cssName","shareLineAppearanceCssName", "huntListName"]

    print("Name Change Initiated...")
    count = 0
    for file in Files:
        if ".json" in file:
            entityList = json.load(open(orgFolder+file))
            for entity in entityList:
                entity, tempcount = changeName(entity, keyList, replaceMap)
                count += tempcount
            name = ((file.split("/"))[-1].split(".json"))[0]
            write_results(orgFolder, entityList, name)

    print("Name Change Completed. Replaced- ",count,"instances.")

# driverMethod(siteCode)
