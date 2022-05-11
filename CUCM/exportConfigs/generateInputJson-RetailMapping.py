import pandas as pd
import json

## Read the Input sheet
siteInputs = pd.read_excel("siteInputs.xlsx")
siteInputs.fillna(method="ffill", inplace=True)
dataFilterDict = {}
allSiteCodes = set(siteInputs["siteCode"].tolist())

## Generate the datafilter JSON Content
for site in allSiteCodes:
    filteredDF = siteInputs[siteInputs["siteCode"] == site]
    # for index, row in filteredDF.iterrows():
    siteSpecificdataFilterDict = {
        "CSSList": [
            f"{site}-DEV_CSS",
            f"{site}-TRK_CSS",
            f"{site}-RX_CSS",
            f"{site}-FAX_Modem_CSS",
            f"{site}-FAX_Modem_DEV_CSS",
        ],
        "callParkRoutePartitions": [f"{site}-PHNDN_PT"],
        "directedCallParkRoutePartitions": [f"{site}-Park_PT", f"{site}-RX_PT"],
        "voiceMailProfileNames": [f"{site}_VMP"],
        "routePatternPartition": [
            f"{site}-911_PT",
            f"{site}-PHNDN_PT",
            f"{site}-RX_PT",
        ],
        "translationPatternPartitions": [f"{site}-CHK_PT", f"{site}-PHNDN_PT"],
        "SiteMRGList": [f"{site}_MRGL"],
        "transcoderNames": [f"{site}-XCODE"],
        "intercomPartition": [f"{site}-COM_PT"],
        "intercomCSS": [f"{site}-COM_CSS"],
        "locationNames": [f"{site}_LOC"],
        "DevicePoolList": [f"{site}-ALG_DP", f"{site}_ALG_DP", f"{site}_DP", f"{site}_Non_SIP-DP", f"{site}_NON-SIP-DP", f"{site}_NON_SIP-DP", f"{site}_Non-SIP-DP", 
        f"{site}_Non-SIP_DP", f"{site}_Non_SIPDP", f"{site}-NonSIP_DP", f"{site}-Non-SIPDP", f"{site}-Non-SIP", f"{site}_NON-SISP-DP",
        f"{site}P-ALG_DP", f"{site}P_ALG_DP", f"{site}P_DP", f"{site}P_Non_SIP-DP", f"{site}P_NON-SIP-DP", f"{site}P_NON_SIP-DP", f"{site}P_Non-SIP-DP", 
        f"{site}P_Non-SIP_DP", f"{site}P_Non_SIPDP", f"{site}P-NonSIP_DP", f"{site}P-Non-SIPDP", f"{site}P-Non-SIP", f"{site}P_NON-SISP-DP"],
        "ctiRPNames": [f"{site}_CTIRP", f"{site}-CTIRPS", f"{site}-CTIRP"],
    }
    siteSpecificdataFilterDict["huntPilotPattern"] = filteredDF[
        "huntPilotPatterns"
    ].dropna().tolist()
    siteSpecificdataFilterDict["huntPilotPattern"] = list(
        map(int, siteSpecificdataFilterDict["huntPilotPattern"]))
    siteSpecificdataFilterDict["huntPilotPattern"] = list(
        map(str, siteSpecificdataFilterDict["huntPilotPattern"]))
    siteSpecificdataFilterDict["gatewayNames"] = filteredDF["gatewayNames"].dropna().tolist(
    )
    siteSpecificdataFilterDict["gatewayNames"] = list(
        map(str, siteSpecificdataFilterDict["gatewayNames"]))
    dataFilterDict[site] = siteSpecificdataFilterDict

# Serializing json
dataFilterDict_JSONobject = json.dumps(dataFilterDict, indent=4)
jsonFile = open(f"../adapter/getDataFilter.json", "w")
jsonFile.write(dataFilterDict_JSONobject)
jsonFile.close()
