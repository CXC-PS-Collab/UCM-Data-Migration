import json
import os
from zeep.exceptions import Fault
import traceback
import sys
sys.path.append("../")

from ciscoaxl import axl
from common.baseFunctions import *
from common.importLogic import updateConfigs

sourceJsonFile=f"../inputs/sourceCluster.json"
dataFilterFile=f"getDataFilter.json"
destinationJsonFile=f"../inputs/destinationCluster.json"
configExportPath=f"./ConfigExports"


## Reading import Logic Sheet
importLogicFile = f"../common/importLogic.json"
dynamicLogicJson = json.load(open(importLogicFile))


## Reading Source File and Destination File
sourceClusterInputJson = json.load(open(sourceJsonFile))
destinationClusterInputJson = json.load(open(destinationJsonFile))


## Creating Source AXL Object
ucm_source = axl(
    username=sourceClusterInputJson["username"],
    password=sourceClusterInputJson["password"],
    cucm=sourceClusterInputJson["cucm"],
    cucm_version=sourceClusterInputJson["version"],
)

ucm_destination = axl(
    username=destinationClusterInputJson["username"],
    password=destinationClusterInputJson["password"],
    cucm=destinationClusterInputJson["cucm"],
    cucm_version=destinationClusterInputJson["version"],
)
# ## Sites to import from config Folder
# Sites = destinationClusterInputJson["configsFolders"]


def generate_config_patterns():
    """
    Step 1: use this function to dynamically 
    create data that we need to extract from 
    source cluster
    """

    ## Define an empty dictionary object to store all sites data
    allSitesData = {}
    ## Generate the datafilter JSON Content
    for site in sourceClusterInputJson['siteCode']:
        siteSpecificdataFilterDict = {
            "CSSList": [
                f"{site}-FAX_Modem_CSS",
                f"{site}-TRK_CSS",
                f"{site}-DEV_CSS",
            ]
        }

        allSitesData[site] = siteSpecificdataFilterDict

    # Serializing json
    dataFilterDict_JSONobject = json.dumps(allSitesData, indent=4)
    jsonFile = open(dataFilterFile, "w")
    jsonFile.write(dataFilterDict_JSONobject)

    ## Close JSON File
    jsonFile.close()


def SiteDataExport(directory, siteDataFilterContent):
    # Flag = True

    CSSList = (
        siteDataFilterContent["CSSList"]
        if "CSSList" in siteDataFilterContent.keys()
        else []
    )

    #Partition List
    PartitionList = (
        siteDataFilterContent["partitionName"]
        if "partitionName" in siteDataFilterContent.keys()
        else []
    )


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


def export_CSS_Partition():
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



def import_CSS_Partition():
    ## iterate over each site folder and push the configurations
    for site in sourceClusterInputJson['siteCode']:
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
                if userAccept == "Y":
                    try:
                        updateConfigs(configDirectory, ucm_destination, dynamicLogicJson)
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
#generate_config_patterns()

# Step 2
#export_CSS_Partition()

# Step 3
#import_CSS_Partition()