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

dataFilterFile=f"getDataFilter.json" ## output of generate config patterns
configExportPath=f"./ConfigExports"

# ## Sites to import from config Folder
# Sites = destinationClusterInputJson["configsFolders"]


def generate_config_patterns():

    # ## Define an empty dictionary object to store all sites data
    # allSitesData = {}
    # ## Generate the datafilter JSON Content
    # for site in sourceClusterInputJson['siteCode']:
    #     siteSpecificdataFilterDict = {
    #         "CSSList": [
    #             f"{site}_CSS"
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

    CSSList = (
        siteDataFilterContent["CSSList"]
        if "CSSList" in siteDataFilterContent.keys()
        else []
    )

    #Partition List
    PartitionList = []


        # CSS
    allCSS = []

    for css in CSSList:
        cssFound = ucm_source.get_calling_search_space(name=css)
        ## Extract Parition from CSS

    # Write Results
    write_results(directory, allCSS, "css")

        # Partitions
    allPartitions = []

    for partition in set(PartitionList):
        partitionFound = ucm_source.get_partition(name=partition)
        

    # Write Results
    write_results(directory, allPartitions, "partition")

    return True


def export_CSS_Partition():

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
                if userAccept == "Y":
                    try:
                        pass
                        #updateConfigs(configDirectory, ucm_destination)
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
export_CSS_Partition()

# Step 3
import_CSS_Partition()