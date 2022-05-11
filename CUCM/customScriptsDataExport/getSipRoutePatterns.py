import sys

sys.path.append("../")
from zeep.exceptions import Fault
import os
from adapter.appcore import *


directory = f"../ConfigExports/sipRoutePatterns-{ucmSourceContent['siteCode']}"
if not os.path.exists(directory):
    os.makedirs(directory)
## Export and Import SIP Trunks
## Get List of all SIP Trunks
allSipRPdata = ucm_source.get_sip_route_patterns()
allSipRoutePatterns = []
PartitionList = []
routeListNames = []

if type(allSipRPdata) != Fault:
    for siprp in allSipRPdata:
        siprpFound = ucm_source.get_sip_route_pattern(uuid=siprp["uuid"])
        if type(siprpFound) != Fault:
            allSipRoutePatterns.append(siprpFound["return"]["sipRoutePattern"])
            PartitionList.append(siprpFound["return"]["sipRoutePattern"]["routePartitionName"]["_value_1"])
            routeListNames.append(siprpFound["return"]["sipRoutePattern"]["sipTrunkName"]["_value_1"])
    
    ## Partitions
    allPartitions = []
    for partition in set(PartitionList):
        partitionFound = ucm_source.get_partition(name=partition)
        if type(partitionFound) != Fault:
            allPartitions.append(partitionFound["return"]["routePartition"])

    ## Write Results
    write_results(directory, allPartitions, "partition")

    ## Route List and corresponding Route Groups
    allRouteList = []
    corRouteGroup = []
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
    write_results(directory, allRouteList, "routelist")
    write_results(directory, corRouteGroup, "routegroup")

else:
    print(allSipRPdata)



## Write Results
write_results(directory, allSipRoutePatterns, "sipRoutePatterns")
