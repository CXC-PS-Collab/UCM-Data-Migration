import sys

sys.path.append("../")
from zeep.exceptions import Fault
import os
from adapter.appcore import *


icast_Configs = ucmSourceContent["iCastConfigsParameters"]

directory = f"../ConfigExports/ICastConfigs-{ucmSourceContent['siteCode']}"

transcoderNames = []
mtpNames = []
srstNames = []
def iCastExport(directory):

    #CUCM Connectivity check
    if not ucm_source.check_cucm():
        print("CUCM AXL Connectivity issue: \n\t1. Check Credentials\n\t2. Check AXL Connectivity\n\t3. Check Account locked status.")
        exit()
    global icast_Configs
    PartitionList = []
    SiteMRGName = []
    CSSList = []
    locationList = []
    linetuple = []

    ## CALL PARK
    allCallPark = []
    for cpPattern in icast_Configs["callParkPattern"]:
        ## get the Callpark patterns in this partition
        callparkQuery = (
            f"select np.dnorpattern,rp.name from callpark cp "
            f"join numplan np on np.pkid=cp.fknumplan "
            f"join routepartition rp on np.fkroutepartition=rp.pkid "
            f"where np.tkPatternUsage in (0) and np.dnorpattern = '{cpPattern}'"
        )
        callParkData = ucm_source.sql_query(callparkQuery)
        if type(callParkData) != Fault and callParkData and not isinstance(callParkData, str):
            for sqldata in callParkData["row"]:
                cgFound = ucm_source.get_callpark(
                    pattern=str(sqldata[0].text),
                    routePartitionName=str(sqldata[1].text),
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
    for devicepool in icast_Configs["DevicePoolList"]:
        dpFound = ucm_source.get_device_pool(name=devicepool)
        # print(dpFound)
        # print(devicepool)
        
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
            icast_Configs["SiteMRGList"].append(
                dps["mediaResourceListName"]["_value_1"]
            )

    ## gather locations from DP
    for dps in allDevicePools:
        if dps["locationName"]["_value_1"] != None:
            locationList.append(dps["locationName"]["_value_1"])

    ## MEDIA RESOURCES
    allMRGLs = []
    allMRGs = []
    for mrgl in set(icast_Configs["SiteMRGList"]):
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
                try:
                    SiteMRGName.extend(mrgldata["clause"].split(":"))
                except:
                    pass

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

    # CTI Route Point
    allCTIiRP = []
    for devicepool in icast_Configs["DevicePoolList"]:
        ctiRPFoundlist = ucm_source.get_cti_route_points(
            SearchCriteria={"devicePoolName": devicepool}
        )
        if type(ctiRPFoundlist) != Fault and ctiRPFoundlist != None:
            for ctirp in ctiRPFoundlist["ctiRoutePoint"]:
                ctifound = ucm_source.get_cti_route_point(name=ctirp["name"])
                if type(ctifound) != Fault and ctifound != None:
                    allCTIiRP.append(
                        ctifound["return"]["ctiRoutePoint"]
                    )  # validate this

    ## Write Results
    write_results(directory, allCTIiRP, "ctiroutepoint")

    ## Collate dependecies List
    for ctirp in allCTIiRP:
        CSSList.append(ctirp["callingSearchSpaceName"]["_value_1"])
        locationList.append(ctirp["locationName"]["_value_1"])
        if ctirp["lines"] != None and "line" in ctirp["lines"] and ctirp["lines"]["line"] != None :
            for linerecord in ctirp["lines"]["line"]:
                try:
                    linetuple.append(
                        (
                            linerecord["dirn"]["pattern"],
                            linerecord["dirn"]["routePartitionName"]["_value_1"],
                        )
                    )
                except Exception as e:
                    print("Error in CTIRP DN: "+str(e))

    ## CTI Ports DATA: CTI PORTS
    allCTIPorts = []
    for devicepool in icast_Configs["DevicePoolList"]:
        searchCTIPorts = ucm_source.get_phones(
            SearchCriteria={"devicePoolName": devicepool, "product": "CTI Port"}
        )
        if type(searchCTIPorts) != Fault and searchCTIPorts:
            print(f"Found {len(searchCTIPorts)} devices in {devicepool}")
            for ports in searchCTIPorts:
                foundCTIPhone = ucm_source.get_phone(name=ports["name"])
                if type(foundCTIPhone) != Fault and foundCTIPhone != None:
                    ## Correct the vendor configs
                    if foundCTIPhone["vendorConfig"]:
                        configsDict = [
                            {
                                entry.tag: entry.text
                                for entry in foundCTIPhone["vendorConfig"]["_value_1"]
                            }
                        ]
                        del foundCTIPhone["vendorConfig"]
                        foundCTIPhone["vendorConfig"] = {"_value_1": configsDict}

                    allCTIPorts.append(foundCTIPhone)
                    # addPhoneDependentRecords(foundPhone)

    ## Write Results
    write_results(directory, allCTIPorts, "ctiPorts")

    ## Collate dependecies List
    for ctipr in allCTIPorts:
        CSSList.append(ctipr["callingSearchSpaceName"]["_value_1"])
        locationList.append(ctipr["locationName"]["_value_1"])
        if ctipr["lines"] != None and "line" in ctipr["lines"] and ctipr["lines"]["line"] != None :
            for linerecord in ctipr["lines"]["line"]:
                try:
                    linetuple.append(
                        (
                            linerecord["dirn"]["pattern"],
                            linerecord["dirn"]["routePartitionName"]["_value_1"],
                        )
                    )
                except Exception as e:
                    print("Error in CTIRP Ports DN: "+str(e))

    ## get locations
    ## Locations
    allLocations = []
    for loc in set(locationList):
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

    ## Get all Lines w.r.t to CTI
    allDirectoryNumbers = []
    for lPart in set(linetuple):
        dnFound = ucm_source.get_directory_number(
            pattern=lPart[0], routePartitionName=lPart[1]
        )
        if type(dnFound) != Fault and dnFound != None:
            allDirectoryNumbers.append(dnFound["return"]["line"])
        
    allDirectoryNumbers = [cleanObject(entry) for entry in allDirectoryNumbers]

    for dn in allDirectoryNumbers:
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
    
    ## Write Results
    write_results(directory, allDirectoryNumbers, "directorynumber")

    ## CSS
    CSSList.extend(icast_Configs["CSSList"])
    allCSS = []
    for css in set(CSSList):
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


if not os.path.exists(directory):
    os.makedirs(directory)
print(f"Files will be saved in '{directory}' directory: SourceCluster: {ucmSourceContent['sourceCUCM']}")
iCastExport(directory)