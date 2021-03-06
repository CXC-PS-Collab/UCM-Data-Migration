import json
import os
from zeep.exceptions import Fault
import traceback
import sys
sys.path.append("../")

from ciscoaxl import axl
from common.baseFunctions import *
from common.importLogic import updateConfigs



## Reading import Logic Sheet
importLogicFile = f"../common/importLogic.json"
dynamicLogicJson = json.load(open(importLogicFile))



### Read Source and Destination Input JSON's
sourceJsonFile=f"../inputs/sourceCluster.json"
destinationJsonFile=f"../inputs/destinationCluster.json"
#sourceClusterInputJson = 
#destinationClusterInputJson = 


## Create Source AXL Object
# ucm_axl_object_source = axl(
#     username=,
#     password=,
#     cucm=,
#     cucm_version=,
# )

## Create Destination AXL Object
# ucm_axl_object_dest = axl(
#     username=,
#     password=,
#     cucm=,
#     cucm_version=,
# )

def generate_config_patterns():

    # ## Define an empty dictionary object to store all sites data
    # allSitesData = {}
    # ## Generate the datafilter JSON Content
    # for site in sourceClusterInputJson['siteCode']:
    #     siteSpecificdataFilterDict = {
    #         "routePatternPartition": [
    #             f"{site}_911_PT",
    #             f"{site}_International_PT"
    #             f"{site}_national_PT"
    #         ]
    #     }

    #     allSitesData[site] = siteSpecificdataFilterDict

    # # Serializing json
    # dataFilterDict_JSONobject = json.dumps(allSitesData, indent=4)
    # jsonFile = open(dataFilterFile, "w")
    # jsonFile.write(dataFilterDict_JSONobject)

    # ## Close JSON File
    # jsonFile.close()
    return


def SiteDataExport(directory, siteDataFilterContent):
    # Flag = True

    routePatternPartition = (
        siteDataFilterContent["routePatternPartition"]
        if "routePatternPartition" in siteDataFilterContent.keys()
        else []
    )

    ## Store all dependent Route Pattern data
    allRoutePatterns = []

    ## Store all dependent Route List data
    corrRouteListNames= []
    allRouteList = []

    ## Store all dependent Route Group data
    allRouteGroup = []

    ## Store all dependent Partition data
    corrPartitionsNames = []
    allPartitions = []

    for rpt in routePatternPartition:
        rptResults = ucm_source.get_route_patterns(
            SearchCriteria={"routePartitionName": rpt}
        )
    ## Write code logic to extract Route list from Route Pattern

    ## Write code logic to extract Route Group from Route List

    ## Collate Partition List
    for rps in allRoutePatterns:
        corrPartitionsNames.append(rps["routePartitionName"]["_value_1"])


    for partition in set(corrPartitionsNames):
        partitionFound = ucm_source.get_partition(name=partition)
        if type(partitionFound) != Fault:
            allPartitions.append(partitionFound["return"]["routePartition"])

    # Write Results
    write_results(directory, allRoutePatterns, "routepattern")
    # write_results(directory, allRouteList, "routelist")
    # write_results(directory, allRouteGroup, "routegroup")
    # write_results(directory, allPartitions, "partition")

    return True


def export_RP_Dependencies():
    """
    Step 2: use this function to export
    CSS and its dependent partitions.
    """
    # Read the dataFilter JSON: This JSON is created in step 1
    dataFilterContent = json.load(open(dataFilterFile))
    for siteCode, siteData in dataFilterContent.items():
        configDirectory = f"{configExportPath}/{siteCode}"
        if not os.path.exists(configDirectory):
            os.makedirs(configDirectory)
        logPrint(f"Files will be saved in '{configDirectory}' directory")
        logPrint(f"Fetching data for Site: {siteCode}")

        try:
            SiteDataExport(configDirectory, siteData)
        except Exception as siteExe:
            logPrint(f"Error Occured while exporting configs: {siteExe}")
            traceback.print_exc()
            exit()

        else:
            logPrint(f"Export Completed for Site: {siteCode}. Proceeding..")



def import_RP_Dependencies():
    ## iterate over each site folder and push the configurations
    for site in sourceClusterInputJson['configsFolders']:
        configDirectory = f"{configExportPath}/{site}"
        logPrint(f"Reading Configs from Directory: {configDirectory}. Proceeding...")
        if os.path.exists(configDirectory):
            logPrint(
                f"Starting Import for Site: {site} on CUCM: {destinationClusterInputJson['cucm']}"
            )
            try:
                userAccept = input("Do you want to proceed (Y/n)?")
            except KeyError:
                print("Invalid input. Existing..")
                exit()
            else:
                if userAccept.lower == "Y":
                    try:
                        updateConfigs(configDirectory, ucm_destination,)
                    except Exception as importExe:
                        logPrint(f"Error Occured while Importing: {importExe}")
                        traceback.print_exc()
                        exit()
                    else:
                        logPrint(f"Data Import completed for site: {site}. Proceeding...")
                else:
                    logPrint(f"invalid response '{userAccept}' received. Exiting...")
                    exit()




# Step 1
generate_config_patterns()

# Step 2
export_RP_Dependencies()

# Step 3
import_RP_Dependencies()