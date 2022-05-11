import sys
sys.path.append("../")
from excelJSONConversion import ConvertToExcel
import xmltodict
import requests
from adapter.appcore import *
import datetime
import os
import json

from zeep.exceptions import Fault
from customScriptsDataExport import getUsers
from customScriptsDataMigration import nameChange
from Misc import cssPartitionIndexChange
from requests.auth import HTTPBasicAuth
import traceback
import time

#After path append

# Flag = True

with open('logs.txt', 'w') as f:
    ct = datetime.datetime.now()
    print(ct, ":::", "Process Started", file=f)


def logPrint(msg):
    with open('logs.txt', 'a') as f:
        ct = datetime.datetime.now()
        print(ct, ":::", msg, file=f)
        print(msg)

def getRemoteDestination(destination):
    payload = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://www.cisco.com/AXL/API/" + \
        ucmSourceContent["version"]+"\">\r\n    <soapenv:Header/>\r\n    <soapenv:Body>\r\n        <ns:getRemoteDestination>\r\n            <destination>" + \
            destination+"</destination>\r\n        </ns:getRemoteDestination>\r\n    </soapenv:Body>\r\n</soapenv:Envelope>\r\n"
    headers = {
        'Content-Type': 'text/plain',
    }
    AUTH = HTTPBasicAuth(
        ucmSourceContent["username"], ucmSourceContent["password"])
    cucm = ucmSourceContent["sourceCUCM"]

    response = requests.request(
        "POST", f"https://{cucm}:8443/axl/", headers=headers, auth=AUTH, data=payload, verify=False)

    data_dict = xmltodict.parse(response.text)
    data_dict = data_dict["soapenv:Envelope"]["soapenv:Body"]
    data_dict = data_dict["ns:getRemoteDestinationResponse"]["return"]["remoteDestination"]
    data_dict = getUsers.dictFilter(data_dict, False)
    return data_dict


def getDNFromRDP(rDPData):
    DN = []
    if "lines" in rDPData and rDPData["lines"] != None and "line" in rDPData["lines"]:
        Line = rDPData["lines"]['line']
        if isinstance(Line, dict):
            if 'dirn' in Line:
                line = Line['dirn']
                if "routePartitionName" in line:
                    dn = {"pattern": line['pattern'],
                        "routePartitionName": line['routePartitionName']}
                else:
                    dn = {"pattern": line['pattern'],
                        "routePartitionName": ""}
                if dn not in DN:
                    DN.append(dn)
        else:
            for line in Line:
                if 'dirn' in line:
                    if "routePartitionName" in line['dirn']:
                        dn = {"pattern": line['dirn']['pattern'],
                            "routePartitionName": line['dirn']['routePartitionName']}
                    else:
                        dn = {"pattern": line['dirn']['pattern'],
                            "routePartitionName": ""}
                    if dn not in DN:
                        DN.append(dn)

    if "lineAssociations" in rDPData and rDPData["lineAssociations"] != None and "lineAssociation" in rDPData["lineAssociations"]:
        Line = rDPData["lineAssociations"]['lineAssociation']
        if isinstance(Line, dict):
            if "routePartitionName" in Line:
                dn = {"pattern": Line['pattern'],
                    "routePartitionName": Line['routePartitionName']}
            else:
                dn = {"pattern": Line['pattern'],"routePartitionName": ""}  
            if dn not in DN:
                DN.append(dn)
        else:
            for line in Line:
                if "routePartitionName" in line:
                    dn = {"pattern": line['pattern'],
                        "routePartitionName": line['routePartitionName']}
                else:
                    dn = {"pattern": line['pattern'],"routePartitionName": ""}  
                if dn not in DN:
                    DN.append(dn)
    return DN

def getRoutePatternFromPartition(rpt):
    #Added to consider all partition to be added as part of partition.json
    allRoutePatterns = []
    try:
        rptResults = ucm_source.get_route_patterns(
            SearchCriteria={"routePartitionName": rpt}
        )        
    except Exception as e:
        logPrint(str(e))
        return []
    else:
        if rptResults == None:
            return []
        elif type(rptResults) == Fault:
            return []
        elif type(rptResults["routePattern"]) == list:
            for patt in rptResults["routePattern"]:
                rpData = ucm_source.get_route_pattern(uuid=patt["uuid"])["return"][
                    "routePattern"
                ]
                allRoutePatterns.append(rpData)
            return allRoutePatterns


def getRouteListFromName(rl):
    data = []
    rlFound = ucm_source.get_route_list(name=rl)
    if type(rlFound) != Fault:
        # Extract respective members
        data = [rlFound["return"]["routeList"]]
    return data

def getRouteGroupFromName(rg):
    data = []
    rgFound = ucm_source.get_route_group(name=rg)
    if type(rgFound) != Fault:
        # Extract respective members
        data = [rgFound["return"]["routeGroup"]]
    return data

def getGatewaysFromName(gatewaysTemp):
    gatewayNameListLocal = []
    try:
        foundGateway = ucm_source.get_gateway(domainName=gatewaysTemp)
        if type(foundGateway) != Fault and foundGateway != None:
            gatewayData = foundGateway["return"]["gateway"]
            if gatewayData["vendorConfig"]:
                configsDict = [
                    {
                        entry.tag: entry.text
                        for entry in gatewayData["vendorConfig"]["_value_1"]
                    }
                ]
                del gatewayData["vendorConfig"]
                gatewayData["vendorConfig"] = {"_value_1": configsDict}
            gatewayNameListLocal.append(gatewayData)
    except Exception as e:
        print("Error in Gateway- "+gatewaysTemp+" : "+str(e))
        print(foundGateway)
    return gatewayNameListLocal

def getDPFromName(devicePoolTemp):
    devicePoolListLocal = []
    try:
        dpFound = ucm_source.get_device_pool(name=devicePoolTemp)
        if type(dpFound) != Fault and dpFound != None:
            dpFound = dpFound["return"]["devicePool"]
            devicePoolListLocal.append(dpFound)
    except Exception as e:
        print("Error in Device Pool- "+devicePoolTemp+" : "+str(e))
        print(dpFound)
    return devicePoolListLocal

def extractInfoFromDevice(foundPhone, directedCallParkRoutePartitions, siteDirectoryNumbers, allPhones, CSSList, PartitionList):
    # Correct the vendor configs
    if "vendorConfig" in foundPhone and foundPhone["vendorConfig"] != None:
        configsDict = [
            {
                entry.tag: entry.text
                for entry in foundPhone["vendorConfig"]["_value_1"]
            }
        ]
        del foundPhone["vendorConfig"]
        # print(configsDict)
        foundPhone["vendorConfig"] = {"_value_1": configsDict}

    try:
        foundPhone = cleanObject(foundPhone)
    except Exception as e:
        print("Error in cleaning phone/endpoint data: "+str(e))

    # Correcting dependency for BLF Directed Call parks
    if "blfDirectedCallParks" in foundPhone and foundPhone["blfDirectedCallParks"]:
        resolvedblfDirectedCallParks = []
        for dircallParks in foundPhone["blfDirectedCallParks"][
            "blfDirectedCallPark"
        ]:
            tempentry = dircallParks
            foundDirCallPark = ucm_source.get_directedcallpark(
                uuid=dircallParks["directedCallParkId"]
            )
            if (
                type(foundDirCallPark) != Fault
                and foundDirCallPark != None
            ):
                tempentry["directedCallParkId"] = None
                tempentry["directedCallParkDnAndPartition"] = {
                    "dnPattern": foundDirCallPark["return"][
                        "directedCallPark"
                    ]["pattern"],
                    "routePartitionName": foundDirCallPark["return"][
                        "directedCallPark"
                    ]["routePartitionName"],
                }
                directedCallParkRoutePartitions.append(
                    foundDirCallPark["return"]["directedCallPark"][
                        "routePartitionName"
                    ]["_value_1"]
                )
            resolvedblfDirectedCallParks.append(tempentry)

        foundPhone["blfDirectedCallParks"][
            "blfDirectedCallPark"
        ] = resolvedblfDirectedCallParks

    # Expanding _raw_elements
    if "_raw_elements" in foundPhone:
        configsDict = {
            entry.tag: entry.text
            for entry in foundPhone["_raw_elements"]
        }
        # print(configsDict)
        del foundPhone["_raw_elements"]
        foundPhone.update(configsDict)

    #Getting site specific DNs
    if "lines" in foundPhone and foundPhone["lines"] is not None:
        if "line" in foundPhone["lines"] and foundPhone["lines"]["line"] is not None:
            if isinstance(foundPhone["lines"]['line'], dict):
                line = foundPhone["lines"]['line']
                try:
                    dn = ucm_source.get_directory_number(
                        pattern=line["dirn"]["pattern"], routePartitionName=line["dirn"]["routePartitionName"])["return"]["line"]
                    if line["dirn"]["routePartitionName"] != None and line["dirn"]["routePartitionName"] not in PartitionList:
                        PartitionList.append(
                            line["dirn"]["routePartitionName"])
                    if dn not in siteDirectoryNumbers:
                        siteDirectoryNumbers.append(dn)
                        # if Flag:
                        #     print(dn)
                        #     Flag = False
                except Exception as e:
                    print("Error Fetching/Processing DN for phone:",
                          line["dirn"]["pattern"], ":", str(e))
            else:
                for line in foundPhone["lines"]["line"]:
                    try:
                        dn = ucm_source.get_directory_number(
                            pattern=line["dirn"]["pattern"], routePartitionName=line["dirn"]["routePartitionName"])["return"]["line"]
                        if line["dirn"]["routePartitionName"] != None and line["dirn"]["routePartitionName"] not in PartitionList:
                            PartitionList.append(
                                line["dirn"]["routePartitionName"])
                        if dn not in siteDirectoryNumbers:
                            siteDirectoryNumbers.append(dn)
                            # if Flag:
                            #     print(dn)
                            #     Flag = False
                    except Exception as e:
                        print("Error Fetching/Processing DN for phone:",
                              line["dirn"]["pattern"], ":", str(e))

    if "callingSearchSpaceName" in foundPhone and foundPhone["callingSearchSpaceName"] != None and foundPhone["callingSearchSpaceName"] not in CSSList:
        CSSList.append(foundPhone["callingSearchSpaceName"])

    if foundPhone not in allPhones:
        allPhones.append(foundPhone)

    # addPhoneDependentRecords(foundPhone)
    return [foundPhone, directedCallParkRoutePartitions, siteDirectoryNumbers, allPhones, CSSList, PartitionList]

def getGatewayPortName(gatewayName):
    sqlQuery = "select CASE when d.name is NULL then m.domainname||'_'||'none' else m.domainname||'_'||d.name end as unique,   m.domainname as gatewayname, d.name as endpointname from mgcp as m left join typeproduct as t on t.enum=m.tkproduct left join callmanagergroup as cmg on cmg.pkid = m.fkcallmanagergroup left join mgcpdevicemember as map on map.fkmgcp=m.pkid left join device as d on map.fkdevice=d.pkid left join typemodel as tm on tm.enum = d.tkmodel left join typeproduct as tp on tp.enum=d.tkproduct left join devicenumplanmap as dmap on dmap.fkdevice = d.pkid left join numplan as n on n.pkid = dmap.fknumplan left join callingsearchspace as lcss on lcss.pkid = n.fkcallingsearchspace_sharedlineappear left join devicexml4k as dxml on dxml.fkdevice = d.pkid  where domainname = '"+gatewayName+"' order by m.domainname, map.slot, map.subunit, map.port"
    endpointname = []
    result = ucm_source.sql_query(sqlQuery)
    if type(result) != Fault:
        if result != None:
            for sqldata in result["row"]:
                endpointname.append(str(sqldata[2].text))
    else:
        print("Gateway Port processing failed for- ",gatewayName)
    return endpointname

def SiteDataExport(directory, siteDataFilterContent, siteCode, APP):
    # Flag = True

    CSSList = (
        siteDataFilterContent["CSSList"]
        if "CSSList" in siteDataFilterContent.keys()
        else []
    )
    huntPilotPatterns = (
        siteDataFilterContent["huntPilotPattern"]
        if "huntPilotPattern" in siteDataFilterContent.keys()
        else []
    )
    callParkRouteParitions = (
        siteDataFilterContent["callParkRoutePartitions"]
        if "callParkRoutePartitions" in siteDataFilterContent.keys()
        else []
    )
    directedCallParkRoutePartitions = (
        siteDataFilterContent["directedCallParkRoutePartitions"]
        if "directedCallParkRoutePartitions" in siteDataFilterContent.keys()
        else []
    )

    voiceMailProfileNames = (
        siteDataFilterContent["voiceMailProfileNames"]
        if "voiceMailProfileNames" in siteDataFilterContent.keys()
        else []
    )

    routePatternPartition = (
        siteDataFilterContent["routePatternPartition"]
        if "routePatternPartition" in siteDataFilterContent.keys()
        else []
    )
    routeGroupNameList = (
        siteDataFilterContent["routeGroupNameList"]
        if "routeGroupNameList" in siteDataFilterContent.keys()
        else []
    )

    translationPatternPartitions = (
        siteDataFilterContent["translationPatternPartitions"]
        if "translationPatternPartitions" in siteDataFilterContent.keys()
        else []
    )

    SiteMRGList = (
        siteDataFilterContent["SiteMRGList"]
        if "SiteMRGList" in siteDataFilterContent.keys()
        else []
    )
    transcoderNames = (
        siteDataFilterContent["transcoderNames"]
        if "transcoderNames" in siteDataFilterContent.keys()
        else []
    )

    intercomCSS = (
        siteDataFilterContent["intercomCSS"]
        if "intercomCSS" in siteDataFilterContent.keys()
        else []
    )

    locationNames = (
        siteDataFilterContent["locationNames"]
        if "locationNames" in siteDataFilterContent.keys()
        else []
    )

    DevicePoolList = (
        siteDataFilterContent["DevicePoolList"]
        if "DevicePoolList" in siteDataFilterContent.keys()
        else []
    )


    allGatewayPorts = []  # GatewayPorts Global Var

    def getGatewayPorts(gatewaydata):
        portslist = getGatewayPortName(gatewaydata['domainName'])
        
        #Old Gateway Port code
        # for units in gatewaydata["units"]["unit"]:
        #     if "subunits" in units and units["subunits"] != None:
        #         slotNumber = units["index"]
        #         l = ['000', '001', '002', '003', '004', '005', '006', '007', '008', '009', '00A', '00B', '00C', '00D', '00E', '00F', '010', '011', '012', '013', '014', '015', '016',
        #                         '017','100', '101', '102', '103', '200', '201', '202', '203']

        #         if "subunit" in units["subunits"] and units["subunits"]["subunit"] != None:
        #             for subunits in units["subunits"]["subunit"]:
        #                 if "index" in subunits and "beginPort" in subunits:
        #                     subSlotNumber = subunits["index"]
        #                     beginPort = subunits["beginPort"]
        #                     if "FXO" in subunits["product"]:
        #                         for portnumber in range(0, 4):
        #                             portslist.append(
        #                                 f"AALN/S{slotNumber}/SU{subSlotNumber}/{portnumber}@{gatewaydata['domainName']}"
        #                             )
        #                     #Backlog:: Retrace the logic
        #                     elif "T1" in subunits["product"]:
        #                         for portnumber in range(0, 4):
        #                             portslist.append(
        #                                 f"S{slotNumber}/SU{subSlotNumber}/DS1-{portnumber}@{gatewaydata['domainName']}")
        #                     # @author: guruprbh
        #                     elif "24FXS-SCCP" in subunits["product"]:

        #                         for i in l:
        #                             portslist.append(
        #                                 "AN"+gatewayData["domainName"][5:]+i)
        #                     #Backlog:: Retrace the logic
        #                     elif "E1" in subunits["product"]:
        #                         for portnumber in range(0, 4):
        #                             portslist.append(
        #                                 f"S{slotNumber}/SU{subSlotNumber}/DS1-{portnumber}@{gatewaydata['domainName']}")
        #                     #Backlog:: Retrace the logic
        #                     elif "NIM" in subunits["product"]:
        #                         for i in l:
        #                             portslist.append(
        #                                 "AN"+gatewayData["domainName"][5:]+i)
        #                     elif "VIC3-4FXS" in subunits["product"]:
        #                         for portnumber in range(0, 4):
        #                             portslist.append(
        #                                 "AN"+gatewayData["domainName"][5:]+str(slotNumber)+"8"+str(portnumber))                                
        #                     else:
        #                         print("\nPlease handle this case in GatewayPort for- ",subunits["product"],"type of Gateway- ",gatewayData["domainName"])
        #                         exit()
        if len(portslist) > 0:
            allGatewayPorts.extend(portslist)
        return True

   
    ctiRPNames = []
    try:
        # ctiRPNames = siteDataFilterContent["ctiRPNames"] if "callParkRoutePartitions" in siteDataFilterContent.keys() else []
        if "ctiRPNames" in siteDataFilterContent and siteDataFilterContent["ctiRPNames"] != None:
            ctiRPNames = siteDataFilterContent["ctiRPNames"]
    except Exception as err:
        logPrint("Error in CTI RP: "+str(err))
    gatewayName = (
        siteDataFilterContent["gatewayNames"]
        if "gatewayNames" in siteDataFilterContent.keys()
        else []
    )

    # These records will be populated based on dependency
    phonesDP = (
        siteDataFilterContent["DevicePoolList"]
        if "DevicePoolList" in siteDataFilterContent.keys()
        else []
    )

    mtpNames = (
        siteDataFilterContent["hardwareMTP"]
        if "hardwareMTP" in siteDataFilterContent.keys()
        else []
    )

    cnfNames = (
        siteDataFilterContent["hardwareCNF"]
        if "hardwareCNF" in siteDataFilterContent.keys()
        else []
    )
    sipprofiles = (
        siteDataFilterContent["SIPProfile"]
        if "SIPProfile" in siteDataFilterContent.keys()
        else []
    )
    #Remote Destination Profile Name
    rDPName = (
        siteDataFilterContent["rDPName"]
        if "rDPName" in siteDataFilterContent.keys()
        else []
    )
    #Remote Destination Name
    rDName = (
        siteDataFilterContent["rDName"]
        if "rDName" in siteDataFilterContent.keys()
        else []
    )
    #Device Profile
    deviceProfileName = (
        siteDataFilterContent["deviceProfileName"]
        if "deviceProfileName" in siteDataFilterContent.keys()
        else []
    )

    #Partition List
    PartitionList = (
        siteDataFilterContent["partitionName"]
        if "partitionName" in siteDataFilterContent.keys()
        else []
    )
    #Route List
    routeListExtra = (
        siteDataFilterContent["routeListName"]
        if "routeListName" in siteDataFilterContent.keys()
        else []
    )
    #Intercom Partitions
    intercomPartition = (
        siteDataFilterContent["intercomPartition"]
        if "intercomPartition" in siteDataFilterContent.keys()
        else []
    )
    srstNames = []  # done
    # PartitionList = []  # done
    HuntList = []  # done
    routeListNames = []  # done
    SiteMRGName = []  # done
    linePartition = []  # done
    # Begin the data Export
    # HUNT PILOT, HUNT LIST, LINE GROUP
    allHuntPilots = []
    allHuntList = []
    corLineGroups = []
    for hpPart in huntPilotPatterns:
        try:
            hpReult = ucm_source.get_huntpilots(
                SearchCriteria={"pattern": hpPart})
        except Exception as e:
            logPrint(str(e))
        else:
            if hpReult == None:
                continue
            elif type(hpReult) == Fault:
                continue
            elif type(hpReult["huntPilot"]) == list:
                for pilots in hpReult["huntPilot"]:
                    hpdata = ucm_source.get_huntpilot(uuid=pilots["uuid"])["return"][
                        "huntPilot"
                    ]
                    allHuntPilots.append(hpdata)
                    HuntList.append(hpdata["huntListName"]["_value_1"])
    # Hunt List and corresponding Line Groups
    # To Do: Get Linegroup from DN/Route Partition
    for hunt in set(HuntList):
        huntListFound = ucm_source.get_huntlist(name=hunt)
        if type(huntListFound) != Fault:
            # Extract respective members
            data = huntListFound["return"]["huntList"]
            allHuntList.append(data)
            if "members" in data and data["members"] != None:
                for mem in data["members"]["member"]:
                    lgFound = ucm_source.get_line_group(
                        name=mem["lineGroupName"]["_value_1"]
                    )
                    corLineGroups.append(lgFound["return"]["lineGroup"])

    #Getting DN from LineGroups
    #
    lineGroupSiteDirectoryNumbers = []
    for lineGroups in corLineGroups:
        if "members" in lineGroups and lineGroups["members"] != None:
            if not isinstance(lineGroups["members"]["member"], dict):
                for line in lineGroups["members"]["member"]:
                    if "directoryNumber" in line and "pattern" in line["directoryNumber"] and line["directoryNumber"]["pattern"] != None:
                        try:
                            lineGroupSiteDirectoryNumbers.append(
                                ucm_source.get_directory_number(pattern=line["directoryNumber"]["pattern"], routePartitionName=line["directoryNumber"]["routePartitionName"])["return"][
                                        "line"
                                    ]
                            )
                        except Exception as e:
                            print("Error Fetching/Processing DN for linegroup:",
                                  line["directoryNumber"]["pattern"], ":", str(e))

            else:
                #Change it later if you are getting single dictionary instead of list of dict
                pass

    # Write Results
    write_results(directory, allHuntPilots, "huntpilot")
    write_results(directory, allHuntList, "huntlist")
    write_results(directory, corLineGroups, "linegroup")

    # Collate Partition List
    for lgs in corLineGroups:
        if lgs["members"]:
            for memb in lgs["members"]["member"]:
                PartitionList.append(
                    memb["directoryNumber"]["routePartitionName"]["_value_1"]
                )

    # CALL PARK
    allCallPark = []
    for cpPartition in callParkRouteParitions:
        # get the Callpark patterns in this partition
        callparkQuery = (
            f"select np.dnorpattern from callpark cp "
            f"join numplan np on np.pkid=cp.fknumplan "
            f"join routepartition rp on np.fkroutepartition=rp.pkid "
            f"where np.tkPatternUsage in (0) and rp.name = '{cpPartition}'"
        )
        callParkData = ucm_source.sql_query(callparkQuery)
        if callParkData:
            for sqldata in callParkData["row"]:
                cgFound = ucm_source.get_callpark(
                    pattern=str(sqldata[0].text), routePartitionName=cpPartition
                )
                if type(cgFound) != Fault:
                    allCallPark.append(cgFound["return"]["callPark"])

    # Write Results
    write_results(directory, allCallPark, "callpark")

    # Collate Partition List
    for clps in allCallPark:
        PartitionList.append(clps["routePartitionName"]["_value_1"])

    # Device Pools
    allDevicePools = []
    # for devicepool in DevicePoolList:
    #     dpFound = ucm_source.get_device_pool(name=devicepool)
    #     if type(dpFound) != Fault:
    #         allDevicePools.append(dpFound["return"]["devicePool"])


    # Getting Device Pools
    DevicePoolList = set(DevicePoolList)
    if MULTI_PROCESSING:
        print("Processing Device Pools...")
        parallelProcessOP = parallelProcessing(getDPFromName, DevicePoolList)
        allDevicePools.extend(parallelProcessOP)
    else:
        DevicePoolList = tqdm(DevicePoolList)
        for devicePoolTemp in DevicePoolList:
            DevicePoolList.set_description("Processing Device Pool- %s" % devicePoolTemp)
            allDevicePools.extend(getDPFromName(devicePoolTemp))


    # Write Results
    write_results(directory, allDevicePools, "devicepool")

    # gather SRST
    for dps in allDevicePools:
        if dps["srstName"]["_value_1"] != None:
            srstNames.append(dps["srstName"]["_value_1"])

    # gather MRGL from DP
    for dps in allDevicePools:
        if dps["mediaResourceListName"]["_value_1"] != None:
            SiteMRGList.append(dps["mediaResourceListName"]["_value_1"])

    # gather locations from DP
    for dps in allDevicePools:
        if dps["locationName"]["_value_1"] != None:
            locationNames.append(dps["locationName"]["_value_1"])

    # MEDIA RESOURCES
    allMRGLs = []
    allMRGs = []
    for mrgl in set(SiteMRGList):
        try:
            entry = ucm_source.get_media_resource_group_list(mrgl)
        except Exception as e:
            logPrint(str(e))
        else:
            if entry == None:
                continue
            elif type(entry) == Fault:
                continue
            else:
                mrgldata = entry["return"]["mediaResourceList"]
                allMRGLs.append(mrgldata)
                try:
                    if "clause" in mrgldata and mrgldata["clause"] != None:
                        SiteMRGName.extend(mrgldata["clause"].split(":"))
                except Exception as e:
                    print("MRGL Export Error- "+str(e))

    for mrg in set(SiteMRGName):
        try:
            entry = ucm_source.get_media_resource_group(mrg)
        except Exception as e:
            logPrint(str(e))
        else:
            if entry == None:
                continue
            elif type(entry) == Fault:
                continue
            else:
                allMRGs.append(entry["return"]["mediaResourceGroup"])

    # Write Results
    write_results(directory, allMRGLs, "mediaresourcegrouplist")
    write_results(directory, allMRGs, "mediaresourcegroup")

    # gather Transcoders and MTP from MRG
    for devices in allMRGs:
        if devices["members"] != None:
            for mediaDevices in devices["members"]["member"]:
                if "XCODE" in mediaDevices["deviceName"]["_value_1"]:
                    transcoderNames.append(mediaDevices["deviceName"]["_value_1"])
                elif "-MTP" in mediaDevices["deviceName"]["_value_1"]:
                    mtpNames.append(mediaDevices["deviceName"]["_value_1"])
                elif "CNF" in mediaDevices["deviceName"]["_value_1"]:
                    cnfNames.append(mediaDevices["deviceName"]["_value_1"])
                elif "CONF" in mediaDevices["deviceName"]["_value_1"]:
                    cnfNames.append(mediaDevices["deviceName"]["_value_1"])

    # TRANSCODERS
    allTranscoders = []
    transcoderExtraDP = []
    for trans in set(transcoderNames):
        foundTrans = ucm_source.get_transcoder(name=trans)
        if type(foundTrans) != Fault:
            transData = foundTrans["return"]["transcoder"]
            allTranscoders.append(transData)
            #Getting Device Pool for Transcoder
            transcoderExtraDP = []
            if "devicePoolName" in transData and transData["devicePoolName"] != None:
                if transData["devicePoolName"]["_value_1"] not in DevicePoolList and transData["devicePoolName"] not in transcoderExtraDP:
                    transcoderExtraDP.append(transData["devicePoolName"])
    if len(transcoderExtraDP) > 0:
        print("Found additional DP dependencies in transcoders. Please fetch the same afterwards: ",transcoderExtraDP)
    # Write Results
    write_results(directory, allTranscoders, "transcoder")

    # HARDWARE MTP
    allhardwareMTP = []
    for mtps in set(mtpNames):
        foundMTPs = ucm_source.get_mtp(name=mtps)
        if type(foundMTPs) != Fault:
            allhardwareMTP.append(foundMTPs["return"]["mtp"])

    # Write Results
    write_results(directory, allhardwareMTP, "mtp")

    # HARDWARE Conference Bridges
    allhardwareCNF = []
    for hcnf in set(cnfNames):
        foundCNFs = ucm_source.get_conference_bridge(name=hcnf)
        if type(foundCNFs) != Fault:
            allhardwareCNF.append(foundCNFs["return"]["conferenceBridge"])

    # Write Results
    write_results(directory, allhardwareCNF, "hcnf")

    # ROUTE PATTERNS, ROUTE LIST, ROUTE GROUP
    allRoutePatterns = []
    allRouteList = []
    corRouteGroup = []
    callingPartyXform = []
    calledPartyXform = []


    #Extending PartitionList
    routePatternPartition = set(routePatternPartition)
    PartitionList.extend(routePatternPartition)
    PartitionList = set(PartitionList)

    #For Route Pattern
    if MULTI_PROCESSING:
        print("Processing Route Pattern...")
        parallelProcessOP = parallelProcessing(getRoutePatternFromPartition, routePatternPartition)
        # print('OP Type-',type(parallelProcessOP),"length-",len(parallelProcessOP))
        # print(parallelProcessOP)
        allRoutePatterns.extend(parallelProcessOP)
    else:
        routePatternPartition = tqdm(routePatternPartition)
        for rpt in routePatternPartition:
            routePatternPartition.set_description("Processing RoutePattern in- %s" % rpt)
            allRoutePatterns.extend(getRoutePatternFromPartition(rpt))

    #Getting Route List and Gateways from Route Pattern
    for rpData in allRoutePatterns:
        if rpData["destination"]:
            if rpData["destination"]["routeListName"] != None:
                routeListNames.append(
                    rpData["destination"]["routeListName"]["_value_1"]
                )
            else:
                extraGateway = rpData["destination"]["gatewayName"]["_value_1"]
                if "@" in extraGateway:
                    #Handling Analog gateways and appending it to the code
                    gatewayName.append(extraGateway.split("@")[1])
                else:
                    print("\n Unhandled Gateway/SIP format found in RoutePattern-",extraGateway)
    
    #Getting Calling Party Transformation Pattern from Route Pattern partition
    print("Processing Calling Party and Called Party Transformation...")
    routePatternPartition = tqdm(set(routePatternPartition))
    for rpt in routePatternPartition:
        try:
            # print(rpt)
            callingPartyXformData = ucm_source.get_calling_party_xforms(
                rpt)
            callingPartyXform.extend(callingPartyXformData)
        except Exception as e:
            # print(str(e))
            pass
        try:
            calledPartyXformData = ucm_source.get_called_party_xforms(rpt)
            calledPartyXform.extend(calledPartyXformData)
        except Exception as e:
            # print(str(e))
            pass

    # Route List and corresponding Route Groups
    routeListNames.extend(routeListExtra)
    routeListNames = set(routeListNames)
    if MULTI_PROCESSING:
        print("Processing Route List...")
        parallelProcessOP = parallelProcessing(getRouteListFromName, routeListNames)
        allRouteList.extend(parallelProcessOP)
    else:
        routeListNames = tqdm(routeListNames)
        for rl in routeListNames:
            routeListNames.set_description("Processing RouteList- %s" % rl)
            allRouteList.extend(getRouteListFromName(rl))
            
    #Extracting RouteGroup from Route List
    for data in allRouteList:
        if data["members"] != None:
            for mem in data["members"]["member"]:
                routeGroupNameList.append(mem["routeGroupName"]["_value_1"])

    # Getting Route Group
    routeGroupNameList = set(routeGroupNameList)
    if MULTI_PROCESSING:
        print("Processing Route Group...")
        parallelProcessOP = parallelProcessing(getRouteGroupFromName, routeGroupNameList)
        corRouteGroup.extend(parallelProcessOP)
    else:
        routeGroupNameList = tqdm(routeGroupNameList)
        for rg in routeGroupNameList:
            routeGroupNameList.set_description("Processing RouteGroup- %s" % rg)
            corRouteGroup.extend(getRouteGroupFromName(rg))
    
    
    #Getting GatewayName from RouteGroup
    for items in corRouteGroup:
        items =  cleanObject(items)
        members = items.get("members", None)
        if members != None:
            member = members.get("member", None)
            if isinstance(member,list) and len(member)>0:
                for mem in member:
                    if "deviceName" in mem and mem["deviceName"] != None:
                        if "@" in mem["deviceName"]:
                            #Handling Analog gateways and appending it to the code
                            gatewayName.append(mem["deviceName"].split("@")[1])           

    # Write Results
    write_results(directory, allRoutePatterns, "routepattern")
    write_results(directory, allRouteList, "routelist")
    write_results(directory, corRouteGroup, "routegroup")
    write_results(directory, callingPartyXform, "callingPartyXform")
    write_results(directory, calledPartyXform, "calledPartyXform")

    # Collate Partition List
    PartitionList = list(PartitionList)
    for rps in allRoutePatterns:
        PartitionList.append(rps["routePartitionName"]["_value_1"])

    # TRANSLATION PATTERN
    allTranslationPatterns = []
    translationPatternPartitions = tqdm(set(translationPatternPartitions))
    for tppart in translationPatternPartitions:
        try:
            translationPatternPartitions.set_description("Processing Translation Pattern in- %s" % tppart)

            foundTP = ucm_source.get_translations(
                SearchCriteria={"routePartitionName": tppart}
            )
        except Exception as e:
            pass
        else:
            if foundTP == None:
                continue
            elif type(foundTP) == Fault:
                continue
            else:
                for entry in foundTP:
                    allTranslationPatterns.append(
                        ucm_source.get_translation(uuid=entry["uuid"])["return"][
                            "transPattern"
                        ]
                    )

    # Write Results
    write_results(directory, allTranslationPatterns, "translationpattern")

    # Collate Partition List
    for tps in allTranslationPatterns:
        PartitionList.append(tps["routePartitionName"]["_value_1"])

    # INTERCOM CSS and PARTITION
    allintercomCSS = []
    for intercss in intercomCSS:
        intercssFound = ucm_source.get_calling_search_space(name=intercss)
        if type(intercssFound) != Fault:
            intercomcssdata = intercssFound["return"]["css"]
            try:
                allintercomCSS.append(intercomcssdata)
                if "clause" in intercomcssdata and intercomcssdata["clause"] != None:
                    intercomPartition.extend(
                        intercomcssdata["clause"].split(":"))
            except Exception as e:
                print("Intercom CSS Export Error- "+str(e))

    allintercomPartition = []
    for intercompart in set(intercomPartition):
        intercompartFound = ucm_source.get_partition(name=intercompart)
        if type(intercompartFound) != Fault:
            allintercomPartition.append(
                intercompartFound["return"]["routePartition"])

    # Write Results
    write_results(directory, allintercomCSS, "intercomcss")
    write_results(directory, allintercomPartition, "intercomroutepartition")

    # Voice Mail profile and Voice Mail Pilot
    allVMProfiles = []
    allVMPilots = []
    for vmpro in voiceMailProfileNames:
        vmprofound = ucm_source.get_voicemailprofile(name=vmpro)
        if type(vmprofound) != Fault and vmprofound != None:
            allVMProfiles.append(vmprofound["return"]["voiceMailProfile"])
            allVMPilots.append(
                ucm_source.get_voicemailpilot(
                    uuid=vmprofound["return"]["voiceMailProfile"]["voiceMailPilot"][
                        "uuid"
                    ]
                )["return"]["voiceMailPilot"]
            )

    # Write Results
    write_results(directory, allVMPilots, "voicemailpilot")
    write_results(directory, allVMProfiles, "voicemailprofile")

    # Collate CSS List
    for vps in allVMPilots:
        CSSList.append(vps["cssName"]["_value_1"])

    # Locations
    allLocations = []
    for loc in set(locationNames):
        locfound = ucm_source.get_location(name=loc)
        if type(locfound) != Fault:
            allLocations.append(locfound["return"]["location"])

    # Write Results
    write_results(directory, allLocations, "location")

    # SRST
    allSRST = []
    for srst in srstNames:
        if srst != "Disable":
            srstfound = ucm_source.get_srst(name=srst)
            if type(srstfound) != Fault and srstfound != None:
                allSRST.append(srstfound["return"]["srst"])

    # Write Results
    write_results(directory, allSRST, "srst")

    #DN
    siteDirectoryNumbers = []

    ## CTI Route Point
    allCTIiRP = []
    for ctirp in ctiRPNames:
        try:
            # print("CTIRP Name-",ctirp)
            ctifound = ucm_source.get_cti_route_point(name=ctirp)
            # print(ctifound)
            if type(ctifound) != Fault and ctifound != None:
                foundCti = ctifound["return"]["ctiRoutePoint"]
                allCTIiRP.append(foundCti)

                #Getting site specific DNs
                if "lines" in foundCti and foundCti["lines"] is not None:
                    if "line" in foundCti["lines"] and foundCti["lines"]["line"] is not None:
                        for line in foundCti["lines"]["line"]:
                            try:
                                dn = ucm_source.get_directory_number(
                                    pattern=line["dirn"]["pattern"], routePartitionName=line["dirn"]["routePartitionName"])["return"]["line"]
                                if dn not in siteDirectoryNumbers:
                                    siteDirectoryNumbers.append(dn)
                            except Exception as e:
                                logPrint("Error in CTIRP DN: "+str(e))

        except Exception as err:
            logPrint("Error in CTIRP Implementation: "+str(err))
    ## Write Results
    write_results(directory, allCTIiRP, "ctiroutepoint")

    #Getting Device Profile
    deviceProfile = []
    deviceProfileDN = []
    deviceProfileName = set(deviceProfileName)
    deviceProfileName = tqdm(deviceProfileName)
    for dP in deviceProfileName:
        deviceProfileName.set_description(
            "Processing deviceProfileName- %s" % dP)
        dPFound = ucm_source.get_device_profile(
            name=dP)["return"]["deviceProfile"]

        if type(dPFound) != Fault and dPFound:
            if dPFound not in deviceProfile:
                deviceProfileDN.extend(getDNFromRDP(dPFound))
                deviceProfile.append(dPFound)

    write_results(directory, deviceProfile, "deviceprofile")

    #For SIPTrunk site code i.e., Siptrunk folders skipping phone part
    if "SIPTRUNK" not in siteCode:
        #PHONE DATA: INCLUDES PHONES, ANALOG PHONES, CTI PORTS
        allPhones = []

        #Checking No. of phones in DP versus with desired description
        tempPhones = []
        for phdp in phonesDP:
            tempPhone = ucm_source.get_phones(
                SearchCriteria={"devicePoolName": phdp})
            if type(tempPhone) != Fault and len(tempPhone) > 0:
                tempPhones.extend(tempPhone)
        noOfPhonesByDp = len(tempPhones)
        noOfPhonesByDesc = 0
        tempPhones = ucm_source.get_phones(
            SearchCriteria={"description": "%"+str(siteCode)+"%"})
        if type(tempPhones) != Fault and len(tempPhones) > 0:
            noOfPhonesByDesc = len(tempPhones)
        userAccept = 1
        if noOfPhonesByDp != noOfPhonesByDesc:
            try:
                print("1. No. of phones found with Device Pool as critera: ",
                    noOfPhonesByDp)
                print("2. No. of phones found with Description as critera: ",
                    noOfPhonesByDesc)
                print("Default is device pool.")
                # userAccept = 1
                userAccept = int(
                    input("Which one you want to proceed with(1/2)? "))
            except KeyError:
                print("Invalid input. Selecting Default as DevicePool..")
                userAccept = 1
                print("Scanning phones using device pool.")

    #Getting Phones Logic
    #Add getting Gateway name from endpoints if doesn't exist
        for phdp in phonesDP:
            #Commenting the getPhones through device pool and activating by description
            if userAccept == 2:
                print("Scanning phones using description.")
                searchPhones = ucm_source.get_phones(
                    SearchCriteria={"description": "%"+str(siteCode)+"%"})
                if searchPhones:
                    logPrint(
                        f"Found {len(searchPhones)} devices with {siteCode} in description")
            else:
                print("Scanning phones using device pool-",phdp)
                searchPhones = ucm_source.get_phones(
                    SearchCriteria={"devicePoolName": phdp})
                if searchPhones:
                    logPrint(f"Found {len(searchPhones)} devices in {phdp}")

            if searchPhones:
                searchPhones = tqdm(searchPhones)
                for phone in searchPhones:
                    foundPhone = ucm_source.get_phone(name=phone["name"])
                    searchPhones.set_description(
                        "Processing Phone- %s" % phone["name"])
                    if type(foundPhone) != Fault and foundPhone != None:
                        #Checking and Extracting from phone
                        foundPhone, directedCallParkRoutePartitions, siteDirectoryNumbers, allPhones, CSSList, PartitionList = extractInfoFromDevice(
                            foundPhone, directedCallParkRoutePartitions, siteDirectoryNumbers, allPhones, CSSList, PartitionList)
            if userAccept == 2:
                break

        # Write Results
        # print(allPhones)
        write_results(directory, allPhones, "phone")

    gatewayNameList = []

    # Getting Gateways
    gatewayName = set(gatewayName)
    if MULTI_PROCESSING:
        print("Processing Gateways...")
        parallelProcessOP = parallelProcessing(getGatewaysFromName, gatewayName)
        gatewayNameList.extend(parallelProcessOP)
    else:
        gatewayName = tqdm(gatewayName)
        for gatewaysTemp in gatewayName:
            gatewayName.set_description("Processing Gateway- %s" % gatewaysTemp)
            gatewayNameList.extend(getGatewaysFromName(gatewaysTemp))

    # Write Results
    write_results(directory, gatewayNameList, "gateways")
    #Getting GatewayPort Name from Gateways
    for gatewayData in gatewayNameList:
        # TO DO: Remove the redundancy
        if gatewayData["protocol"] == "SCCP":  # SCCP Gateway
            getGatewayPorts(gatewayData)
        elif gatewayData["protocol"] == "MGCP":
            # Construct names of all Sub Ports
            getGatewayPorts(gatewayData)
            #Get Gateway Ports:  MGCP and SCCP ports
        else:
            print("Unhandled Gateway Protocol Found- ",gatewayData["protocol"])

    allGatewayPortsList = []
    allEndpoints = []
    # print(allGatewayPorts)
    allGatewayPorts = tqdm(set(allGatewayPorts))
    for gtwyPort in allGatewayPorts:
        allGatewayPorts.set_description(
                        "Processing GatewayPort- %s" % gtwyPort)
        try:
            try:
                #MGCP
                gatewayPortFound = ucm_source.get_gateway_analog_port(
                    name=gtwyPort)
            except:
                gatewayPortFound = ucm_source.get_gateway_sccp_port(
                    name=gtwyPort)
            if type(gatewayPortFound) == Fault:
                try:
                    #MGCP
                    gatewayPortFound = ucm_source.get_gateway_analog_port(
                        name=gtwyPort.upper())
                except:
                    gatewayPortFound = ucm_source.get_gateway_sccp_port(
                        name=gtwyPort.upper())
            # print(gatewayPortFound)
            if type(gatewayPortFound) != Fault and gatewayPortFound != None:

                portdata = gatewayPortFound["return"]["gatewayEndpointAnalogAccess"]
                try:
                    if "protocol" in portdata["endpoint"] and portdata["endpoint"]["protocol"] == "SCCP":
                        try:
                            gatewayPortFoundSccp = ucm_source.get_gateway_sccp_port(
                                name=gtwyPort.upper())
                            portdata = gatewayPortFoundSccp["return"]["gatewaySccpEndpoints"]
                        except:
                            gatewayPortFoundSccp = ucm_source.get_gateway_sccp_port(
                                name=gtwyPort)
                            portdata = gatewayPortFoundSccp["return"]["gatewaySccpEndpoints"]

                        gatewayPortFound = gatewayPortFoundSccp
                        # print(gatewayPortFound)
                    if "digital" in portdata["endpoint"]["protocol"].lower():
                        if "t1" in portdata["endpoint"]["protocol"].lower():
                            gatewayPortFound = ucm_source.get_gateway_digital_access_t1(
                                name=gtwyPort.upper())
                            portdata = gatewayPortFound["return"]["gatewayEndpointDigitalAccessT1"]
                        if "pri" in portdata["endpoint"]["protocol"].lower():
                            gatewayPortFound = ucm_source.get_gateway_digital_access_pri(
                                name=gtwyPort.upper())
                            portdata = gatewayPortFound["return"]["gatewayEndpointDigitalAccessPri"]
                        if "bri" in portdata["endpoint"]["protocol"].lower():
                            gatewayPortFound = ucm_source.get_gateway_digital_access_bri(
                                name=gtwyPort.upper())
                            portdata = gatewayPortFound["return"]["gatewayEndpointDigitalAccessBri"]

                except Exception as e:
                    print("Error in Sccp endpoint: " +
                          str(e)+" : "+str(gatewayPortFound))

                 #Managaing ports's Vendor Config
                if "port" in portdata["endpoint"] and portdata["endpoint"]["port"] and "vendorConfig" in portdata["endpoint"]["port"]:
                    if portdata["endpoint"]["port"]["vendorConfig"] != None:
                        # print(portdata)
                        configsDict = [
                            {
                                entry.tag: entry.text
                                for entry in portdata["endpoint"]["port"]["vendorConfig"][
                                    "_value_1"
                                ]
                            }
                        ]

                        del portdata["endpoint"]["port"]["vendorConfig"]
                        # print(configsDict)
                        portdata["endpoint"]["port"]["vendorConfig"] = {
                            "_value_1": configsDict
                        }

                #Extracting info from Portdata
                #Checking and Extracting from phone
                try:
                    if "endpoint" in portdata and portdata["endpoint"] != None:
                       portdata["endpoint"], directedCallParkRoutePartitions, siteDirectoryNumbers, allEndpoints, CSSList, PartitionList = extractInfoFromDevice(
                           portdata["endpoint"], directedCallParkRoutePartitions, siteDirectoryNumbers, allEndpoints, CSSList, PartitionList)
                except Exception as e:
                    logPrint("Error in Extracting endpoint from GatewayPort: "+str(e))

                allGatewayPortsList.append(portdata)
            else:
                print("Error in fetching GatewayPort, This should not be happening!!! Something went Wrong with Gateway Port- ",gtwyPort)
                print("Forcefully Exiting...Fix the issue first")
                # exit()

        except Exception as e:
             print("Failed Gateway Port- ",gtwyPort,":", str(e))
    # ## Write Results
    # print(allGatewayPortsList)
    write_results(directory, allGatewayPortsList, "gatewayports")

    deviceProfileDN = [cleanObject(entry) for entry in deviceProfileDN]

    for dn in deviceProfileDN:
        try:
            dn = ucm_source.get_directory_number(
                pattern=dn["pattern"], routePartitionName=dn["routePartitionName"])["return"]["line"]
            if dn not in siteDirectoryNumbers:
                siteDirectoryNumbers.append(dn)
                # if Flag:
                #     print(dn)
                #     Flag = False
        except Exception as e:
            print("Error Fetching/Processing DN for service profile:", dn["pattern"],":",str(e))

    siteDirectoryNumbers.extend(lineGroupSiteDirectoryNumbers)
    #Getting RDP
    #Doing Manually for now.
    # for dn in siteDirectoryNumbers:
    #     if "associatedDevices" in dn and dn["associatedDevices"] != None:
    #         if "device" in dn["associatedDevices"] and dn["associatedDevices"]["device"] != None:
    #             for device in dn["associatedDevices"]["device"]:
    #                 if "RDP" in device.upper():
    #                     if device not in rDPName:
    #                         rDPName.append(device)
    #Bug Fixed by Getting remoteDestination directly from AXL API - https://cdetsng.cisco.com/summary/#/defect/CSCvj13556
    #Discussion- https://community.cisco.com/t5/management/invalid-schema-definition-for-getremotedestinationreq-in-axl-11/td-p/3459712
    remoteDestination = []
    remoteDestinationProfile = []
    remoteDestinationDN = []
    for rDP in set(rDPName):
        try:
            # print("Going for- ", rDP)
            rDPFound = ucm_source.get_remote_destination_profile(
                name=rDP)["return"]["remoteDestinationProfile"]
            if type(rDPFound) != Fault and rDPFound != None:
                try:
                    rDList = ucm_source.get_remote_destinations(
                        searchCriteria={"remoteDestinationProfileName": rDP})
                except Exception as e:
                    if "NoneType" in str(e):
                        pass
                    else:
                        print("Error for RDP-", rDP, str(e))
                    rDList = None
                # print("RD",rDList)

                if type(rDList) != Fault and rDList != None:
                    for rD in rDList:
                        if "destination" in rD and rD["destination"] != None:
                            try:
                                rDFound = ucm_source.get_remote_destination(
                                    destination=rD["destination"])["return"]["remoteDestination"]
                            except:
                                try:
                                    rDFound = getRemoteDestination(
                                        rD["destination"])
                                except Exception as e:
                                    print("Error fetching remote destination :",
                                          rD["destination"], ":", str(e))
                                    rDFound = False
                            if type(rDFound) != Fault and rDFound:
                                #for rD
                                remoteDestinationDN.extend(
                                    getDNFromRDP(rDFound))
                                remoteDestination.append(rDFound)
                #For rDP
                remoteDestinationDN.extend(getDNFromRDP(rDPFound))
                remoteDestinationProfile.append(rDPFound)
        except Exception as e:
            print("Error in remote Destination part for rDP: "+rDP, str(e))
            traceback.print_exc()
            # exit()

    for rD in set(rDName):
        try:
            rDFound = ucm_source.get_remote_destination(
                destination=rD)["return"]["remoteDestination"]
        except:
            try:
                rDFound = getRemoteDestination(rD)
            except Exception as e:
                print("Error fetching remote destination :", rD, ":", str(e))
                rDFound = False
        if type(rDFound) != Fault and rDFound:
            if rDFound not in remoteDestination:
                remoteDestinationDN.extend(getDNFromRDP(rDFound))
                remoteDestination.append(rDFound)

    # Write Results
    write_results(directory, remoteDestination, "remoteDestination")
    write_results(directory, remoteDestinationProfile,
                  "remoteDestinationProfile")

    #Appending DNs got from linegroup and remoteDestinations
    remoteDestinationDN = [cleanObject(entry) for entry in remoteDestinationDN]

    for dn in remoteDestinationDN:
        try:
            dn = ucm_source.get_directory_number(
                pattern=dn["pattern"], routePartitionName=dn["routePartitionName"])["return"]["line"]
            if dn not in siteDirectoryNumbers:
                siteDirectoryNumbers.append(dn)
                # if Flag:
                #     print(dn)
                #     Flag = False
        except Exception as e:
            print("Error Fetching/Processing DN for remote destination:", dn["pattern"],":",str(e))


    # Directory Numbers
    # Getting Directory number based on route partition only
    # print("DN Export will start here!")
    ## Commented out the DN Addition - Already added above as sitedn
    # allDirectoryNumbers = []
    # # print(linePartition)
    # linePartition = ["BCKSTG_SVCDN_PT", "BCKSTG_PHNDN_PT",
    #                   "BCKSTG_DV_PSTN_PT", "BCKSTG_DV_BLK_LOCAL_PT", "BCKSTG_VID_DN_PT"]
    # uniqueLinePartition = list(set(linePartition))
    # # print("from consolidaton:")
    # # print(uniqueLinePartition)
    # for lPart in uniqueLinePartition:
    #     # print(ucm_source.get_directory_numbers(
    #     #     SearchCriteria={"routePartitionName": lPart}))
    #     allDNs = ucm_source.get_directory_numbers(
    #         SearchCriteria={"routePartitionName": lPart}
    #     )
    #     # print("All Dns:")
    #     # print(allDNs)
    #     if type(allDNs) == list:
    #         for entry in allDNs:
    #             allDirectoryNumbers.append(
    #                 ucm_source.get_directory_number(uuid=entry["uuid"])["return"][
    #                     "line"
    #                 ]
    #             )
    # # print("after removing uuid:")
    # # print(allDirectoryNumbers)

    # # Write Results
    # write_results(directory, allDirectoryNumbers, "directorynumber")

    # Get Gateways

    # @author: guruprbh


    # Directed Call park needs a partition filter

    alldirectedCallParks = []
    for dircpPartition in set(directedCallParkRoutePartitions):
        # get the Callpark patterns in this partition
        dircallparkQuery = (
            f"select np.dnorpattern from numplan np "
            f"join routepartition rp on np.fkroutepartition=rp.pkid "
            f"where np.tkPatternUsage in (12) and ikNumPlan_ParkCode IS NULL and rp.name = '{dircpPartition}'"
        )
        queryResult = ucm_source.sql_query(dircallparkQuery)
        if queryResult:
            for sqldata in queryResult["row"]:
                dircgFound = ucm_source.get_directedcallpark(
                    pattern=str(sqldata[0].text), routePartitionName=dircpPartition
                )
                if type(dircgFound) != Fault:
                    alldirectedCallParks.append(
                        dircgFound["return"]["directedCallPark"]
                    )

    # Write Results
    write_results(directory, alldirectedCallParks, "directedcallpark")

    # Collate Partition List
    for dcps in alldirectedCallParks:
        PartitionList.append(dcps["routePartitionName"]["_value_1"])


    #Appending DNs got from linegroup and remoteDestinations
    remoteDestinationDN = [cleanObject(entry) for entry in remoteDestinationDN]
    deviceProfileDN = [cleanObject(entry) for entry in deviceProfileDN]

    for dn in remoteDestinationDN:
        try:
            dn = ucm_source.get_directory_number(pattern=dn["pattern"], routePartitionName=dn["routePartitionName"])["return"]["line"]
            if dn not in siteDirectoryNumbers:
                siteDirectoryNumbers.append(dn)
                # if Flag:
                #     print(dn)
                #     Flag = False
        except Exception as e:
            print("Error Fetching/Processing DN for remote destination:",dn["pattern"],":",str(e))

    for dn in deviceProfileDN:
        try:
            dn = ucm_source.get_directory_number(pattern=dn["pattern"], routePartitionName=dn["routePartitionName"])["return"]["line"]
            if dn not in siteDirectoryNumbers:
                siteDirectoryNumbers.append(dn)
                # if Flag:
                #     print(dn)
                #     Flag = False
        except Exception as e:
            print("Error Fetching/Processing DN for service profile:",dn["pattern"],":",str(e))

    siteDirectoryNumbers.extend(lineGroupSiteDirectoryNumbers)
    #Filtering DN for 12.5 version also
    siteDirectoryNumbers = [cleanObject(entry) for entry in siteDirectoryNumbers]
    for dn in siteDirectoryNumbers:
        if "externalPresentationInfo" in dn and dn["externalPresentationInfo"] != None:
            # Expanding _raw_elements
            if "_raw_elements" in dn["externalPresentationInfo"]:
                configsDict = {
                        entry.tag: entry.text
                        for entry in dn["externalPresentationInfo"]["_raw_elements"]
                    }

                del dn["externalPresentationInfo"]["_raw_elements"]
                # print(dn["externalPresentationInfo"])
                # print(type(dn["externalPresentationInfo"]))
                # print(configsDict)
                dn["externalPresentationInfo"].update(configsDict)
    
    
    #DN Conclusion
    #Filtering DN for 12.5 version also
    siteDirectoryNumbers = [cleanObject(entry)
                                        for entry in siteDirectoryNumbers]
    for dn in siteDirectoryNumbers:
        if "_raw_elements" in dn:
            configsDict = {
                entry.tag: entry.text
                for entry in dn["_raw_elements"]
            }

            del dn["_raw_elements"]
            # print(dn["externalPresentationInfo"])
            # print(type(dn["externalPresentationInfo"]))
            # print(configsDict)
            dn.update(configsDict)
        if "externalPresentationInfo" in dn and dn["externalPresentationInfo"] != None:
            # Expanding _raw_elements
            if "_raw_elements" in dn["externalPresentationInfo"]:
                configsDict = {
                    entry.tag: entry.text
                    for entry in dn["externalPresentationInfo"]["_raw_elements"]
                }

                del dn["externalPresentationInfo"]["_raw_elements"]
                # print(dn["externalPresentationInfo"])
                # print(type(dn["externalPresentationInfo"]))
                # print(configsDict)
                dn["externalPresentationInfo"].update(configsDict)
    write_results(directory, siteDirectoryNumbers, "directorynumber")

    # Directory Numbers
    # Getting Directory number based on route partition only
    # print("DN Export will start here!")
    ## Commented out the DN Addition - Already added above as sitedn
    # allDirectoryNumbers = []
    # # print(linePartition)
    # linePartition = ["BCKSTG_SVCDN_PT", "BCKSTG_PHNDN_PT",
    #                   "BCKSTG_DV_PSTN_PT", "BCKSTG_DV_BLK_LOCAL_PT", "BCKSTG_VID_DN_PT"]
    # uniqueLinePartition = list(set(linePartition))
    # # print("from consolidaton:")
    # # print(uniqueLinePartition)
    # for lPart in uniqueLinePartition:
    #     # print(ucm_source.get_directory_numbers(
    #     #     SearchCriteria={"routePartitionName": lPart}))
    #     allDNs = ucm_source.get_directory_numbers(
    #         SearchCriteria={"routePartitionName": lPart}
    #     )
    #     # print("All Dns:")
    #     # print(allDNs)
    #     if type(allDNs) == list:
    #         for entry in allDNs:
    #             allDirectoryNumbers.append(
    #                 ucm_source.get_directory_number(uuid=entry["uuid"])["return"][
    #                     "line"
    #                 ]
    #             )
    # # print("after removing uuid:")
    # # print(allDirectoryNumbers)

    # # Write Results
    # write_results(directory, allDirectoryNumbers, "directorynumber")

    # Get Gateways

    # @author: guruprbh


    # Directed Call park needs a partition filter

    alldirectedCallParks = []
    for dircpPartition in set(directedCallParkRoutePartitions):
        # get the Callpark patterns in this partition
        dircallparkQuery = (
            f"select np.dnorpattern from numplan np "
            f"join routepartition rp on np.fkroutepartition=rp.pkid "
            f"where np.tkPatternUsage in (12) and ikNumPlan_ParkCode IS NULL and rp.name = '{dircpPartition}'"
        )
        queryResult = ucm_source.sql_query(dircallparkQuery)
        if queryResult:
            for sqldata in queryResult["row"]:
                dircgFound = ucm_source.get_directedcallpark(
                    pattern=str(sqldata[0].text), routePartitionName=dircpPartition
                )
                if type(dircgFound) != Fault:
                    alldirectedCallParks.append(
                        dircgFound["return"]["directedCallPark"]
                    )

    # Write Results
    write_results(directory, alldirectedCallParks, "directedcallpark")

    # Collate Partition List
    for dcps in alldirectedCallParks:
        PartitionList.append(dcps["routePartitionName"]["_value_1"])


    # CSS
    allCSS = []

    for css in CSSList:
        cssFound = ucm_source.get_calling_search_space(name=css)
        if type(cssFound) != Fault:
            cssdata = cssFound["return"]["css"]
            allCSS.append(cssdata)
            # Create Extended Partition List
            if cssdata["clause"] and cssdata["clause"] != None:
                cssParitions = cssdata["clause"].split(":")
                PartitionList.extend(cssParitions)

    # Write Results
    write_results(directory, allCSS, "css")

    # Partitions
    allPartitions = []

    for partition in set(PartitionList):
        partitionFound = ucm_source.get_partition(name=partition)
        if type(partitionFound) != Fault:
            allPartitions.append(partitionFound["return"]["routePartition"])

    # Write Results
    write_results(directory, allPartitions, "partition")

    return True


def export(APP=False):
    #CUCM Connectivity check
    if not ucm_source.check_cucm():
        print("CUCM AXL Connectivity issue: \n\t1. Check Credentials\n\t2. Check AXL Connectivity\n\t3. Check Account locked status.")
        exit()
    # Read the Input JSON
    dataFilterContent = DATA_FILTER_CONTENT

    if APP:
        if not os.path.exists(f"./ConfigExports"):
            os.makedirs(f"./ConfigExports", exist_ok=True)
    for siteCode, siteData in dataFilterContent.items():
        if siteCode in ucmSourceContent["dataFilterJSONKeys"]:
            if APP:
                directory = f"./ConfigExports/{siteCode}"
            else:
                directory = f"../ConfigExports/{siteCode}"
            if not os.path.exists(directory):
                os.makedirs(directory)
            logPrint(f"Files will be saved in '{directory}' directory")
            logPrint(f"Fetching data for Site: {siteCode}")
            try:
                result = SiteDataExport(directory, siteData, siteCode, APP)
                pass
            except Exception as siteExe:
                logPrint(f"Error Occured while exporting configs: {siteExe}")
                traceback.print_exc()
                exit()

            else:
                logPrint(
                    f"Export Completed for Site: {siteCode}. Proceeding..")
            try:
                userAccept = "Y"
                #input("Do you want to proceed with get user info (Y/n)? ")
            except KeyError:
                logPrint("Invalid input. Existing..")
                exit()
            if userAccept == "Y" or userAccept == "y":
                getUsers.userInfo(siteCode)

            ConvertToExcel([siteCode])

            print("\nExport Completed...")
            if NAMECHANGE:
                time.sleep(2)
                try:
                    userAccept = "Y"
                    #input("Do you want to proceed with Namechange Request (Y/n)? ")
                except KeyError:
                    logPrint("Invalid input. Existing..")
                    exit()
                if userAccept == "Y" or userAccept == "y":
                    nameChange.driverMethod(siteCode)
                else:
                    print(" Existing..")
            
            if MODIFY_CSS:
                try:
                    userAccept = input(
                        "Do you want to proceed with modify CSS PT index Request (Y/n)? ")
                except KeyError:
                    logPrint("Invalid input. Existing..")
                    exit()
                if userAccept == "Y" or userAccept == "y":
                    cssPartitionIndexChange.driverMethod()
                else:
                    print(" Existing..")
            
            print("Completed Export for -",siteCode)

        else:
            logPrint(
                f"SiteCode- {siteCode} of getDataFilter.json is not synchronized with sourceJSON.json file.")

if __name__ == '__main__':
    export()
