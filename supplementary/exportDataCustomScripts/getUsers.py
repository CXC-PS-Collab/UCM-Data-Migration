# -*- coding: utf-8 -*-
"""
Created on Wed Oct  6 15:29:18 2021

@author: ashimis3
"""
#Getting all the users and its dependencies - userprofiles, universaldevicetemplate, universallinetemplate
import sys
sys.path.append("../")
import os
import json
from zeep.exceptions import Fault
from requests.auth import HTTPBasicAuth
import requests
import xmltodict
from adapter.appcore import *
import traceback
siteCode = ucmSourceContent["siteCode"]

# Old School Method for filtering data from xml
def dictFilter(myDict, FLAG = False):
    masterList = ["line", "member","betweenLocation","service","userGroup","callState","softKey"]
    if FLAG:           #Logic for line [list]
        # print(type(myDict))
        newLineList = []
        if type(myDict) == list:
            for line in myDict:
                newLineList.append(dictFilter(line,False))
            myDict = newLineList
            #For single line
        else:
            myDict = dictFilter(myDict,False)

    elif isinstance(myDict,dict):
        myDict = dict(myDict)

        temp = myDict.copy() #resolve mutated error
        for key, val in temp.items():
            if ("@uuid" == key):
                myDict.pop(key)
                continue
            #None Type delete
            if (val is None):
                myDict.pop(key)
                continue

            if "#text" == key:
                myDict = val
                #BYpass
            if key in masterList:
                # print(type(val))
                myDict[key] = dictFilter(val, True)
            elif isinstance(val,dict):
                #Undefined Value Removal
                if '@xsi:nil' in val:
                    myDict.pop(key)
                    continue
                myDict[key] = dictFilter(val, False)



    return myDict

def getUser(userid):
    payload = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://www.cisco.com/AXL/API/"+ucmSourceContent["version"]+"\">\r\n    <soapenv:Header/>\r\n    <soapenv:Body>\r\n        <ns:getUser>\r\n            <userid>"+userid+"</userid>\r\n        </ns:getUser>\r\n    </soapenv:Body>\r\n</soapenv:Envelope>\r\n"
    headers = {
      'Content-Type': 'text/plain',
    }
    AUTH = HTTPBasicAuth(ucmSourceContent["username"], ucmSourceContent["password"])
    cucm = ucmSourceContent["sourceCUCM"]

    response = requests.request("POST", f"https://{cucm}:8443/axl/", headers=headers, auth= AUTH, data=payload, verify = False)

    data_dict = xmltodict.parse(response.text)
    data_dict = data_dict["soapenv:Envelope"]["soapenv:Body"]
    data_dict = data_dict["ns:getUserResponse"]["return"]["user"]
    data_dict = dictFilter(data_dict, False)
    return data_dict

def getUserProfile(userProfileName, userProfile = [], universalLineTemplate = [], universalDeviceTemplate = []):
    #Append userprofile, UDT and ULT to existing list
    userProfileTemp = ucm_source.get_user_profile_provision(name = userProfileName)
    userProfileTemp = cleanObject(userProfileTemp)
    userProfileTemp = userProfileTemp['return']["userProfileProvision"]

    if userProfileTemp not in userProfile:
        if "_raw_elements" in userProfileTemp:
            configsDict = {
                    entry.tag: entry.text
                    for entry in userProfileTemp["_raw_elements"]
                }

            del userProfileTemp["_raw_elements"]
            userProfileTemp.update(configsDict)
        # print(configsDict)
        userProfile.append(userProfileTemp)

    #Getting line template
    if "universalLineTemplate" in userProfileTemp and userProfileTemp["universalLineTemplate"] is not None:
        try:
            lineTemplateData = ucm_source.get_universal_line_template(name = userProfileTemp["universalLineTemplate"])
            lineTemplateData = cleanObject(lineTemplateData)
            lineTemplateData = lineTemplateData['return']["universalLineTemplate"]

            if lineTemplateData not in universalLineTemplate:
                universalLineTemplate.append(lineTemplateData)
        except Exception as e:
            print("Error in line template:",str(e))

    #Getting device template
    if "deskPhones" in userProfileTemp and userProfileTemp["deskPhones"] is not None:
        try:
            deviceTemplateData = ucm_source.get_universal_device_template(name = userProfileTemp["deskPhones"])
            deviceTemplateData = cleanObject(deviceTemplateData)
            deviceTemplateData = deviceTemplateData['return']["universalDeviceTemplate"]
            if deviceTemplateData not in universalDeviceTemplate:
                universalDeviceTemplate.append(deviceTemplateData)
        except Exception as e:
            print("Error in Device template:",str(e))
    #Getting device template for mobile devices
    if "mobileDevices" in userProfileTemp and userProfileTemp["mobileDevices"] is not None:
        try:
            deviceTemplateData = ucm_source.get_universal_device_template(name = userProfileTemp["mobileDevices"])
            deviceTemplateData = cleanObject(deviceTemplateData)
            deviceTemplateData = deviceTemplateData['return']["universalDeviceTemplate"]
            if deviceTemplateData not in universalDeviceTemplate:
                universalDeviceTemplate.append(deviceTemplateData)
        except Exception as e:
            print("Error in Device template:",str(e))
    return [ userProfile, universalLineTemplate, universalDeviceTemplate]


def userInfo(siteCode = siteCode):
    try:
        directory = f"../ConfigExports/{siteCode}-SanitizedData/"
        #getting user info from phone and CTIRP
        deviceList = [directory +"phone.json",directory +"ctiroutepoint.json",
                      directory +"remoteDestinationProfile.json",
                      directory + "remoteDestination.json"]
        users = []
        userProfile = []
        universalLineTemplate = []
        universalDeviceTemplate = []
        userId = []

        for devices in deviceList:
            fileName = devices.split("/")[-1]
            try:
                devices = json.load(open(devices))
            except Exception as e:
                # print(str(e))
                continue
            for phone in devices:
                if ("ownerUserName" in phone) and (phone["ownerUserName"] is not None):
                    # print(phone["ownerUserName"])
                    if phone["ownerUserName"] not in userId:
                        userId.append(phone["ownerUserName"])
                if ("digestUser" in phone) and (phone["digestUser"] is not None):
                    # print(phone["digestUser"])
                    if phone["digestUser"] not in userId:
                        userId.append(phone["digestUser"])
                if ("mobilityUserIdName" in phone) and (phone["mobilityUserIdName"] is not None):
                    # print(phone["mobilityUserIdName"])
                    if phone["mobilityUserIdName"] not in userId:
                        userId.append(phone["mobilityUserIdName"])
                if ("userId" in phone) and (phone["userId"] is not None):
                    # print(phone["mobilityUserIdName"])
                    if phone["userId"] not in userId:
                        userId.append(phone["userId"])
                if ("ownerUserId" in phone) and (phone["ownerUserId"] is not None):
                    # print(phone["mobilityUserIdName"])
                    if phone["ownerUserId"] not in userId:
                        userId.append(phone["ownerUserId"])

                #Handling users at line level
                if "lines" in phone and phone["lines"] != None and "line" in phone["lines"]:
                    for line in phone["lines"]["line"]:
                        if "associatedEndusers" in line and line["associatedEndusers"] != None:
                            if "enduser" in line["associatedEndusers"] and line["associatedEndusers"]["enduser"] != None:
                                for user in line["associatedEndusers"]["enduser"]:
                                    if "userId" in user and user["userId"] != None:
                                        if user["userId"] not in userId:
                                            userId.append(user["userId"])

            print("Found",len(userId),"users in "+fileName)
        #Handle users also from phone line
        userId = list(set(userId))

        for user in tqdm (userId,
           desc="Loading users…",
           ascii=False, ncols=75):
            try:
                try:
                    data = ucm_source.get_user(user)
                except Exception as e:
                    # print(str(e))
                    data = getUser(user)

                if type(data) != Fault:
                    user = cleanObject(data)
                    # if "associatedDevices" in user:
                    #     del user["associatedDevices"]
                    # if "lineAppearanceAssociationForPresences" in user:
                    #     del user["lineAppearanceAssociationForPresences"]
                    # if "associatedGroups" in user:
                    #     del user["associatedGroups"]
                    # if "primaryExtension" in user:
                    #     del user["primaryExtension"]
                    # if "extensionsInfo" in user:
                    #     del user["extensionsInfo"]
                    #Adding User Profile of the user
                    if "userProfile" in user and user["userProfile"] != None:
                        try:
                            userProfile, universalLineTemplate, universalDeviceTemplate = getUserProfile(user["userProfile"], userProfile, universalLineTemplate, universalDeviceTemplate)
                        except Exception as e:
                            print("Error in userprofile export- ",str(e))
                    if "_raw_elements" in user:
                        configsDict = {
                                entry.tag: entry.text
                                for entry in user["_raw_elements"]
                            }

                        del user["_raw_elements"]
                        # print(configsDict)
                        user.update(configsDict)
                    if user not in users:
                        users.append(user)
            except Exception as e:
                print("Error while fetching userid: "+ str(user) + " : " + str(e))

        directory = f"../ConfigExports/{siteCode}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        write_results(directory, users, "user")
        write_results(directory, userProfile, "userprofile")
        write_results(directory, universalLineTemplate, "universalLineTemplate")
        write_results(directory, universalDeviceTemplate, "universalDeviceTemplate")
    except Exception as e:
        print("Error in User Module: "+str(e))
        traceback.print_exc()


def onlyUserProfile(userProfileList, siteCode = siteCode):
    user_profile=[]
    udt=[]
    ult=[]
    for up in userProfileList:
        user_profile, ult, udt= getUserProfile(up,user_profile,ult,udt)
    directory = f"../ConfigExports/{siteCode}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    write_results(directory, user_profile, "userprofile")
    write_results(directory, ult, "universalLineTemplate")
    write_results(directory, udt, "universalDeviceTemplate")

def getUniversalLineTemplate(lineTemplate,universalLineTemplate=[]):
    for i in lineTemplate:
        try:
            lineTemplateData = ucm_source.get_universal_line_template(name = i)
            lineTemplateData = cleanObject(lineTemplateData)
            lineTemplateData = lineTemplateData['return']["universalLineTemplate"]

            if lineTemplateData not in universalLineTemplate:
                universalLineTemplate.append(lineTemplateData)
        except Exception as e:
            print("Error in line template:",str(e))

    directory = f"../ConfigExports/{siteCode}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    write_results(directory, universalLineTemplate, "universalLineTemplate")