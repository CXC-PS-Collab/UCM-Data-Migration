# -*- coding: utf-8 -*-
"""
Created on Tue Nov 25 14:18:34 2021

@author: ashimis3
"""

# -*- coding: utf-8 -*-
#Getting all the callPickupGroup
import sys
sys.path.append("../")
import time
from adapter.appcore import *
import os


siteCode = ucmSourceContent["siteCode"]

directory = f"../ConfigExports/{siteCode}"

tagfilter = {'name': ''}

#General Methods

configList = {
  "PhoneNtp": [{"description": "%"}, {"ipAddress": ""}, "phoneNtp"],
  "PhoneSecurityProfile": [{"name": "%"}, {"name": ""}, "phoneSecurityProfile"],
  "SipTrunkSecurityProfile": [{"name": "%"}, {"name": ""}, "sipTrunkSecurityProfile"],
  "PhysicalLocation": [{"name": "%"}, {"name": ""}, "physicalLocation"],
  "AudioCodecPreferenceList": [{"name": "%"}, {"name": ""}, "audioCodecPreferenceList"],
  "ApplicationDialRules": [{"name": "%"}, {"name": ""}, "applicationDialRules"],
  "TimePeriod": [{"name": "%"}, {"name": ""}, "timePeriod"],
  "AarGroup": [{"name": "%"}, {"name": ""}, "aarGroup"],
  "SipDialRules": [{"name": "%"}, {"name": ""}, "sipDialRules"],
  "UcService": [{"name": "%"}, {"name": ""}, "ucService"],
  "SoftKeyTemplate": [{"name": "%"}, {"name": ""}, "softKeyTemplate"],
  "IpPhoneServices": [{"serviceName": "%"}, {"serviceName": ""}, "ipPhoneServices"],
  "PhoneButtonTemplate": [{"name": "%"}, {"name": ""}, "phoneButtonTemplate"],
  "SIPNormalizationScript": [{"name": "%"}, {"name": ""}, "sIPNormalizationScript"],
  "DateTimeGroup": [{"name": "%"}, {"name": ""}, "dateTimeGroup"],
  "Region": [{"name": "%"}, {"name": ""}, "region"],
  "TimeSchedule": [{"name": "%"}, {"name": ""}, "timeSchedule"],
  "ServiceProfile": [{"name": "%"}, {"name": ""}, "serviceProfile"],
  "CommonPhoneConfig": [{"name": "%"}, {"name": ""}, "commonPhoneConfig"],
  "DefaultDeviceProfile": [{"name": "%"}, {"name": ""}, "defaultDeviceProfile"]
  }

if not os.path.exists(directory):
    os.makedirs(directory)

#CUCM Connectivity check
if not ucm_source.check_cucm():
    print("CUCM AXL Connectivity issue: \n\t1. Check Credentials\n\t2. Check AXL Connectivity\n\t3. Check Account locked status.")
    exit()

for key, val in configList.items():
    start = time.time()
    if key == "PhoneNtp" and ucmSourceContent["version"] == "12.5":
        val[1] = {'ipAddress': '','ipv6Address':''}
    listConfig = "list" + key
    getConfig = "get" + key
    try:
        entityNameList = getattr(ucm_source.client, listConfig)(
            val[0], returnedTags=val[1])
        if entityNameList != None and entityNameList["return"] != None:
            entityNameList = entityNameList["return"][val[2]]
        else:
            print("\n",key,"Not found.")
            continue
        # print(entityNameList)
        for i in range(len(entityNameList)):
            entityNameList[i] = cleanObject(entityNameList[i])
        end = time.time()

        print(
            f"\nFound {len(entityNameList)} {key} in {round(end - start,2)} seconds. Processing...")

        entityConfigs = []
        entityNameList = tqdm(entityNameList)
        for entity in entityNameList:
            if key == "PhoneNtp":
                if "ipAddress" in entity and entity["ipAddress"] != None:
                    entity = {"ipAddress": entity.get("ipAddress")}
                else:
                    entity = {"ipv6Address": entity.get("ipv6Address")}
            elif key == "IpPhoneServices":
                entity = {"serviceName": entity.get("serviceName")}
            else:
                entity = {"name": entity.get("name")}
            resp = getattr(ucm_source.client, getConfig)(
                **entity)["return"][val[2]]
            entityConfigs.append(resp)
        configList[key].append(entityConfigs)

        write_results(directory, entityConfigs, key)
    except Exception as e:
        print("Error Occured-", str(e))
        # print(entityNameList)
        # print(entityConfigs)
        traceback.print_exc()
