# -*- coding: utf-8 -*-
#Getting all the users and its dependencies - userprofiles, universaldevicetemplate, universallinetemplate
import sys
sys.path.append("../")
import os
from zeep.exceptions import Fault
from requests.auth import HTTPBasicAuth
import requests
import xmltodict
from adapter.appcore import *

import time

start = time.time()

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


tagfilter = {'firstName': '', 'middleName': '', 'lastName': '',
             'userid': '', 'mailid': '', 'department': '', 'manager': '',
             'userLocale': '', 'enableCti': '',
             'enableMobility': '', 'enableMobileVoiceAccess': '',
             'maxDeskPickupWaitTime': '', 'remoteDestinationLimit': '',
             'status': '', 'enableEmcc': '', 'patternPrecedence': '',
             'numericUserId': '', 'mlppPassword': '', 'homeCluster': '',
             'imAndPresenceEnable': '', 'directoryUri': '',
             'telephoneNumber': '', 'title': '', 'mobileNumber': '', 'homeNumber': '',
             'pagerNumber': '', 'calendarPresence': '', 'userIdentity': ''}
allUsers = ucm_source.get_users(tagfilter)
directory = f"../ConfigExports/{siteCode}"


if not os.path.exists(directory):
    os.makedirs(directory)
write_results(directory, allUsers, "basicuserdetails")


users = []
userProfile = []
universalLineTemplate = []
universalDeviceTemplate = []
userId = []
failedUser = []
for user in allUsers:
    user = cleanObject(user)
    if user["userid"] not in userId:
        userId.append(user["userid"])
userLen = len(userId)
end = time.time()

print(f"\nFound {userLen} users in {round(end - start,2)} seconds")
save = 0
for user in tqdm (userId,
               desc="Loading users…",
               ascii=False, ncols=75):
    save += 1
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
                    userProfileTemp = ucm_source.get_user_profile_provision(name = user["userProfile"])
                    userProfileTemp = cleanObject(userProfileTemp)
                    userProfileTemp = userProfileTemp['return']["userProfileProvision"]

                    if userProfileTemp not in userProfile:
                        if "_raw_elements" in userProfileTemp:
                            configsDict = {
                                    entry.tag: entry.text
                                    for entry in user["_raw_elements"]
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


                except Exception as e:
                    print("Error in userprofile export- ",str(e))

            if user not in users:
                if "_raw_elements" in user:
                    configsDict = {
                            entry.tag: entry.text
                            for entry in user["_raw_elements"]
                        }

                    del user["_raw_elements"]
                    # print(configsDict)
                    user.update(configsDict)
                users.append(user)
        if save % 500 == 0:
            # Save for every 500 iterations
            write_results(directory, users, "user")
            write_results(directory, userProfile, "userprofile")
            write_results(directory, universalLineTemplate, "universalLineTemplate")
            write_results(directory, universalDeviceTemplate, "universalDeviceTemplate")
    except Exception as e:
        print("Error while fetching userid: "+ str(user) + " : " + str(e))
        failedUser.append(str(user))


write_results(directory, users, "user")
write_results(directory, userProfile, "userprofile")
write_results(directory, universalLineTemplate, "universalLineTemplate")
write_results(directory, universalDeviceTemplate, "universalDeviceTemplate")



# if not os.path.exists(directory):
#     os.makedirs(directory)
# write_results(directory, allUsers, "allUsers")
