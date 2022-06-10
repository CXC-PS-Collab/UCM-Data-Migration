"""
Class to interface with cisco ucm axl api.
Author: Jeff Levensailor
Version: 0.1
Dependencies:
 - zeep: https://python-zeep.readthedocs.io/en/master/

Links:
 - https://developer.cisco.com/site/axl/
"""
"""
New UCM AXL methods added and generalised
for UCM Like to Like migrations.

Author: Saurabh Khaneja
Version: 0.2
"""


from pathlib import Path
import os
import traceback
from requests import Session
from requests.auth import HTTPBasicAuth
import re
import urllib3
from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.cache import SqliteCache
from zeep.plugins import HistoryPlugin
from zeep.exceptions import Fault
from lxml import etree
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class axl(object):
    """
    The AXL class sets up the connection to the call manager with methods for configuring UCM.
    Tested with environment of;
    Python 3.6
    """

    def __init__(self, username, password, cucm, cucm_version):
        """
        :param username: axl username
        :param password: axl password
        :param cucm: UCM IP address
        :param cucm_version: UCM version

        example usage:
        >>> from axl import AXL
        >>> ucm = AXL('axl_user', 'axl_pass', '192.168.200.10')
        """

        cwd = os.path.dirname(os.path.abspath(__file__))
        if os.name == "posix":
            wsdl = Path(f"{cwd}/schema/{cucm_version}/AXLAPI.wsdl").as_uri()
        else:
            wsdl = str(
                Path(f"{cwd}/schema/{cucm_version}/AXLAPI.wsdl").absolute())

        session = Session()
        session.verify = False
        session.auth = HTTPBasicAuth(username, password)
        settings = Settings(
            strict=False, xml_huge_tree=True, xsd_ignore_sequence_order=True
        )
        self.history = HistoryPlugin()
        transport = Transport(session=session, timeout=20, cache=SqliteCache())
        try:
            axl_client = Client(
                wsdl, settings=settings, transport=transport, plugins=[
                    self.history]
            )
        #For Pyinstaller Exe file

        except Exception as e:
            if os.name == "posix":
                wsdl = Path(f"./schema/{cucm_version}/AXLAPI.wsdl").as_uri()
            else:
                wsdl = str(
                    Path(f"./schema/{cucm_version}/AXLAPI.wsdl").absolute())

            axl_client = Client(
                wsdl, settings=settings, transport=transport, plugins=[
                    self.history]
            )

        self.wsdl = wsdl
        self.username = username
        self.password = password
        self.wsdl = wsdl
        self.cucm = cucm
        self.cucm_version = cucm_version
        self.UUID_PATTERN = re.compile(
            r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$", re.IGNORECASE
        )
        self.client = axl_client.create_service(
            "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding",
            f"https://{cucm}:8443/axl/",
        )
        self.axl_client = axl_client

    def get_locations(
        self,
        tagfilter={
            "name": "",
            "withinAudioBandwidth": "",
            "withinVideoBandwidth": "",
            "withinImmersiveKbits": "",
        },
    ):
        """
        Get location details
        :param mini: return a list of tuples of location details
        :return: A list of dictionary's
        """
        try:
            return self.client.listLocation({"name": "%"}, returnedTags=tagfilter,)[
                "return"
            ]["location"]
        except Fault as e:
            return e

    def sql_query(self, query):
        """
        Execute SQL query
        :param query: SQL Query to execute
        :return: result dictionary
        """
        try:
            return self.client.executeSQLQuery(query)["return"]
        except Fault as e:
            return str(e)

    def sql_update(self, query):
        """
        Execute SQL update
        :param query: SQL Update to execute
        :return: result dictionary
        """
        try:
            return self.client.executeSQLUpdate(query)["return"]
        except Fault as e:
            return e

    def get_ldap_dir(
        self,
        tagfilter={
            "name": "",
            "ldapDn": "",
            "userSearchBase": "",
        },
    ):
        """
        Get LDAP Syncs
        :return: result dictionary
        """
        try:
            return self.client.listLdapDirectory(
                {"name": "%"},
                returnedTags=tagfilter,
            )["return"]["ldapDirectory"]
        except Fault as e:
            return e

    def do_ldap_sync(self, uuid):
        """
        Do LDAP Sync
        :param uuid: uuid
        :return: result dictionary
        """
        try:
            return self.client.doLdapSync(uuid=uuid, sync=True)
        except Fault as e:
            return e

    def do_change_dnd_status(self, **args):
        """
        Do Change DND Status
        :param userID:
        :param status:
        :return: result dictionary
        """
        try:
            return self.client.doChangeDNDStatus(**args)
        except Fault as e:
            return e

    def do_device_login(self, **args):
        """
        Do Device Login
        :param deviceName:
        :param userId:
        :param profileName:
        :return: result dictionary
        """
        try:
            return self.client.doDeviceLogin(**args)
        except Fault as e:
            return e

    def do_device_logout(self, **args):
        """
        Do Device Logout
        :param device:
        :param userId:
        :return: result dictionary
        """
        try:
            return self.client.doDeviceLogout(**args)
        except Fault as e:
            return e

    def do_device_reset(self, name="", uuid=""):
        """
        Do Device Reset
        :param name: device name
        :param uuid: device uuid
        :return: result dictionary
        """
        if name != "" and uuid == "":
            try:
                return self.client.doDeviceReset(deviceName=name, isHardReset=True)
            except Fault as e:
                return e
        elif name == "" and uuid != "":
            try:
                return self.client.doDeviceReset(uuid=uuid, isHardReset=True)
            except Fault as e:
                return e

    def reset_sip_trunk(self, name="", uuid=""):
        """
        Reset SIP Trunk
        :param name: device name
        :param uuid: device uuid
        :return: result dictionary
        """
        if name != "" and uuid == "":
            try:
                return self.client.resetSipTrunk(name=name)
            except Fault as e:
                return e
        elif name == "" and uuid != "":
            try:
                return self.client.resetSipTrunk(uuid=uuid)
            except Fault as e:
                return e

    def get_location(self, **args):
        """
        Get device pool parameters
        :param name: location name
        :param uuid: location uuid
        :return: result dictionary
        """
        try:
            return self.client.getLocation(**args)
        except Fault as e:
            return e

    def add_location(self, locationObject={}):
        """
        Add a location
        :param locationObject: JSON object for the Location
        :return: result dictionary
        """
        try:
            return self.client.addLocation(locationObject)
        except Fault as e:
            return e

    def delete_location(self, **args):
        """
        Delete a location
        :param name: The name of the location to delete
        :param uuid: The uuid of the location to delete
        :return: result dictionary
        """
        try:
            return self.client.removeLocation(**args)
        except Fault as e:
            return e

    def update_location(self, **args):
        """
        Update a Location
        :param name:
        :param uuid:
        :param newName:
        :param withinAudioBandwidth:
        :param withinVideoBandwidth:
        :param withImmersiveKbits:
        :param betweenLocations:
        :return:
        """
        try:
            return self.client.updateLocation(**args)
        except Fault as e:
            return e

    def get_regions(self, tagfilter={"uuid": "", "name": ""}):
        """
        Get region details
        :param mini: return a list of tuples of region details
        :return: A list of dictionary's
        """
        try:
            return self.client.listRegion({"name": "%"}, returnedTags=tagfilter)[
                "return"
            ]["region"]
        except Fault as e:
            return e

    def get_region(self, **args):
        """
        Get region information
        :param name: Region name
        :return: result dictionary
        """
        try:
            return self.client.getRegion(**args)
        except Fault as e:
            return e

    def add_region(self, name):
        """
        Add a region
        :param name: Name of the region to add
        :return: result dictionary
        """
        try:
            return self.client.addRegion({"name": name})
        except Fault as e:
            return e

    def update_region(self, name="", newName="", moh_region=""):
        """
        Update region and assign region to all other regions
        :param name:
        :param uuid:
        :param moh_region:
        :return:
        """
        # Get all Regions
        all_regions = self.client.listRegion(
            {"name": "%"}, returnedTags={"name": ""})
        # Make list of region names
        region_names = [str(i["name"])
                        for i in all_regions["return"]["region"]]
        # Build list of dictionaries to add to region api call
        region_list = []

        for i in region_names:
            # Highest codec within a region
            if i == name:
                region_list.append(
                    {
                        "regionName": i,
                        "bandwidth": "256 kbps",
                        "videoBandwidth": "-1",
                        "immersiveVideoBandwidth": "-1",
                        "lossyNetwork": "Use System Default",
                    }
                )

            # Music on hold region name
            elif i == moh_region:
                region_list.append(
                    {
                        "regionName": i,
                        "bandwidth": "64 kbps",
                        "videoBandwidth": "-1",
                        "immersiveVideoBandwidth": "-1",
                        "lossyNetwork": "Use System Default",
                    }
                )

            # All else G.711
            else:
                region_list.append(
                    {
                        "regionName": i,
                        "bandwidth": "64 kbps",
                        "videoBandwidth": "-1",
                        "immersiveVideoBandwidth": "-1",
                        "lossyNetwork": "Use System Default",
                    }
                )
        try:
            return self.client.updateRegion(
                name=name,
                newName=newName,
                relatedRegions={"relatedRegion": region_list},
            )
        except Fault as e:
            return e

    def delete_region(self, **args):
        """
        Delete a location
        :param name: The name of the region to delete
        :param uuid: The uuid of the region to delete
        :return: result dictionary
        """
        try:
            return self.client.removeRegion(**args)
        except Fault as e:
            return e

    def get_srsts(self, tagfilter={"uuid": ""}):
        """
        Get all SRST details
        :param mini: return a list of tuples of SRST details
        :return: A list of dictionary's
        """
        try:
            return self.client.listSrst({"name": "%"}, returnedTags=tagfilter)[
                "return"
            ]["srst"]
        except Fault as e:
            return e

    def get_srst(self, name):
        """
        Get SRST information
        :param name: SRST name
        :return: result dictionary
        """
        try:
            return self.client.getSrst(name=name)
        except Fault as e:
            return e

    def add_srst(self, SRSTObject={}):
        """
        Add SRST
        :param SRSTObject: SRST JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addSrst(SRSTObject)
        except Fault as e:
            return e

    def delete_srst(self, name):
        """
        Delete a SRST
        :param name: The name of the SRST to delete
        :return: result dictionary
        """
        try:
            return self.client.removeSrst(name=name)
        except Fault as e:
            return e

    def update_srst(self, name, newName=""):
        """
        Update a SRST
        :param srst: The name of the SRST to update
        :param newName: The new name of the SRST
        :return: result dictionary
        """
        try:
            return self.client.updateSrst(name=name, newName=newName)
        except Fault as e:
            return e

    def get_device_pools(
        self,
        tagfilter={
            "name": "",
            "dateTimeSettingName": "",
            "callManagerGroupName": "",
            "mediaResourceListName": "",
            "regionName": "",
            "srstName": "",
            # 'localRouteGroup': [0],
        },
    ):
        """
        Get a dictionary of device pools
        :param mini: return a list of tuples of device pool info
        :return: a list of dictionary's of device pools information
        """
        try:
            return self.client.listDevicePool({"name": "%"}, returnedTags=tagfilter,)[
                "return"
            ]["devicePool"]
        except Fault as e:
            return e

    def get_device_pool(self, **args):
        """
        Get device pool parameters
        :param name: device pool name
        :return: result dictionary
        """
        try:
            return self.client.getDevicePool(**args)
        except Fault as e:
            return e

    def add_device_pool(self, devicePoolObject={}):
        """
        Add a device pool
        :param devicePoolObject: Device pool Object
        :return: result dictionary
        """
        try:
            return self.client.addDevicePool(devicePoolObject)
        except Fault as e:
            return e

    def update_device_pool(self, **args):
        """
        Update a device pools route group and media resource group list
        :param name:
        :param uuid:
        :param newName:
        :param mediaResourceGroupListName:
        :param dateTimeSettingName:
        :param callManagerGroupName:
        :param regionName:
        :param locationName:
        :param networkLocale:
        :param srstName:
        :param localRouteGroup:
        :param elinGroup:
        :param media_resource_group_list:
        :return:
        """
        try:
            return self.client.updateDevicePool(**args)
        except Fault as e:
            print("Error in updating Device Pool- ", str(e))
            return e

    def delete_device_pool(self, **args):
        """
        Delete a Device pool
        :param device_pool: The name of the Device pool to delete
        :return: result dictionary
        """
        try:
            return self.client.removeDevicePool(**args)
        except Fault as e:
            return e

    def get_conference_bridges(
        self,
        tagfilter={
            "name": "",
            "description": "",
            "devicePoolName": "",
            "locationName": "",
        },
    ):
        """
        Get conference bridges
        :param mini: List of tuples of conference bridge details
        :return: results dictionary
        """
        try:
            return self.client.listConferenceBridge(
                {"name": "%"},
                returnedTags=tagfilter,
            )["return"]["conferenceBridge"]
        except Fault as e:
            return e

    def get_conference_bridge(self, name):
        """
        Get conference bridge parameters
        :param name: conference bridge name
        :return: result dictionary
        """
        try:
            return self.client.getConferenceBridge(name=name)
        except Fault as e:
            return e

    def add_conference_bridge(
        self,
        conferenceBridgeObject={},
    ):
        """
        Add a conference bridge
        :param conferenceBridgeObject: Conference bridge JSON Object
        """
        try:
            return self.client.addConferenceBridge(conferenceBridgeObject)
        except Fault as e:
            return e

    def update_conference_bridge(self, **args):
        """
        Update a conference bridge
        :param name: Conference bridge name
        :param newName: New Conference bridge name
        :param description: Conference bridge description
        :param device_pool: Device pool name
        :param location: Location name
        :param product: Conference bridge type
        :param security_profile: Conference bridge security type
        :return: result dictionary
        """
        try:
            return self.client.updateConferenceBridge(**args)
        except Fault as e:
            return e

    def delete_conference_bridge(self, name):
        """
        Delete a Conference bridge
        :param name: The name of the Conference bridge to delete
        :return: result dictionary
        """
        try:
            return self.client.removeConferenceBridge(name=name)
        except Fault as e:
            return e

    def get_transcoders(
        self, tagfilter={"name": "", "description": "", "devicePoolName": ""}
    ):
        """
        Get transcoders
        :param mini: List of tuples of transcoder details
        :return: results dictionary
        """
        try:
            return self.client.listTranscoder({"name": "%"}, returnedTags=tagfilter,)[
                "return"
            ]["transcoder"]
        except Fault as e:
            return e

    def get_transcoder(self, name):
        """
        Get conference bridge parameters
        :param name: transcoder name
        :return: result dictionary
        """
        try:
            return self.client.getTranscoder(name=name)
        except Fault as e:
            return e

    def add_transcoder(
        self,
        transcoderObject={},
    ):
        """
        Add a transcoder
        :param transcoderObject: Transcoder JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addTranscoder(transcoderObject)
        except Fault as e:
            return e

    def update_transcoder(self, **args):
        """
        Add a transcoder
        :param name: Transcoder name
        :param newName: New Transcoder name
        :param description: Transcoder description
        :param device_pool: Transcoder device pool
        :param product: Trancoder product
        :return: result dictionary
        """
        try:
            return self.client.updateTranscoder(**args)
        except Fault as e:
            return e

    def delete_transcoder(self, name):
        """
        Delete a Transcoder
        :param name: The name of the Transcoder to delete
        :return: result dictionary
        """
        try:
            return self.client.removeTranscoder(name=name)
        except Fault as e:
            return e

    def get_mtps(self, tagfilter={"name": "", "description": "", "devicePoolName": ""}):
        """
        Get mtps
        :param mini: List of tuples of transcoder details
        :return: results dictionary
        """
        try:
            return self.client.listMtp({"name": "%"}, returnedTags=tagfilter,)[
                "return"
            ]["mtp"]
        except Fault as e:
            return e

    def get_mtp(self, name):
        """
        Get mtp parameters
        :param name: transcoder name
        :return: result dictionary
        """
        try:
            return self.client.getMtp(name=name)
        except Fault as e:
            return e

    def add_mtp(
        self,
        mtpObject={},
    ):
        """
        Add an mtp
        :param mtpObject: MTP JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addMtp(mtpObject)
        except Fault as e:
            return e

    def update_mtp(self, **args):
        """
        Update an MTP
        :param name: MTP name
        :param newName: New MTP name
        :param description: MTP description
        :param device_pool: MTP device pool
        :param mtpType: MTP Type
        :return: result dictionary
        """
        try:
            return self.client.updateMtp(**args)
        except Fault as e:
            return e

    def delete_mtp(self, name):
        """
        Delete an MTP
        :param name: The name of the Transcoder to delete
        :return: result dictionary
        """
        try:
            return self.client.removeMtp(name=name)
        except Fault as e:
            return e

    def get_h323_gateways(
        self,
        tagfilter={
            "name": "",
            "description": "",
            "devicePoolName": "",
            "locationName": "",
            "sigDigits": "",
        },
    ):
        """
        Get H323 Gateways
        :param mini: List of tuples of H323 Gateway details
        :return: results dictionary
        """
        try:
            return self.client.listH323Gateway({"name": "%"}, returnedTags=tagfilter,)[
                "return"
            ]["h323Gateway"]
        except Fault as e:
            return e

    def get_h323_gateway(self, name):
        """
        Get H323 Gateway parameters
        :param name: H323 Gateway name
        :return: result dictionary
        """
        try:
            return self.client.getH323Gateway(name=name)
        except Fault as e:
            return e

    def add_h323_gateway(self, **args):
        """
        Add H323 gateway
        :param h323_gateway:
        :param description:
        :param device_pool:
        :param location:
        :param media_resource_group_list: Media resource group list name
        :param prefix_dn:
        :param sig_digits: Significant digits, 99 = ALL
        :param css:
        :param aar_css:
        :param aar_neighborhood:
        :param product:
        :param protocol:
        :param protocol_side:
        :param pstn_access:
        :param redirect_in_num_ie:
        :param redirect_out_num_ie:
        :param cld_party_ie_num_type:
        :param clng_party_ie_num_type:
        :param clng_party_nat_pre:
        :param clng_party_inat_prefix:
        :param clng_party_unknown_prefix:
        :param clng_party_sub_prefix:
        :param clng_party_nat_strip_digits:
        :param clng_party_inat_strip_digits:
        :param clng_party_unknown_strip_digits:
        :param clng_party_sub_strip_digits:
        :param clng_party_nat_trans_css:
        :param clng_party_inat_trans_css:
        :param clng_party_unknown_trans_css:
        :param clng_party_sub_trans_css:
        :return:
        """
        try:
            return self.client.addH323Gateway(**args)
        except Fault as e:
            return e

    def update_h323_gateway(self, **args):
        """

        :param name:
        :return:
        """
        try:
            return self.client.updateH323Gateway(**args)
        except Fault as e:
            return e

    def delete_h323_gateway(self, name):
        """
        Delete a H323 gateway
        :param name: The name of the H323 gateway to delete
        :return: result dictionary
        """
        try:
            return self.client.removeH323Gateway(name=name)
        except Fault as e:
            return e

    def get_route_groups(self, tagfilter={"name": "", "distributionAlgorithm": ""}):
        """
        Get route groups
        :param mini: return a list of tuples of route group details
        :return: A list of dictionary's
        """
        try:
            return self.client.listRouteGroup({"name": "%"}, returnedTags=tagfilter)[
                "return"
            ]["routeGroup"]
        except Fault as e:
            return e

    def get_route_group(self, **args):
        """
        Get route group
        :param name: route group name
        :param uuid: route group uuid
        :return: result dictionary
        """
        try:
            return self.client.getRouteGroup(**args)
        except Fault as e:
            return e

    def add_route_group(self, routeGroupObject={}):
        """
        Add a route group
        :param routeGroupObject: Route group JSON Object
        """
        try:
            return self.client.addRouteGroup(routeGroupObject)
        except Fault as e:
            return e

    def delete_route_group(self, **args):
        """
        Delete a Route group
        :param name: The name of the Route group to delete
        :return: result dictionary
        """
        try:
            return self.client.removeRouteGroup(**args)
        except Fault as e:
            return e

    def update_route_group(self, **args):
        """
        Update a Route group
        :param name: The name of the Route group to update
        :param distribution_algorithm: Top Down/Circular
        :param members: A list of devices to add (must already exist DUH!)
        :return: result dictionary
        """
        try:
            return self.client.updateRouteGroup(**args)
        except Fault as e:
            return e

    def get_route_lists(self, tagfilter={"name": "", "description": ""}):
        """
        Get route lists
        :param mini: return a list of tuples of route list details
        :return: A list of dictionary's
        """
        try:
            return self.client.listRouteList({"name": "%"}, returnedTags=tagfilter)[
                "return"
            ]["routeList"]
        except Fault as e:
            return e

    def get_route_list(self, **args):
        """
        Get route list
        :param name: route list name
        :param uuid: route list uuid
        :return: result dictionary
        """
        try:
            return self.client.getRouteList(**args)
        except Fault as e:
            return e

    def add_route_list(self, routeListObject={}):
        """
        Add a route list
        :param routeListObject: Route list JSON Object
        :return:
        """

        try:
            return self.client.addRouteList(routeListObject)
        except Fault as e:
            return e

    def delete_route_list(self, **args):
        """
        Delete a Route list
        :param name: The name of the Route list to delete
        :param uuid: The uuid of the Route list to delete
        :return: result dictionary
        """
        try:
            return self.client.removeRouteList(**args)
        except Fault as e:
            return e

    def update_route_list(self, **args):
        """
        Update a Route list
        :param name: The name of the Route list to update
        :param uuid: The uuid of the Route list to update
        :param description: Route list description
        :param cm_group_name: Route list call mangaer group name
        :param route_list_enabled: Enable route list
        :param run_on_all_nodes: Run route list on all nodes
        :param members: A list of route groups
        :return: result dictionary
        """
        try:
            return self.client.updateRouteList(**args)
        except Fault as e:
            return e

    def get_partitions(self, tagfilter={"name": "", "description": ""}):
        """
        Get partitions
        :param mini: return a list of tuples of partition details
        :return: A list of dictionary's
        """
        try:
            return self.client.listRoutePartition(
                {"name": "%"}, returnedTags=tagfilter
            )["return"]["routePartition"]
        except Fault as e:
            return e

    def get_partition(self, **args):
        """
        Get partition details
        :param partition: Partition name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getRoutePartition(**args)
        except Fault as e:
            return e

    def add_partition(self, partitionObject={}):
        """
        Add a partition
        :param partitionObject: Partition JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addRoutePartition(partitionObject)
        except Fault as e:
            return e

    def delete_partition(self, **args):
        """
        Delete a partition
        :param partition: The name of the partition to delete
        :return: result dictionary
        """
        try:
            return self.client.removeRoutePartition(**args)
        except Fault as e:
            return e

    def update_partition(self, **args):
        """
        Update calling search space
        :param uuid: CSS UUID
        :param name: CSS Name
        :param description:
        :param newName:
        :param timeScheduleIdName:
        :param useOriginatingDeviceTimeZone:
        :param timeZone:
        :return: result dictionary
        """
        try:
            return self.client.updateRoutePartition(**args)
        except Fault as e:
            return e

    def get_calling_search_spaces(self, tagfilter={"name": "", "description": ""}):
        """
        Get calling search spaces
        :param mini: return a list of tuples of css details
        :return: A list of dictionary's
        """
        try:
            return self.client.listCss({"name": "%"}, returnedTags=tagfilter)["return"][
                "css"
            ]
        except Fault as e:
            return e

    def get_calling_search_space(self, **css):
        """
        Get Calling search space details
        :param name: Calling search space name
        :param uuid: Calling search space uuid
        :return: result dictionary
        """
        try:
            return self.client.getCss(**css)
        except Fault as e:
            return e

    def add_calling_search_space(self, cssObject={}):
        """
        Add a Calling search space
        :param cssObject: CSS JSON Object
        :return: result dictionary
        """

        try:
            return self.client.addCss(cssObject)
        except Fault as e:
            return e

    def delete_calling_search_space(self, **args):
        """
        Delete a Calling search space
        :param calling_search_space: The name of the partition to delete
        :return: result dictionary
        """
        try:
            return self.client.removeCss(**args)
        except Fault as e:
            return e

    def update_calling_search_space(self, **args):
        """
        Update calling search space
        :param uuid: CSS UUID
        :param name: CSS Name
        :param description:
        :param newName:
        :param members:
        :param removeMembers:
        :param addMembers:
        :return: result dictionary
        """
        try:
            return self.client.updateCss(**args)
        except Fault as e:
            return e

    def get_route_patterns(
        self,
        tagfilter={
            "pattern": "",
            "description": "",
            "routePartitionName": "",
            "uuid": "",
        },
        SearchCriteria={"pattern": "%"},
    ):
        """
        Get route patterns
        :param mini: return a list of tuples of route pattern details
        :return: A list of dictionary's
        """
        try:
            return self.client.listRoutePattern(
                SearchCriteria,
                returnedTags=tagfilter,
            )["return"]
        except Fault as e:
            return e

    def get_route_pattern(self, pattern="", uuid=""):
        """
        Get route pattern
        :param pattern: route pattern
        :param uuid: route pattern uuid
        :return: result dictionary
        """
        if uuid == "" and pattern != "":
            # Cant get pattern directly so get UUID first
            try:
                uuid = self.client.listRoutePattern(
                    {"pattern": pattern}, returnedTags={"uuid": ""}
                )
            except Fault as e:
                return e
            if "return" in uuid and uuid["return"] is not None:
                uuid = uuid["return"]["routePattern"][0]["uuid"]
                try:
                    return self.client.getRoutePattern(uuid=uuid)
                except Fault as e:
                    return e

        elif uuid != "" and pattern == "":
            try:
                return self.client.getRoutePattern(uuid=uuid)
            except Fault as e:
                return e

    def add_route_pattern(self, routePatternObject={}):
        """
        Add a route pattern
        :param routePatternObject: Route pattern JSON Object
        :return:
        """

        try:
            return self.client.addRoutePattern(routePatternObject)
        except Fault as e:
            return e

    def delete_route_pattern(self, **args):
        """
        Delete a route pattern
        :param uuid: The pattern uuid
        :param pattern: The pattern of the route to delete
        :param partition: The name of the partition
        :return: result dictionary
        """
        try:
            return self.client.removeRoutePattern(**args)
        except Fault as e:
            return e

    def update_route_pattern(self, **args):
        """
        Update a route pattern
        :param uuid: The pattern uuid
        :param pattern: The pattern of the route to update
        :param partition: The name of the partition
        :param gateway: Destination gateway - required
        :param route_list: Destination route list - required
               Either a gateway or route list can be used at the same time
        :param description: Route pattern description
        :param partition: Route pattern partition
        :return: result dictionary
        """
        try:
            return self.client.updateRoutePattern(**args)
        except Fault as e:
            return e

    def get_media_resource_groups(self, tagfilter={"name": "", "description": ""}):
        """
        Get media resource groups
        :param mini: return a list of tuples of route pattern details
        :return: A list of dictionary's
        """
        try:
            return self.client.listMediaResourceGroup(
                {"name": "%"}, returnedTags=tagfilter
            )["return"]["mediaResourceGroup"]
        except Fault as e:
            return e

    def get_media_resource_group(self, name):
        """
        Get a media resource group details
        :param media_resource_group: Media resource group name
        :return: result dictionary
        """
        try:
            return self.client.getMediaResourceGroup(name=name)
        except Fault as e:
            return e

    def add_media_resource_group(self, mediaResourceGroupObject={}):
        """
        Add a media resource group
        :param mediaResourceGroupObject: Media resource group JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addMediaResourceGroup(mediaResourceGroupObject)
        except Fault as e:
            return e

    def update_media_resource_group(self, **args):
        """
        Update a media resource group
        :param name: Media resource group name
        :param description: Media resource description
        :param multicast: Mulicast enabled
        :param members: Media resource group members
        :return: result dictionary
        """
        try:
            return self.client.updateMediaResourceGroup(**args)
        except Fault as e:
            return e

    def delete_media_resource_group(self, name):
        """
        Delete a Media resource group
        :param media_resource_group: The name of the media resource group to delete
        :return: result dictionary
        """
        try:
            return self.client.removeMediaResourceGroup(name=name)
        except Fault as e:
            return e

    def get_media_resource_group_lists(self, tagfilter={"name": ""}):
        """
        Get media resource groups
        :param mini: return a list of tuples of route pattern details
        :return: A list of dictionary's
        """
        try:
            return self.client.listMediaResourceList(
                {"name": "%"}, returnedTags=tagfilter
            )["return"]["mediaResourceList"]
        except Fault as e:
            return e

    def get_media_resource_group_list(self, name):
        """
        Get a media resource group list details
        :param name: Media resource group list name
        :return: result dictionary
        """
        try:
            return self.client.getMediaResourceList(name=name)
        except Fault as e:
            return e

    def add_media_resource_group_list(self, mediaResouceGroupListObject={}):
        """
        Add a media resource group list
        :param mediaResouceGroupListObject: Media resource group list JSON Object
        :param members: A list of members
        :return:
        """
        try:
            return self.client.addMediaResourceList(mediaResouceGroupListObject)
        except Fault as e:
            return e

    def update_media_resource_group_list(self, **args):
        """
        Update a media resource group list
        :param name: Media resource group name
        :param description: Media resource description
        :param multicast: Mulicast enabled
        :param members: Media resource group members
        :return: result dictionary
        """
        try:
            return self.client.updateMediaResourceList(**args)
        except Fault as e:
            return e

    def delete_media_resource_group_list(self, name):
        """
        Delete a Media resource group list
        :param name: The name of the media resource group list to delete
        :return: result dictionary
        """
        try:
            return self.client.removeMediaResourceList(name=name)
        except Fault as e:
            return e

    def get_directory_numbers(
        self,
        tagfilter={
            "pattern": "",
            "description": "",
            "routePartitionName": "",
        },
        SearchCriteria={"pattern": "%"},
    ):
        """
        Get directory numbers
        :param pattern: SearchCriteria object
        :param mini: return a list of tuples of directory number details
        :return: A list of dictionary's
        """
        try:
            return self.client.listLine(SearchCriteria, returnedTags=tagfilter,)[
                "return"
            ]["line"]
        except Fault as e:
            return e

    def get_directory_number(self, **args):
        """
        Get directory number details
        :param name:
        :param partition:
        :return: result dictionary
        """
        try:
            return self.client.getLine(**args)
        except Fault as e:
            return e

    def add_directory_number(self, directoryObject={}):
        """
        Add a directory number
        :param directoryObject: Directory number JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addLine(directoryObject)
        except Fault as e:
            return e

    def delete_directory_number(self, pattern="", routePartitionName="", uuid=""):
        """
        Delete a directory number
        :param directory_number: The name of the directory number to delete
        :return: result dictionary
        """
        if uuid != "":
            try:
                return self.client.removeLine(uuid=uuid)
            except Fault as e:
                return e
        else:
            try:
                return self.client.removeLine(
                    pattern=pattern, routePartitionName=routePartitionName
                )
            except Fault as e:
                return e

    def update_directory_number(self, **args):
        """
        Update a directory number
        :param pattern: Directory number
        :param partition: Route partition name
        :param description: Directory number description
        :param alerting_name: Alerting name
        :param ascii_alerting_name: ASCII alerting name
        :param shared_line_css: Calling search space
        :param aar_neighbourhood: AAR group
        :param call_forward_css: Call forward calling search space
        :param vm_profile_name: Voice mail profile
        :param aar_destination_mask: AAR destination mask
        :param call_forward_destination: Call forward destination
        :param forward_all_to_vm: Forward all to voice mail checkbox
        :param forward_all_destination: Forward all destination
        :param forward_to_vm: Forward to voice mail checkbox
        :return: result dictionary
        """
        try:
            return self.client.updateLine(**args)
        except Fault as e:
            return e

    def update_line(self, **args):
        """
        Update a directory number
        :param pattern: Directory number
        :param partition: Route partition name
        :param description: Directory number description
        :param alerting_name: Alerting name
        :param ascii_alerting_name: ASCII alerting name
        :param shared_line_css: Calling search space
        :param aar_neighbourhood: AAR group
        :param call_forward_css: Call forward calling search space
        :param vm_profile_name: Voice mail profile
        :param aar_destination_mask: AAR destination mask
        :param call_forward_destination: Call forward destination
        :param forward_all_to_vm: Forward all to voice mail checkbox
        :param forward_all_destination: Forward all destination
        :param forward_to_vm: Forward to voice mail checkbox
        :return: result dictionary
        """
        try:
            #if tag E164AltNum has value, tag UseE164AltNum cannot be set to false
            #if tag EnterpriseAltNum has value, tag UseEnterpriseAltNum cannot be set to false
            NOTSET = ["false", False, "f", "False", 0, "0"]
            if "useE164AltNum" in args and args["useE164AltNum"] in NOTSET:
                if "e164AltNum" in args:
                    del args["e164AltNum"]
            if "useEnterpriseAltNum" in args and args["useEnterpriseAltNum"] in NOTSET:
                if "enterpriseAltNum" in args:
                    del args["enterpriseAltNum"]
            return self.client.updateLine(**args)
        except Fault as e:
            return e

    def update_directory_number_advance(self, dirnObject={}):
        """
        Update a directory number
        :param pattern: Directory number
        :param partition: Route partition name
        :param description: Directory number description
        :param alerting_name: Alerting name
        :param ascii_alerting_name: ASCII alerting name
        :param shared_line_css: Calling search space
        :param aar_neighbourhood: AAR group
        :param call_forward_css: Call forward calling search space
        :param vm_profile_name: Voice mail profile
        :param aar_destination_mask: AAR destination mask
        :param call_forward_destination: Call forward destination
        :param forward_all_to_vm: Forward all to voice mail checkbox
        :param forward_all_destination: Forward all destination
        :param forward_to_vm: Forward to voice mail checkbox
        :return: result dictionary
        """
        try:
            #if tag E164AltNum has value, tag UseE164AltNum cannot be set to false
            #if tag EnterpriseAltNum has value, tag UseEnterpriseAltNum cannot be set to false
            NOTSET = ["false", False, "f", "False", 0, "0"]
            if "UseE164AltNum" in dirnObject and dirnObject["UseE164AltNum"] in NOTSET:
                if "e164AltNum" in dirnObject:
                    del dirnObject["e164AltNum"]
            if "UseEnterpriseAltNum" in dirnObject and dirnObject["UseEnterpriseAltNum"] in NOTSET:
                if "enterpriseAltNum" in dirnObject:
                    del dirnObject["enterpriseAltNum"]

            return self.client.updateLine(dirnObject)
        except Fault as e:
            return e

    def get_cti_route_points(
        self, tagfilter={"name": "", "description": ""}, SearchCriteria={"name": "%"}
    ):
        """
        Get CTI route points
        :param mini: return a list of tuples of CTI route point details
        :return: A list of dictionary's
        """
        try:
            return self.client.listCtiRoutePoint(
                SearchCriteria, returnedTags=tagfilter
            )["return"]
        except Fault as e:
            return e

    def get_cti_route_point(self, **args):
        """
        Get CTI route point details
        :param name: CTI route point name
        :param uuid: CTI route point uuid
        :return: result dictionary
        """
        try:
            return self.client.getCtiRoutePoint(**args)
        except Fault as e:
            return e

    def add_cti_route_point(self, ctiRoutePointObject={}):
        """
        Add CTI route point
        :param ctiRoutePointObject: CTI route point JSON Object
        :return:
        """

        try:
            return self.client.addCtiRoutePoint(ctiRoutePointObject)
        except Fault as e:
            return e

    def delete_cti_route_point(self, **args):
        """
        Delete a CTI route point
        :param cti_route_point: The name of the CTI route point to delete
        :return: result dictionary
        """
        try:
            return self.client.removeCtiRoutePoint(**args)
        except Fault as e:
            return e

    def update_cti_route_point(self, **args):
        """
        Add CTI route point
        lines should be a list of tuples containing the pattern and partition
        EG: [('77777', 'AU_PHONE_PT')]
        :param name: CTI route point name
        :param description: CTI route point description
        :param device_pool: Device pool name
        :param location: Location name
        :param common_device_config: Common device config name
        :param css: Calling search space name
        :param product: CTI device type
        :param dev_class: CTI device type
        :param protocol: CTI protocol
        :param protocol_slide: CTI protocol slide
        :param use_trusted_relay_point: Use trusted relay point: (Default, On, Off)
        :param lines: A list of tuples of [(directory_number, partition)]
        :return:
        """
        try:
            return self.client.updateCtiRoutePoint(**args)
        except Fault as e:
            return e

    def get_phones(
        self,
        tagfilter={
            "name": "",
            "product": "",
            "description": "",
            "protocol": "",
            "locationName": "",
            "callingSearchSpaceName": "",
            "devicePoolName": "",
        },
        SearchCriteria={"name": "%"},
    ):
        try:
            skip = 0
            a = []

            def inner(skip):
                while True:
                    res = self.client.listPhone(
                        SearchCriteria, returnedTags=tagfilter, first=1000, skip=skip
                    )["return"]
                    skip = skip + 1000
                    if res is not None and "phone" in res:
                        yield res["phone"]
                    else:
                        break

            for each in inner(skip):
                a.extend(each)
            return a
        except Fault as e:
            return e

    def get_phone(self, **args):
        """
        Get device profile parameters
        :param phone: profile name
        :return: result dictionary
        """
        try:
            return self.client.getPhone(**args)["return"]["phone"]
        except Fault as e:
            return e

    def add_phone(self, phoneObject={}):
        """
        Add A phone
        :param phoneObject: Phone Config Object
        :return:
        """
        try:
            return self.client.addPhone(phoneObject)
        except Fault as e:
            if "Vendor Configuration" in str(e):
                try:
                    del phoneObject['vendorConfig']
                    return self.client.addPhone(phoneObject)
                except Fault as e:
                    return e
            else:
                return e

    def delete_phone(self, **args):
        """
        Delete a phone
        :param phone: The name of the phone to delete
        :return: result dictionary
        """
        try:
            return self.client.removePhone(**args)
        except Fault as e:
            return e

    def update_phone(self, **args):
        """
        lines takes a list of Tuples with properties for each line EG:

                                               display                           external
            DN     partition    display        ascii          label               mask
        [('77777', 'LINE_PT', 'Jim Smith', 'Jim Smith', 'Jim Smith - 77777', '0294127777')]
        Add A phone
        :param name:
        :param description:
        :param product:
        :param device_pool:
        :param location:
        :param phone_template:
        :param common_device_config:
        :param css:
        :param aar_css:
        :param subscribe_css:
        :param lines:
        :param dev_class:
        :param protocol:
        :param softkey_template:
        :param enable_em:
        :param em_service_name:
        :param em_service_url:
        :param em_url_button_enable:
        :param em_url_button_index:
        :param em_url_label:
        :param ehook_enable:
        :return:
        """
        # Create a Zeep xsd type object of type XVendorConfig from the client object
        # phoneObj = **args
        #VendorConfig Reference- https://github.com/CiscoDevNet/axl-python-zeep-samples/blob/master/axl_add_Phone_vendorConfig.py
        #Line no. 122 to 148

        try:
            xvcType = self.axl_client.get_type( 'ns0:XVendorConfig' )
            vendor = []
            phoneObj = args
            if "vendorConfig" in phoneObj and phoneObj["vendorConfig"] != None:
                #Adding webAccess
                for key, val in phoneObj["vendorConfig"][0].items():
                    element = etree.Element(key)
                    element.text = val
                    vendor.append(element)
                # webAccess =  etree.Element( 'webAccess' )
                # webAccess.text = '0'
                # vendor.append(webAccess)
                phoneObj[ 'vendorConfig' ] = xvcType(vendor)
            return self.client.updatePhone(**args)
        except Fault as e:
            return e

    def get_device_profiles(
        self,
        tagfilter={
            "name": "",
            "product": "",
            "protocol": "",
            "phoneTemplateName": "",
        },
    ):
        """
        Get device profile details
        :param mini: return a list of tuples of device profile details
        :return: A list of dictionary's
        """
        try:
            return self.client.listDeviceProfile(
                {"name": "%"},
                returnedTags=tagfilter,
            )["return"]["deviceProfile"]
        except Fault as e:
            return e

    def get_device_profile(self, **args):
        """
        Get device profile parameters
        :param name: profile name
        :param uuid: profile uuid
        :return: result dictionary
        """
        try:
            return self.client.getDeviceProfile(**args)
        except Fault as e:
            return e

    def add_device_profile(
        self,
        name,
        description="",
        product="Cisco 7962",
        phone_template="Standard 7962G SCCP",
        dev_class="Device Profile",
        protocol="SCCP",
        protocolSide="User",
        softkey_template="Standard User",
        em_service_name="Extension Mobility",
        lines=[],
    ):
        """
        Add A Device profile for use with extension mobility
        lines takes a list of Tuples with properties for each line EG:

                                               display                           external
            DN     partition    display        ascii          label               mask
        [('77777', 'LINE_PT', 'Jim Smith', 'Jim Smith', 'Jim Smith - 77777', '0294127777')]
        :param name:
        :param description:
        :param product:
        :param phone_template:
        :param lines:
        :param dev_class:
        :param protocol:
        :param softkey_template:
        :param em_service_name:
        :return:
        """

        req = {
            "name": name,
            "description": description,
            "product": product,
            "class": dev_class,
            "protocol": protocol,
            "protocolSide": protocolSide,
            "softkeyTemplateName": softkey_template,
            "phoneTemplateName": phone_template,
            "lines": {"line": []},
        }

        if lines:
            [
                req["lines"]["line"].append(
                    {
                        "index": lines.index(i) + 1,
                        "dirn": {"pattern": i[0], "routePartitionName": i[1]},
                        "display": i[2],
                        "displayAscii": i[3],
                        "label": i[4],
                        "e164Mask": i[5],
                    }
                )
                for i in lines
            ]

        try:
            blah = self.client.addDeviceProfile(req)
            return blah
        except Fault as e:
            return e



    def add_device_profile_advance(self,dPObject={}):
        """
        Add A Device profile for use with extension mobility
        lines takes a list of Tuples with properties for each line EG:

                                               display                           external
            DN     partition    display        ascii          label               mask
        [('77777', 'LINE_PT', 'Jim Smith', 'Jim Smith', 'Jim Smith - 77777', '0294127777')]
        :param name:
        :param description:
        :param product:
        :param phone_template:
        :param lines:
        :param dev_class:
        :param protocol:
        :param softkey_template:
        :param em_service_name:
        :return:
        """
        try:
            xvcType = self.axl_client.get_type( 'ns0:XVendorConfig' )
            vendor = []
            if "vendorConfig" in dPObject and dPObject["vendorConfig"] != None:
                #Adding webAccess
                for key, val in dPObject["vendorConfig"][0].items():
                    element = etree.Element(key)
                    element.text = val
                    vendor.append(element)
                # webAccess =  etree.Element( 'webAccess' )
                # webAccess.text = '0'
                # vendor.append(webAccess)
                dPObject[ 'vendorConfig' ] = xvcType(vendor)
            res = self.client.addDeviceProfile(dPObject)
            return res
        except Fault as e:
            return e

    def delete_device_profile(self, **args):
        """
        Delete a device profile
        :param profile: The name of the device profile to delete
        :return: result dictionary
        """
        try:
            return self.client.removeDeviceProfile(**args)
        except Fault as e:
            return e

    def update_device_profile(self, **args):
        """
        Update A Device profile for use with extension mobility
        lines takes a list of Tuples with properties for each line EG:

                                               display                           external
            DN     partition    display        ascii          label               mask
        [('77777', 'LINE_PT', 'Jim Smith', 'Jim Smith', 'Jim Smith - 77777', '0294127777')]
        :param profile:
        :param description:
        :param product:
        :param phone_template:
        :param lines:
        :param dev_class:
        :param protocol:
        :param softkey_template:
        :param em_service_name:
        :return:
        """
        try:
            return self.client.updateDeviceProfile(**args)
        except Fault as e:
            return e

    def get_users(self, tagfilter={"userid": "", "firstName": "", "lastName": ""}):
        """
        Get users details
        :return: A list of dictionary's
        """
        skip = 0
        a = []

        def inner(skip):
            while True:
                res = self.client.listUser(
                    {"userid": "%"}, returnedTags=tagfilter, first=1000, skip=skip
                )["return"]
                skip = skip + 1000
                if res is not None and "user" in res:
                    yield res["user"]
                else:
                    break

        for each in inner(skip):
            a.extend(each)
        return a

    def get_user(self, userid):
        """
        Get user parameters
        :param user_id: profile name
        :return: result dictionary
        """
        try:
            return self.client.getUser(userid=userid)["return"]["user"]
        except Fault as e:
            return e

    def add_user(
        self,
        userid,
        lastName,
        firstName,
        presenceGroupName="Standard Presence group",
        phoneProfiles=[],
    ):
        """
        Add a user
        :param user_id: User ID of the user to add
        :param first_name: First name of the user to add
        :param last_name: Last name of the user to add
        :return: result dictionary
        """

        try:
            return self.client.addUser(
                {
                    "userid": userid,
                    "lastName": lastName,
                    "firstName": firstName,
                    "presenceGroupName": presenceGroupName,
                    "phoneProfiles": phoneProfiles,
                }
            )
        except Fault as e:
            return e

    def add_user_advance(self, user_object={}):
        """
        Add a user with all the configs
        :param user_id: User ID of the user to add
        :param first_name: First name of the user to add
        :param last_name: Last name of the user to add
        :return: result dictionary
        """

        try:
            return self.client.addUser(user_object)

        except Fault as e:
            # print("Error is: ", str(e))
            if "Unknown" in str(e):
                traceback.print_exc()
            return e

    def update_user(self, **args):
        """
        Update end user for credentials
        :param userid: User ID
        :param password: Web interface password
        :param pin: Extension mobility PIN
        :return: result dictionary
        """
        try:
            return self.client.updateUser(**args)
        except Fault as e:
            return e

    def update_user_em(
        self, user_id, device_profile, default_profile, subscribe_css, primary_extension
    ):
        """
        Update end user for extension mobility
        :param user_id: User ID
        :param device_profile: Device profile name
        :param default_profile: Default profile name
        :param subscribe_css: Subscribe CSS
        :param primary_extension: Primary extension, must be a number from the device profile
        :return: result dictionary
        """
        try:
            resp = self.client.getDeviceProfile(name=device_profile)
        except Fault as e:
            return e
        if "return" in resp and resp["return"] is not None:
            uuid = resp["return"]["deviceProfile"]["uuid"]
            try:
                return self.client.updateUser(
                    userid=user_id,
                    phoneProfiles={"profileName": {"_uuid": uuid}},
                    defaultProfile=default_profile,
                    subscribeCallingSearchSpaceName=subscribe_css,
                    primaryExtension={"pattern": primary_extension},
                    associatedGroups={"userGroup": {
                        "name": "Standard CCM End Users"}},
                )
            except Fault as e:
                return e
        else:
            return "Device Profile not found for user"

    def update_user_credentials(self, userid, password="", pin=""):
        """
        Update end user for credentials
        :param userid: User ID
        :param password: Web interface password
        :param pin: Extension mobility PIN
        :return: result dictionary
        """

        if password == "" and pin == "":
            return "Password and/or Pin are required"

        elif password != "" and pin != "":
            try:
                return self.client.updateUser(userid=userid, password=password, pin=pin)
            except Fault as e:
                return e

        elif password != "":
            try:
                return self.client.updateUser(userid=userid, password=password)
            except Fault as e:
                return e

        elif pin != "":
            try:
                return self.client.updateUser(userid=userid, pin=pin)
            except Fault as e:
                return e

    def delete_user(self, **args):
        """
        Delete a user
        :param userid: The name of the user to delete
        :return: result dictionary
        """
        try:
            return self.client.removeUser(**args)
        except Fault as e:
            return e

    def get_translations(self, SearchCriteria={"pattern": "%"}):
        """
        Get translation patterns
        :param mini: return a list of tuples of route pattern details
        :return: A list of dictionary's
        """
        try:
            return self.client.listTransPattern(
                SearchCriteria,
                returnedTags={
                    "pattern": "",
                    "description": "",
                    "uuid": "",
                    "routePartitionName": "",
                    "callingSearchSpaceName": "",
                    "useCallingPartyPhoneMask": "",
                    "patternUrgency": "",
                    "provideOutsideDialtone": "",
                    "prefixDigitsOut": "",
                    "calledPartyTransformationMask": "",
                    "callingPartyTransformationMask": "",
                    "digitDiscardInstructionName": "",
                    "callingPartyPrefixDigits": "",
                    "provideOutsideDialtone": "",
                },
            )["return"]["transPattern"]
        except Fault as e:
            return e

    def get_translation(self, pattern="", routePartitionName="", uuid=""):
        """
        Get translation pattern
        :param pattern: translation pattern to match
        :param routePartitionName: routePartitionName required if searching pattern
        :param uuid: translation pattern uuid
        :return: result dictionary
        """

        if pattern != "" and routePartitionName != "" and uuid == "":
            try:
                return self.client.getTransPattern(
                    pattern=pattern,
                    routePartitionName=routePartitionName,
                    returnedTags={
                        "pattern": "",
                        "description": "",
                        "routePartitionName": "",
                        "callingSearchSpaceName": "",
                        "useCallingPartyPhoneMask": "",
                        "patternUrgency": "",
                        "provideOutsideDialtone": "",
                        "prefixDigitsOut": "",
                        "calledPartyTransformationMask": "",
                        "callingPartyTransformationMask": "",
                        "digitDiscardInstructionName": "",
                        "callingPartyPrefixDigits": "",
                    },
                )
            except Fault as e:
                return e
        elif uuid != "" and pattern == "" and routePartitionName == "":
            try:
                return self.client.getTransPattern(uuid=uuid)
            except Fault as e:
                return e
        else:
            return "must specify either uuid OR pattern and partition"

    def add_translation(self, translationPatternObject={}):
        """
        Add a translation pattern
        :param translationPatternObject: Translation pattern JSON Object
        :return:
        """
        try:
            return self.client.addTransPattern(translationPatternObject)
        except Fault as e:
            return e

    def delete_translation(self, pattern="", partition="", uuid=""):
        """
        Delete a translation pattern
        :param pattern: The pattern of the route to delete
        :param partition: The name of the partition
        :param uuid: Required if pattern and partition are not specified
        :return: result dictionary
        """

        if pattern != "" and partition != "" and uuid == "":
            try:
                return self.client.removeTransPattern(
                    pattern=pattern, routePartitionName=partition
                )
            except Fault as e:
                return e
        elif uuid != "" and pattern == "" and partition == "":
            try:
                return self.client.removeTransPattern(uuid=uuid)
            except Fault as e:
                return e
        else:
            return "must specify either uuid OR pattern and partition"

    def update_translation(
        self,
        pattern="",
        partition="",
        uuid="",
        newPattern="",
        description="",
        newRoutePartitionName="",
        callingSearchSpaceName="",
        useCallingPartyPhoneMask="",
        patternUrgency="",
        provideOutsideDialtone="",
        prefixDigitsOut="",
        calledPartyTransformationMask="",
        callingPartyTransformationMask="",
        digitDiscardInstructionName="",
        callingPartyPrefixDigits="",
        blockEnable="",
    ):
        """
        Update a translation pattern
        :param uuid: UUID or Translation + Partition Required
        :param pattern: Translation pattern
        :param partition: Route Partition
        :param description: Description - optional
        :param usage: Usage
        :param callingSearchSpaceName: Calling Search Space - optional
        :param patternUrgency: Pattern Urgency - optional
        :param provideOutsideDialtone: Provide Outside Dial Tone - optional
        :param prefixDigitsOut: Prefix Digits Out - optional
        :param calledPartyTransformationMask: - optional
        :param callingPartyTransformationMask: - optional
        :param digitDiscardInstructionName: - optional
        :param callingPartyPrefixDigits: - optional
        :param blockEnable: - optional
        :return: result dictionary
        """

        args = {}
        if description != "":
            args["description"] = description
        if pattern != "" and partition != "" and uuid == "":
            args["pattern"] = pattern
            args["routePartitionName"] = partition
        if pattern == "" and partition == "" and uuid != "":
            args["uuid"] = uuid
        if newPattern != "":
            args["newPattern"] = newPattern
        if newRoutePartitionName != "":
            args["newRoutePartitionName"] = newRoutePartitionName
        if callingSearchSpaceName != "":
            args["callingSearchSpaceName"] = callingSearchSpaceName
        if useCallingPartyPhoneMask != "":
            args["useCallingPartyPhoneMask"] = useCallingPartyPhoneMask
        if digitDiscardInstructionName != "":
            args["digitDiscardInstructionName"] = digitDiscardInstructionName
        if callingPartyTransformationMask != "":
            args["callingPartyTransformationMask"] = callingPartyTransformationMask
        if calledPartyTransformationMask != "":
            args["calledPartyTransformationMask"] = calledPartyTransformationMask
        if patternUrgency != "":
            args["patternUrgency"] = patternUrgency
        if provideOutsideDialtone != "":
            args["provideOutsideDialtone"] = provideOutsideDialtone
        if prefixDigitsOut != "":
            args["prefixDigitsOut"] = prefixDigitsOut
        if callingPartyPrefixDigits != "":
            args["callingPartyPrefixDigits"] = callingPartyPrefixDigits
        if blockEnable != "":
            args["blockEnable"] = blockEnable
        try:
            return self.client.updateTransPattern(**args)
        except Fault as e:
            return e

    def list_route_plan(self, pattern=""):
        """
        List Route Plan
        :param pattern: Route Plan Contains Pattern
        :return: results dictionary
        """
        try:
            return self.client.listRoutePlan(
                {"dnOrPattern": "%" + pattern + "%"},
                returnedTags={
                    "dnOrPattern": "",
                    "partition": "",
                    "type": "",
                    "routeDetail": "",
                },
            )["return"]["routePlan"]
        except Fault as e:
            return e

    def list_route_plan_specific(self, pattern=""):
        """
        List Route Plan
        :param pattern: Route Plan Contains Pattern
        :return: results dictionary
        """
        try:
            return self.client.listRoutePlan(
                {"dnOrPattern": pattern},
                returnedTags={
                    "dnOrPattern": "",
                    "partition": "",
                    "type": "",
                    "routeDetail": "",
                },
            )
        except Fault as e:
            return e

    def get_called_party_xforms(self,rpName):
        """
        Get called party xforms
        :param mini: return a list of tuples of called party transformation pattern details
        :return: A list of dictionary's
        """
        try:
            return self.client.listCalledPartyTransformationPattern(
                {"pattern": "%","routePartitionName": rpName},

                returnedTags={"pattern": "",
                              "description": "",
                              "usage": "",
                              "routePartitionName": "",
                              "calledPartyTransformationMask": "",
                              "dialPlanName": "",
                              "digitDiscardInstructionName": "",
                              "patternUrgency": "",
                              "calledPartyPrefixDigits": "",
                              "routeFilterName": "",
                              "calledPartyNumberingPlan": "",
                              "calledPartyNumberType": "",
                              "mlppPreemptionDisabled": ""},
            )["return"]["calledPartyTransformationPattern"]
        except Fault as e:
            return e

    def get_called_party_xform(self, **args):
        """
        Get called party xform details
        :param name:
        :param partition:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getCalledPartyTransformationPattern(**args)
        except Fault as e:
            return e

    def add_called_party_xform(
        self, calledPartyXformObj={}
    ):
        """
        Add a called party transformation pattern
        :param pattern: pattern - required
        :param routePartitionName: partition required
        :param description: Route pattern description
        :param calledPartyTransformationmask:
        :param dialPlanName:
        :param digitDiscardInstructionName:
        :param routeFilterName:
        :param calledPartyPrefixDigits:
        :param calledPartyNumberingPlan:
        :param calledPartyNumberType:
        :param mlppPreemptionDisabled: does anyone use this?
        :return: result dictionary
        """
        try:
            return self.client.addCalledPartyTransformationPattern(calledPartyXformObj)
        except Fault as e:
            return e

    def delete_called_party_xform(self, **args):
        """
        Delete a called party transformation pattern
        :param uuid: The pattern uuid
        :param pattern: The pattern of the transformation to delete
        :param partition: The name of the partition
        :return: result dictionary
        """
        try:
            return self.client.removeCalledPartyTransformationPattern(**args)
        except Fault as e:
            return e

    def update_called_party_xform(self, **args):
        """
        Update a called party transformation
        :param uuid: required unless pattern and routePartitionName is given
        :param pattern: pattern - required
        :param routePartitionName: partition required
        :param description: Route pattern description
        :param calledPartyTransformationmask:
        :param dialPlanName:
        :param digitDiscardInstructionName:
        :param routeFilterName:
        :param calledPartyPrefixDigits:
        :param calledPartyNumberingPlan:
        :param calledPartyNumberType:
        :param mlppPreemptionDisabled: does anyone use this?
        :return: result dictionary
        :return: result dictionary
        """
        try:
            return self.client.updateCalledPartyTransformationPattern(**args)
        except Fault as e:
            return e

    def get_calling_party_xforms(self,rpName):
        """
        Get calling party xforms
        :param mini: return a list of tuples of calling party transformation pattern details
        :return: A list of dictionary's
        """
        try:
            return self.client.listCallingPartyTransformationPattern(
                {"pattern": "%","routePartitionName":rpName},

                returnedTags={"pattern": "",
                              "description": "",
                              "usage": "",
                              "routePartitionName": "",
                              "callingPartyTransformationMask": "",
                              "useCallingPartyPhoneMask": "",
                              "dialPlanName": "",
                              "digitDiscardInstructionName": "",
                              "patternUrgency": "",
                              "callingPartyPrefixDigits": "",
                              "routeFilterName": "",
                              "callingLinePresentationBit": "",
                              "callingPartyNumberingPlan": "",
                              "callingPartyNumberType": "",
                              "mlppPreemptionDisabled": ""},
            )["return"]["callingPartyTransformationPattern"]
        except Fault as e:
            return e

    def get_calling_party_xform(self, **args):
        """
        Get calling party xform details
        :param name:
        :param partition:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getCallingPartyTransformationPattern(**args)
        except Fault as e:
            return e

    def add_calling_party_xform(
            self, callingPartyXformObj={}):
        """
        Add a calling party transformation pattern
        :param pattern: pattern - required
        :param routePartitionName: partition required
        :param description: Route pattern description
        :param callingPartyTransformationmask:
        :param dialPlanName:
        :param digitDiscardInstructionName:
        :param routeFilterName:
        :param callingPartyPrefixDigits:
        :param callingPartyNumberingPlan:
        :param callingPartyNumberType:
        :param mlppPreemptionDisabled: does anyone use this?
        :return: result dictionary
        """
        try:
            return self.client.addCallingPartyTransformationPattern(callingPartyXformObj)
        except Fault as e:
            return e

    def delete_calling_party_xform(self, **args):
        """
        Delete a calling party transformation pattern
        :param uuid: The pattern uuid
        :param pattern: The pattern of the transformation to delete
        :param partition: The name of the partition
        :return: result dictionary
        """
        try:
            return self.client.removeCallingPartyTransformationPattern(**args)
        except Fault as e:
            return e

    def update_calling_party_xform(self, **args):
        """
        Update a calling party transformation
        :param uuid: required unless pattern and routePartitionName is given
        :param pattern: pattern - required
        :param routePartitionName: partition required
        :param description: Route pattern description
        :param calledPartyTransformationmask:
        :param dialPlanName:
        :param digitDiscardInstructionName:
        :param routeFilterName:
        :param calledPartyPrefixDigits:
        :param calledPartyNumberingPlan:
        :param calledPartyNumberType:
        :param mlppPreemptionDisabled: does anyone use this?
        :return: result dictionary
        :return: result dictionary
        """
        try:
            return self.client.updateCallingPartyTransformationPattern(**args)
        except Fault as e:
            return e

    def get_sip_trunks(
        self, tagfilter={"name": "", "sipProfileName": "",
                         "callingSearchSpaceName": ""}
    ):
        try:
            return self.client.listSipTrunk({"name": "%"}, returnedTags=tagfilter)[
                "return"
            ]["sipTrunk"]
        except Fault as e:
            return e

    def get_sip_trunk(self, **args):
        """
        Get sip trunk
        :param name:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getSipTrunk(**args)
        except Fault as e:
            return e

    def update_sip_trunk(self, **args):
        """
        Update a SIP Trunk
        :param name:
        :param uuid:
        :param newName:
        :param description:
        :param callingSearchSpaceName:
        :param devicePoolName:
        :param locationName:
        :param sipProfileName:
        :param mtpRequired:

        :return:
        """
        try:
            return self.client.updateSipTrunk(**args)
        except Fault as e:
            return e

    def delete_sip_trunk(self, **args):
        try:
            return self.client.removeSipTrunk(**args)
        except Fault as e:
            return e

    def get_sip_security_profile(self, name):
        try:
            return self.client.getSipTrunkSecurityProfile(name=name)["return"]
        except Fault as e:
            return e

    def get_sip_profile(self, name):
        try:
            return self.client.getSipProfile(name=name)["return"]
        except Fault as e:
            return e

    def add_sip_trunk(self, sipTrunkObject={}):
        """
        Add a SIP Trunk
        :param sipTrunkObject: SIP Trunk JSON Object
        :return:
        """
        try:
            return self.client.addSipTrunk(sipTrunkObject)
        except Fault as e:
            print(str(e))
            return e

    def list_process_nodes(self):
        try:
            return self.client.listProcessNode(
                {"name": "%", "processNodeRole": "CUCM Voice/Video"},
                returnedTags={"name": ""},
            )["return"]["processNode"]
        except Fault as e:
            return e

    def add_call_manager_group(self, name, members):
        """
        Add call manager group
        :param name: name of cmg
        :param members[]: array of members
        :return: result dictionary
        """

        try:
            return self.client.addCallManagerGroup({"name": name, "members": members})
        except Fault as e:
            return e

    def get_call_manager_group(self, name):
        """
        Get call manager group
        :param name: name of cmg
        :return: result dictionary
        """
        try:
            return self.client.getCallManagerGroup(name=name)
        except Fault as e:
            return e

    def get_call_manager_groups(self):
        """
        Get call manager groups
        :param name: name of cmg
        :return: result dictionary
        """
        try:
            return self.client.listCallManagerGroup(
                {"name": "%"}, returnedTags={"name": ""}
            )["return"]["callManagerGroup"]
        except Fault as e:
            return e

    def update_call_manager_group(self, **args):
        """
        Update call manager group
        :param name: name of cmg
        :return: result dictionary
        """
        try:
            return self.client.listCallManagerGroup({**args}, returnedTags={"name": ""})
        except Fault as e:
            return e

    def delete_call_manager_group(self, name):
        """
        Delete call manager group
        :param name: name of cmg
        :return: result dictionary
        """
        try:
            return self.client.removeCallManagerGroup({"name": name})
        except Fault as e:
            return e

    def get_huntlist(self, **args):
        """
        Get huntlist details
        :param name: HuntList name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getHuntList(**args)
        except Fault as e:
            return e

    def get_callpark(self, **args):
        """
        Get callPark details
        :param pattern: Call Park pattern
        :param routePartitionName: Route Partition name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getCallPark(**args)
        except Fault as e:
            return e

    def add_callpark(self, callParkObject={}):
        """
        Get callPark details
        :param callParkObject: Call Park Object in JSON
        :return: result dictionary
        """
        try:
            return self.client.addCallPark(callParkObject)
        except Fault as e:
            return e

    def get_directedcallpark(self, **args):
        """
        Get callPark details
        :param pattern: Directed Call Park pattern
        :param routePartitionName: Route Partition name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getDirectedCallPark(**args)
        except Fault as e:
            return e

    def add_directedcallpark(self, directedcallParkObject={}):
        """
        Get callPark details
        :param directedcallParkObject: Call Park Object in JSON
        :return: result dictionary
        """
        try:
            return self.client.addDirectedCallPark(directedcallParkObject)
        except Fault as e:
            return e

    def get_huntpilot(self, **args):
        """
        Get huntpilot details
        :param pattern: pattern name
        :param routePartitionName: partition name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getHuntPilot(**args)
        except Fault as e:
            return e

    def get_huntpilots(
        self,
        tagfilter={
            "pattern": "",
            "description": "",
            "routePartitionName": "",
        },
        SearchCriteria={"pattern": "%"},
    ):
        """
        Get huntpilot numbers
        :param pattern: SearchCriteria object
        :param mini: return a list of tuples of directory number details
        :return: A list of dictionary's
        """
        try:
            return self.client.listHuntPilot(
                SearchCriteria,
                returnedTags=tagfilter,
            )["return"]
        except Fault as e:
            return e

    def get_line_group(self, **args):
        """
        Get route group
        :param name: route group name
        :param uuid: route group uuid
        :return: result dictionary
        """
        try:
            return self.client.getLineGroup(**args)
        except Fault as e:
            return e

    def get_h323_trunk(self, **args):
        """
        Get route group
        :param name: route group name
        :param uuid: route group uuid
        :return: result dictionary
        """
        try:
            return self.client.getH323Trunk(**args)
        except Fault as e:
            return e

    def get_voicemailpilots(
        self,
        tagfilter={
            "dirn": "",
            "description": "",
        },
        SearchCriteria={"dirn": "%"},
    ):
        """
        Get huntpilot numbers
        :param pattern: SearchCriteria object
        :param mini: return a list of tuples of directory number details
        :return: A list of dictionary's
        """
        try:
            return self.client.listVoiceMailPilot(
                SearchCriteria,
                returnedTags=tagfilter,
            )["return"]
        except Fault as e:
            return e

    def get_voicemailpilot(self, **args):
        """
        Get directory number details
        :param name:
        :param partition:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getVoiceMailPilot(**args)
        except Fault as e:
            return e

    def add_voicemailpilot(self, voicemailpilotObject={}):
        """
        Get directory number details
        :param voicemailpilotObject: VoiceMail Pilot Object
        :return: result dictionary
        """
        try:
            return self.client.addVoiceMailPilot(voicemailpilotObject)
        except Fault as e:
            return e

    def add_voicemailprofile(self, voicemailprofileObject={}):
        """
        Get directory number details
        :param voicemailprofileObject: VoiceMail Profile Object
        :return: result dictionary
        """
        try:
            return self.client.addVoiceMailProfile(voicemailprofileObject)
        except Fault as e:
            return e

    def get_voicemailprofile(self, **args):
        """
        Get directory number details
        :param name:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getVoiceMailProfile(**args)
        except Fault as e:
            return e

    def add_ctiport(self, ctiportObject={}):
        try:
            return self.client.addPhone(ctiportObject)
        except Fault as e:
            return e

    def add_linegroup(self, linegroupObject={}):
        try:
            return self.client.addLineGroup(linegroupObject)
        except Fault as e:
            return e

    def add_huntlist(self, huntListObject={}):
        """
        Get huntlist details
        :param huntListObject: HuntList JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addHuntList(huntListObject)
        except Fault as e:
            return e

    def add_huntpilot(self, huntPilotObject={}):
        """
        Get huntpilot details
        :param huntPilotObject: Hunt Pilot JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addHuntPilot(huntPilotObject)
        except Fault as e:
            return e

    # Section on Standard Configurations
    def get_softkey_template(self, **args):
        """
        :param name:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getSoftKeyTemplate(**args)
        except Fault as e:
            return e

    def add_softkey_template(self, softkeyTemplateObject={}):
        """
        :param softkeyTemplateObject: Softkey template JSON object
        :return: result dictionary
        """
        try:
            return self.client.addSoftKeyTemplate(softkeyTemplateObject)
        except Fault as e:
            return e

    def get_common_device_config(self, **args):
        """
        :param name:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getCommonDeviceConfig(**args)
        except Fault as e:
            return e

    def add_common_device_config(self, commonDeviceConfigObject={}):
        """
        :param commonDeviceConfigObject: Common Device Config JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addCommonDeviceConfig(commonDeviceConfigObject)
        except Fault as e:
            return e

    def get_common_phone_config(self, **args):
        """
        :param name:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getCommonPhoneConfig(**args)
        except Fault as e:
            return e

    def add_common_phone_config(self, commonPhoneConfigObject={}):
        """
        :param commonPhoneConfigObject: Common Phone Config JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addCommonPhoneConfig(commonPhoneConfigObject)
        except Fault as e:
            return e

    def get_phone_security_profile(self, **args):
        """
        :param name:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getPhoneSecurityProfile(**args)
        except Fault as e:
            return e

    def add_phone_security_profile(self, phoneSecurityProfileObject={}):
        """
        :param phoneSecurityProfileObject: Phone Security Profile JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addPhoneSecurityProfile(phoneSecurityProfileObject)
        except Fault as e:
            return e

    def get_phone_button_template(self, **args):
        """
        :param name:
        :param uuid:
        :return: result dictionary
        """
        try:
            return self.client.getPhoneButtonTemplate(**args)
        except Fault as e:
            return e

    def add_phone_button_template(self, phoneButtonTemplateObject={}):
        """
        :param phoneButtonTemplateObject: Phone Button Template JSON Object
        :return: result dictionary
        """
        try:
            return self.client.addPhoneButtonTemplate(phoneButtonTemplateObject)
        except Fault as e:
            return e

    def get_gateway(self, **args):
        """
        :param domainName:
        :return: result dictionary
        """
        try:
            return self.client.getGateway(**args)
        except Fault as e:
            return e

    def add_gateway(self, gatewayObject={}):
        """
        :param gatewayObject: Gateway JSON Object
        :return:
        """
        try:
            return self.client.addGateway(gatewayObject)
        except Fault as e:
            return e
    
    def update_gateway(self, **args):
        """
        :param gatewayObject: Gateway JSON Object
        :return:
        """
        xvcType = self.axl_client.get_type( 'ns0:XVendorConfig' )
        vendor = []
        gatewayObj = args
        if "vendorConfig" in gatewayObj and gatewayObj["vendorConfig"] != None:
            #Adding webAccess
            for key, val in gatewayObj["vendorConfig"][0].items():
                element = etree.Element(key)
                element.text = val
                vendor.append(element)
            # webAccess =  etree.Element( 'webAccess' )
            # webAccess.text = '0'
            # vendor.append(webAccess)
            gatewayObj[ 'vendorConfig' ] = xvcType(vendor)
        try:
            return self.client.updateGateway(**args)
        except Fault as e:
            return e

    def get_gateway_analog_port(self, **args):
        """
        :param name: Gateway port name [MGCP]
        :return: result dictionary
        """
        try:
            return self.client.getGatewayEndpointAnalogAccess(**args)
        except Fault as e:
            return e
    
    
    def get_gateway_sccp_port(self, **args):
        """
        :param name: Gateway port name [SCCP]
        :return: result dictionary
        """
        try:
            return self.client.getGatewaySccpEndpoints(**args)
        except Fault as e:
            return e

    def get_gateway_digital_access_bri(self, **args):
        """
        :param name: Gateway port name
        :return:
        """
        try:
            return self.client.getGatewayEndpointDigitalAccessBri(**args)

        except Fault as e:
            return e

    def get_gateway_digital_access_pri(self, **args):
        """
        :param name: Gateway port name
        :return:
        """
        try:
            return self.client.getGatewayEndpointDigitalAccessPri(**args)

        except Fault as e:
            return e

    def get_gateway_digital_access_t1(self, **args):
        """
        :param name: Gateway port name
        :return:
        """
        try:
            return self.client.getGatewayEndpointDigitalAccessT1(**args)

        except Fault as e:
            return e

    def add_gateway_analog_port(self, gatewayAnalogPortObject={}):
        """
        :param gatewayAnalogPortObject: Gateway Analog Ports JSON Object
        :return:
        """
        try:
            return self.client.addGatewayEndpointAnalogAccess(gatewayAnalogPortObject)
        except Fault as e:
            return e
    
    def add_gateway_digital_access_bri(self, gatewayDigitalAccessObject={}):
        """
        :param gatewayDigitalAccessObject: Gateway Digital Access JSON Object
        :return:
        """
        try:
            return self.client.addGatewayEndpointDigitalAccessBri(gatewayDigitalAccessObject)
        except Fault as e:
            return e

    def add_gateway_digital_access_pri(self, gatewayDigitalAccessObject={}):
        """
        :param gatewayDigitalAccessObject: Gateway Digital Access JSON Object
        :return:
        """
        try:
            return self.client.addGatewayEndpointDigitalAccessPri(gatewayDigitalAccessObject)
        except Fault as e:
            return e

    def add_gateway_digital_access_t1(self, gatewayDigitalAccessObject={}):
        """
        :param gatewayDigitalAccessObject: Gateway Digital Access JSON Object
        :return:
        """
        try:
            return self.client.addGatewayEndpointDigitalAccessT1(gatewayDigitalAccessObject)
        except Fault as e:
            return e
   

    def add_gateway_sccp_port(self, gatewaySccpPortObject={}):
        """
        :param gatewaySccpPortObject: Gateway Sccp Ports JSON Object
        :return:
        """
        try:
            return self.client.addGatewaySccpEndpoints(gatewaySccpPortObject)
        except Fault as e:
            return e
    

    def update_gateway_analog_port(self, **args):
        """
        :param gatewayAnalogPortObject: Gateway Analog Ports JSON Object
        :return:
        """
        try:
            return self.client.updateGatewayEndpointAnalogAccess(**args)
        except Fault as e:
            return e

    def update_gateway_sccp_port(self, sccpObj = {}):
        """
        :param gatewaySccpPortObject: Gateway Sccp Ports JSON Object
        :return:
        """
        try:

            return self.client.updateGatewaySccpEndpoints(name=sccpObj["name"],endpoint = sccpObj["endpoint"])['return']
        except Fault as e:
            return e

    def get_sip_route_patterns(self, tagfilter={"pattern": "", "routePartitionName": ""}):
        """
        Get sip_route_patterns
        :param mini: return a list of tuples of SIP Route pattern details
        :return: A list of dictionary's
        """
        try:
            return self.client.listSipRoutePattern(
                {"pattern": "%"}, returnedTags=tagfilter
            )["return"]["sipRoutePattern"]
        except Fault as e:
            return e

    def get_sip_route_pattern(self, **args):
        """
        Get sip route pattern details
        :param routePattern: SIP Route Pattern
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getSipRoutePattern(**args)
        except Fault as e:
            return e

    def add_sip_route_pattern(self, sipRoutePatternObject={}):
        """
        :param sipRoutePatternObject: SIP Route Pattern JSON Object
        :return:
        """
        try:
            return self.client.addSipRoutePattern(sipRoutePatternObject)
        except Fault as e:
            return e

# Universal Device Template
    def get_universal_device_template(self, **args):
        """
        Get universal device template details
        :param name: universal device template name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getUniversalDeviceTemplate(**args)
        except Fault as e:
            return e

    def add_universal_device_template(self, universalDeviceTemplateObject={}):
        """
        :param universalDeviceTemplateObject: Universal Device Template JSON Object
        :return:
        """
        try:
            return self.client.addUniversalDeviceTemplate(universalDeviceTemplateObject)
        except Fault as e:
            return e


# Universal Device Template

    def get_universal_line_template(self, **args):
        """
        Get universal device line details
        :param name: universal line template name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getUniversalLineTemplate(**args)
        except Fault as e:
            return e

    def add_universal_line_template(self, universalLineTemplateObject={}):
        """
        :param UniversalLineTemplate object: Universal Line Template JSON Object
        :return:
        """
        try:
            return self.client.addUniversalLineTemplate(universalLineTemplateObject)
        except Fault as e:
            return e

# User Profile
    def get_user_profile_provision(self, **args):
        """
        Get User Profile provison
        :param name: User Profile provison name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getUserProfileProvision(**args)
        except Fault as e:
            return e

    def add_user_profile_provision(self, userProfileProvisonObject={}):
        """
        :param userProfileProvisonObject object: User Profile provison JSON Object
        :return:
        """
        try:
            return self.client.addUserProfileProvision(userProfileProvisonObject)
        except Fault as e:
            return e

# Remote Destination and Profile

    def get_remote_destinations(self, searchCriteria = {"remoteDestinationProfileName": "%"}, tagfilter={"name": "", "destination":""}):
        """
        Get Remote Destination Profile Profile provison
        :param mini: return a list of tuples of Remote Destination Profile Profile provison details
        :return: A list of dictionary's
        """
        try:
            return self.client.listRemoteDestination(
                searchCriteria, returnedTags=tagfilter
            )["return"]["remoteDestination"]
        except Fault as e:
            return e
            
    def get_remote_destination(self, **args):
        """
        Get Remote Destination Profile Profile provison
        :param name: Remote Destination Profile provison name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getRemoteDestination(**args)
        except Fault as e:
            return e

    def add_remote_destination(self, rDPObject={}):
        """
        :param rDPObject object: Remote Destination JSON Object
        :return:
        """
        try:
            return self.client.addRemoteDestination(rDPObject)
        except Fault as e:
            return e


    def get_remote_destination_profile(self, **args):
        """
        Get Remote Destination Profile Profile provison
        :param name: Remote Destination Profile provison name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getRemoteDestinationProfile(**args)
        except Fault as e:
            return e

    def add_remote_destination_profile(self, rDPObject={}):
        """
        :param rDPObject object: Remote Destination JSON Object
        :return:
        """
        try:
            return self.client.addRemoteDestinationProfile(rDPObject)
        except Fault as e:
            return e
# Get Call Pickup Group

    def get_call_pickup_groups(
        self,
        tagfilter={
            "name": "",
            "pattern": ""
        },
    ):
        """
        Get Call Pickup Group
        :param mini: return a list of tuples of  Call Pickup Group details
        :return: A list of dictionary's
        """
        try:
            return self.client.listCallPickupGroup({"pattern": "%"}, returnedTags=tagfilter)[
                "return"
            ]["callPickupGroup"]
        except Fault as e:
            return e

    
    def get_call_pickup_group(self, **args):
        """
        Get  Call Pickup Group provison
        :param name:  Call Pickup Group name
        :param uuid: UUID name
        :return: result dictionary
        """
        try:
            return self.client.getCallPickupGroup(**args)
        except Fault as e:
            return e

    
    def add_call_pickup_group(self,args={}):
        """
        :param cpg object: Remote Destination JSON Object
        :return:
        """
        try:
            return self.client.addCallPickupGroup(args)
        except Fault as e:
            return e

    def get_service_parameters(self,tagfilter={
            "processNodeName": "",
            "name": "",
            "service": ""
        }):
        """
        Get Service Parameter
        :return: result dictionary
        """
        try:
            return self.client.listServiceParameter({"processNodeName": "%"}, returnedTags=tagfilter)[
                "return"
            ]["serviceParameter"]
        except Fault as e:
            return e
    
    def get_service_parameter(self, **args):
        """
        Get Service Parameter
        :param name:  service parm name service and processNodeName
        :return: result dictionary
        """
        try:
            return self.client.getServiceParameter(**args)
        except Fault as e:
            return e

    def check_cucm(self,tagfilter={
            "name": "",
        }):
        """
        Get Service Parameter
        :return: result dictionary
        """
        try:
            resp = self.client.listCallManager({"name": "%"}, returnedTags=tagfilter)[
                "return"
            ]["callManager"]
            return True
        except Fault as e:
            return False

    def list_app_user(self,tagfilter={
            "userid": ""
        }):
        """
        List Application Users
        :return: result dictionary
        """
        try:
            return self.client.listAppUser({"userid": "%"}, returnedTags=tagfilter)[
                "return"
            ]["appUser"]
        except Fault as e:
            return e
    
    def get_app_user(self, **args):
        """
        Get Application Users
        :param name:  app Userid
        :return: result dictionary
        """
        try:
            return self.client.getAppUser(**args)
        except Fault as e:
            return e

    def add_app_user(self,args={}):
        """
        :param appUser object: App User JSON Object
        :return:
        """
        try:
            return self.client.addAppUser(args)
        except Fault as e:
            return e

    
    def update_app_user(self, **args):
        """
        :param appUserObj: appUser JSON Object
        :return:
        """
        try:
            return self.client.updateAppUser(**args)
        except Fault as e:
            return e

    def list_advertised_pattern(self,searchCriteria = {"pattern": "%"}, tagfilter={
            "pattern": ""
        }):
        """
        List Advertised Patterns
        :return: result dictionary
        """
        try:
            return self.client.listAdvertisedPatterns(searchCriteria, returnedTags=tagfilter)[
                "return"
            ]["advertisedPatterns"]
        except Exception as e:
            return e

    def get_advertised_pattern(self, **args):
        """
        Get Advertised Patterns
        :param name:  pattern
        :return: result dictionary
        """
        try:
            return self.client.getAdvertisedPatterns(**args)
        except Fault as e:
            return e

    def add_advertised_pattern(self,args={}):
        """
        :param pattern object: pattern JSON Object
        :return:
        """
        try:
            return self.client.addAdvertisedPatterns(args)
        except Fault as e:
            return e

    
    def update_advertised_pattern(self, **args):
        """
        :param pattern: pattern JSON Object
        :return:
        """
        try:
            return self.client.updateAdvertisedPatterns(**args)
        except Fault as e:
            return e
