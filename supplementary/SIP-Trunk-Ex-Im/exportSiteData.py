import sys

sys.path.append("../")
from ciscoaxl import axl
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from collections import OrderedDict
import json
import os

## Reading Source File
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


def SiteDataExport(directory, siteDataFilterContent):
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

    # ctiRPNames = siteDataFilterContent["ctiRPNames"] if "callParkRoutePartitions" in siteDataFilterContent.keys() else []
    gatewayName = (
        siteDataFilterContent["gatewayNames"]
        if "gatewayNames" in siteDataFilterContent.keys()
        else []
    )

    ## These records will be populated based on dependency
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

    srstNames = []  # done
    PartitionList = []  # done
    HuntList = []  # done
    routeListNames = []  # done
    SiteMRGName = []  # done
    intercomPartition = []  # done
    linePartition = []  # done
    allGatewayPorts = []  # done

    def getGatewayPorts(gatewaydata):
        portslist = []
        for units in gatewaydata["units"]["unit"]:
            slotNumber = units["index"]
            for subunits in units["subunits"]["subunit"]:
                subSlotNumber = subunits["index"]
                beginPort = subunits["beginPort"]
                if "FXO" in subunits["product"]:
                    for portnumber in range(0, 2):
                        portslist.append(
                            f"AALN/S{slotNumber}/SU{subSlotNumber}/{portnumber}@{gatewaydata['domainName']}"
                        )
                elif "T1" in subunits["product"]:
                    continue
        allGatewayPorts.extend(portslist)
        return True

    ## Begin the data Export
    ## HUNT PILOT, HUNT LIST, LINE GROUP
    allHuntPilots = []
    allHuntList = []
    corLineGroups = []
    for hpPart in huntPilotPatterns:
        try:
            hpReult = ucm_source.get_huntpilots(SearchCriteria={"Pattern": hpPart})
        except Exception as e:
            print(e)
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
    ## Hunt List and corresponding Line Groups
    for hunt in set(HuntList):
        huntListFound = ucm_source.get_huntlist(name=hunt)
        if type(huntListFound) != Fault:
            ## Extract respective members
            data = huntListFound["return"]["huntList"]
            allHuntList.append(data)
            if data["members"] != None:
                for mem in data["members"]["member"]:
                    lgFound = ucm_source.get_line_group(
                        name=mem["lineGroupName"]["_value_1"]
                    )
                    corLineGroups.append(lgFound["return"]["lineGroup"])

    ## Write Results
    write_results(directory, allHuntPilots, "huntpilot")
    write_results(directory, allHuntList, "huntlist")
    write_results(directory, corLineGroups, "linegroup")

    ## Collate Partition List
    for lgs in corLineGroups:
        if lgs["members"]:
            for memb in lgs["members"]["member"]:
                PartitionList.append(
                    memb["directoryNumber"]["routePartitionName"]["_value_1"]
                )

    ## CALL PARK
    allCallPark = []
    for cpPartition in callParkRouteParitions:
        ## get the Callpark patterns in this partition
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

    ## Write Results
    write_results(directory, allCallPark, "callpark")

    ## Collate Partition List
    for clps in allCallPark:
        PartitionList.append(clps["routePartitionName"]["_value_1"])

    ## Device Pools
    allDevicePools = []
    for devicepool in DevicePoolList:
        dpFound = ucm_source.get_device_pool(name=devicepool)
        if type(dpFound) != Fault:
            allDevicePools.append(dpFound["return"]["devicePool"])

    ## Write Results
    write_results(directory, allDevicePools, "devicepool")

    ## gather SRST
    for dps in allDevicePools:
        if dps["srstName"]["_value_1"] != None:
            srstNames.append(dps["srstName"]["_value_1"])

    ## gather MRGL from DP
    for dps in allDevicePools:
        if dps["mediaResourceListName"]["_value_1"] != None:
            SiteMRGList.append(dps["mediaResourceListName"]["_value_1"])

    ## gather locations from DP
    for dps in allDevicePools:
        if dps["locationName"]["_value_1"] != None:
            locationNames.append(dps["locationName"]["_value_1"])

    ## MEDIA RESOURCES
    allMRGLs = []
    allMRGs = []
    for mrgl in set(SiteMRGList):
        try:
            entry = ucm_source.get_media_resource_group_list(mrgl)
        except Exception as e:
            print(e)
        else:
            if entry == None:
                continue
            elif type(entry) == Fault:
                continue
            else:
                mrgldata = entry["return"]["mediaResourceList"]
                allMRGLs.append(mrgldata)
                SiteMRGName.extend(mrgldata["clause"].split(":"))

    for mrg in set(SiteMRGName):
        try:
            entry = ucm_source.get_media_resource_group(mrg)
        except Exception as e:
            print(e)
        else:
            if entry == None:
                continue
            elif type(entry) == Fault:
                continue
            else:
                allMRGs.append(entry["return"]["mediaResourceGroup"])

    ## Write Results
    write_results(directory, allMRGLs, "mediaresourcegrouplist")
    write_results(directory, allMRGs, "mediaresourcegroup")

    ## gather Transcoders and MTP from MRG
    for devices in allMRGs:
        for mediaDevices in devices["members"]["member"]:
            if "XCODE" in mediaDevices["deviceName"]["_value_1"]:
                transcoderNames.append(mediaDevices["deviceName"]["_value_1"])
            elif "-MTP" in mediaDevices["deviceName"]["_value_1"]:
                mtpNames.append(mediaDevices["deviceName"]["_value_1"])
            elif "CNF" in mediaDevices["deviceName"]["_value_1"]:
                cnfNames.append(mediaDevices["deviceName"]["_value_1"])
            elif "CONF" in mediaDevices["deviceName"]["_value_1"]:
                cnfNames.append(mediaDevices["deviceName"]["_value_1"])

    ## TRANSCODERS
    allTranscoders = []
    for trans in set(transcoderNames):
        foundTrans = ucm_source.get_transcoder(name=trans)
        if type(foundTrans) != Fault:
            allTranscoders.append(foundTrans["return"]["transcoder"])

    ## Write Results
    write_results(directory, allTranscoders, "transcoder")

    ## HARDWARE MTP
    allhardwareMTP = []
    for mtps in set(mtpNames):
        foundMTPs = ucm_source.get_mtp(name=mtps)
        if type(foundMTPs) != Fault:
            allhardwareMTP.append(foundMTPs["return"]["mtp"])

    ## Write Results
    write_results(directory, allhardwareMTP, "mtp")

    ## HARDWARE Conference Bridges
    allhardwareCNF = []
    for hcnf in set(cnfNames):
        foundCNFs = ucm_source.get_conference_bridge(name=hcnf)
        if type(foundCNFs) != Fault:
            allhardwareCNF.append(foundCNFs["return"]["conferenceBridge"])

    ## Write Results
    write_results(directory, allhardwareCNF, "hcnf")

    ## ROUTE PATTERNS, ROUTE LIST, ROUTE GROUP
    allRoutePatterns = []
    allRouteList = []
    corRouteGroup = []

    for rpt in routePatternPartition:
        try:
            rptResults = ucm_source.get_route_patterns(
                SearchCriteria={"routePartitionName": rpt}
            )
        except Exception as e:
            print(e)
        else:
            if rptResults == None:
                continue
            elif type(rptResults) == Fault:
                continue
            elif type(rptResults["routePattern"]) == list:
                for patt in rptResults["routePattern"]:
                    rpData = ucm_source.get_route_pattern(uuid=patt["uuid"])["return"][
                        "routePattern"
                    ]
                    allRoutePatterns.append(rpData)
                    if rpData["destination"]:
                        if rpData["destination"]["routeListName"] != None:
                            routeListNames.append(
                                rpData["destination"]["routeListName"]["_value_1"]
                            )
                        else:
                            routeListNames.append(
                                rpData["destination"]["gatewayName"]["_value_1"]
                            )
    ## Route List and corresponding Route Groups
    for rl in set(routeListNames):
        rlFound = ucm_source.get_route_list(name=rl)
        if type(rlFound) != Fault:
            ## Extract respective members
            data = rlFound["return"]["routeList"]
            allRouteList.append(data)
            if data["members"] != None:
                for mem in data["members"]["member"]:
                    rgFound = ucm_source.get_route_group(
                        name=mem["routeGroupName"]["_value_1"]
                    )
                    corRouteGroup.append(rgFound["return"]["routeGroup"])

    ## Write Results
    write_results(directory, allRoutePatterns, "routepattern")
    write_results(directory, allRouteList, "routelist")
    write_results(directory, corRouteGroup, "routegroup")
    ## Collate Partition List
    for rps in allRoutePatterns:
        PartitionList.append(rps["routePartitionName"]["_value_1"])

    ## TRANSLATION PATTERN
    allTranslationPatterns = []
    for tppart in translationPatternPartitions:
        try:
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

    ## Write Results
    write_results(directory, allTranslationPatterns, "translationpattern")

    ## Collate Partition List
    for tps in allTranslationPatterns:
        PartitionList.append(tps["routePartitionName"]["_value_1"])

    ## INTERCOM CSS and PARTITION
    allintercomCSS = []
    for intercss in intercomCSS:
        intercssFound = ucm_source.get_calling_search_space(name=intercss)
        if type(intercssFound) != Fault:
            intercomcssdata = intercssFound["return"]["css"]
            allintercomCSS.append(intercomcssdata)
            intercomPartition.extend(intercomcssdata["clause"].split(":"))

    allintercomPartition = []
    for intercompart in set(intercomPartition):
        intercompartFound = ucm_source.get_partition(name=intercompart)
        if type(intercompartFound) != Fault:
            allintercomPartition.append(intercompartFound["return"]["routePartition"])

    ## Write Results
    write_results(directory, allintercomCSS, "intercomcss")
    write_results(directory, allintercomPartition, "intercomroutepartition")

    ## Voice Mail profile and Voice Mail Pilot
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

    ## Write Results
    write_results(directory, allVMPilots, "voicemailpilot")
    write_results(directory, allVMProfiles, "voicemailprofile")

    ## Collate CSS List
    for vps in allVMPilots:
        CSSList.append(vps["cssName"]["_value_1"])

    ## Locations
    allLocations = []
    for loc in set(locationNames):
        locfound = ucm_source.get_location(name=loc)
        if type(locfound) != Fault:
            allLocations.append(locfound["return"]["location"])

    ## Write Results
    write_results(directory, allLocations, "location")

    ## SRST
    allSRST = []
    for srst in srstNames:
        if srst != "Disable":
            srstfound = ucm_source.get_srst(name=srst)
            if type(srstfound) != Fault and srstfound != None:
                allSRST.append(srstfound["return"]["srst"])

    ## Write Results
    write_results(directory, allSRST, "srst")

    # ## CTI Route Point
    # allCTIiRP = []
    # for ctirp in ctiRPNames:
    #     ctifound = ucm_source.get_cti_route_point(name=ctirp)
    #     if type(ctifound) != Fault and ctifound != None:
    #         allCTIiRP.append(ctifound["return"]["ctiRoutePoint"])  # validate this

    # ## Write Results
    # write_results(directory, allCTIiRP, "ctiroutepoint")

    ## PHONE DATA: INCLUDES PHONES, ANALOG PHONES, CTI PORTS
    allPhones = []
    for phdp in phonesDP:
        searchPhones = ucm_source.get_phones(SearchCriteria={"devicePoolName": phdp})
        if searchPhones:
            print(f"Found {len(searchPhones)} devices in {phdp}")
            for phone in searchPhones:
                foundPhone = ucm_source.get_phone(name=phone["name"])
                if type(foundPhone) != Fault and foundPhone != None:
                    ## Correct the vendor configs
                    if foundPhone["vendorConfig"]:
                        configsDict = [
                            {
                                entry.tag: entry.text
                                for entry in foundPhone["vendorConfig"]["_value_1"]
                            }
                        ]
                        del foundPhone["vendorConfig"]
                        foundPhone["vendorConfig"] = {"_value_1": configsDict}
                    ## Correcting dependency for BLF Directed Call parks
                    if foundPhone["blfDirectedCallParks"]:
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

                    allPhones.append(foundPhone)
                    # addPhoneDependentRecords(foundPhone)

    ## Write Results
    write_results(directory, allPhones, "phone")

    ## Directed Call park needs a partition filter

    alldirectedCallParks = []
    for dircpPartition in set(directedCallParkRoutePartitions):
        ## get the Callpark patterns in this partition
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

    ## Write Results
    write_results(directory, alldirectedCallParks, "directedcallpark")

    ## Collate Partition List
    for dcps in alldirectedCallParks:
        PartitionList.append(dcps["routePartitionName"]["_value_1"])

    ## Directory Numbers
    allDirectoryNumbers = []
    uniqueLinePartition = list(set(linePartition))
    uniqueLinePartition.extend(set(intercomPartition))
    for lPart in uniqueLinePartition:
        allDNs = ucm_source.get_directory_numbers(
            SearchCriteria={"routePartitionName": lPart}
        )
        if type(allDNs) == list:
            for entry in allDNs:
                allDirectoryNumbers.append(
                    ucm_source.get_directory_number(uuid=entry["uuid"])["return"][
                        "line"
                    ]
                )

    ## Write Results
    write_results(directory, allDirectoryNumbers, "directorynumber")

    # Get Gateways
    gatewayNameList = []
    for gatewaysTemp in set(gatewayName):
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
            if gatewayData["protocol"] == "SCCP":  ## SCCP Gateway
                continue
            elif gatewayData["protocol"] == "MGCP":
                ## Construct names of all Sub Ports
                getGatewayPorts(gatewayData)
            gatewayNameList.append(gatewayData)

    ## Write Results
    write_results(directory, gatewayNameList, "gateways")

    # Get Gateway Ports: Only MGCP ports
    allGatewayPortsList = []
    for gtwyPort in set(allGatewayPorts):
        try:
            gatewayPortFound = ucm_source.get_gateway_analog_port(name=gtwyPort)
        except:
            continue
        else:
            if type(gatewayPortFound) != Fault and gatewayPortFound != None:
                portdata = gatewayPortFound["return"]["gatewayEndpointAnalogAccess"]
                if portdata["endpoint"]["port"]["vendorConfig"]:
                    configsDict = [
                        {
                            entry.tag: entry.text
                            for entry in portdata["endpoint"]["port"]["vendorConfig"][
                                "_value_1"
                            ]
                        }
                    ]
                    del portdata["endpoint"]["port"]["vendorConfig"]
                    portdata["endpoint"]["port"]["vendorConfig"] = {
                        "_value_1": configsDict
                    }
                allGatewayPortsList.append(portdata)

    # ## Write Results
    write_results(directory, allGatewayPortsList, "gatewayports")

    ## CSS
    allCSS = []

    for css in CSSList:
        cssFound = ucm_source.get_calling_search_space(name=css)
        if type(cssFound) != Fault:
            cssdata = cssFound["return"]["css"]
            allCSS.append(cssdata)
            ## Create Extended Partition List
            cssParitions = cssdata["clause"].split(":")
            PartitionList.extend(cssParitions)

    ## Write Results
    write_results(directory, allCSS, "css")

    ## Partitions
    allPartitions = []
    for partition in set(PartitionList):
        partitionFound = ucm_source.get_partition(name=partition)
        if type(partitionFound) != Fault:
            allPartitions.append(partitionFound["return"]["routePartition"])

    ## Write Results
    write_results(directory, allPartitions, "partition")

    return True


## Read the Input JSON
getDataFilterFile = f"../dataJSONS/getDataFilter.json"
dataFilterContent = json.load(open(getDataFilterFile))

for siteCode, siteData in dataFilterContent.items():
    if siteCode in ucmSourceContent["dataFilterJSONKeys"]:
        directory = f"../ConfigExports/{siteCode}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        print(f"Files will be saved in '{directory}' directory")
        print(f"Fetching data for Site: {siteCode}")
        try:
            SiteDataExport(directory, siteData)
        except Exception as siteExe:
            print(f"Error Occured while exporting configs: {siteExe}")
        else:
            print(f"Export Completed for Site: {siteCode}. Proceeding..")
