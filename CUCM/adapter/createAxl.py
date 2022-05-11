axlMethodList = ["AarGroup",
"AdvertisedPatterns",
"Announcement",
"ApplicationDialRules",
"ApplicationServer",
"ApplicationToSoftkeyTemplate",
"ApplicationUserCapfProfile",
"AppServerInfo",
"AppUser",
"AudioCodecPreferenceList",
"BillingServer",
"BlockedLearnedPatterns",
"CalledPartyTracing",
"CalledPartyTransformationPattern",
"CallerFilterList",
"CallingPartyTransformationPattern",
"CallManagerGroup",
"CallPark",
"CallPickupGroup",
"CCAProfiles",
"CcdAdvertisingService",
"CcdHostedDN",
"CcdHostedDNGroup",
"CcdRequestingService",
"CiscoCatalyst600024PortFXSGateway",
"CiscoCatalyst6000E1VoIPGateway",
"CiscoCatalyst6000T1VoIPGatewayPri",
"CiscoCatalyst6000T1VoIPGatewayT1",
"CmcInfo",
"CommonDeviceConfig",
"CommonPhoneConfig",
"ConferenceBridge",
"ConferenceNow",
"CredentialPolicy",
"Css",
"CtiRoutePoint",
"CumaServerSecurityProfile",
"Customer",
"CustomUserField",
"DateTimeGroup",
"DefaultDeviceProfile",
"DeviceMobility",
"DeviceMobilityGroup",
"DevicePool",
"DeviceProfile",
"DhcpServer",
"DhcpSubnet",
"DirectedCallPark",
"DirectoryLookupDialRules",
"DirNumberAliasLookupandSync",
"ElinGroup",
"EndUserCapfProfile",
"EnterpriseFeatureAccessConfiguration",
"ExpresswayCConfiguration",
"ExternalCallControlProfile",
"FacInfo",
"FallbackProfile",
"FeatureControlPolicy",
"FeatureGroupTemplate",
"Gatekeeper",
"Gateway",
"GatewayEndpointAnalogAccess",
"GatewayEndpointDigitalAccessBri",
"GatewayEndpointDigitalAccessPri",
"GatewayEndpointDigitalAccessT1",
"GatewaySccpEndpoints",
"GatewaySubunits",
"GeoLocation",
"GeoLocationFilter",
"GeoLocationPolicy",
"H323Gateway",
"H323Phone",
"H323Trunk",
"HandoffConfiguration",
"HttpProfile",
"HuntList",
"HuntPilot",
"ImeClient",
"ImeE164Transformation",
"ImeEnrolledPattern",
"ImeEnrolledPatternGroup",
"ImeExclusionNumber",
"ImeExclusionNumberGroup",
"ImeFirewall",
"ImeRouteFilterElement",
"ImeRouteFilterGroup",
"ImeServer",
"ImportedDirectoryUriCatalogs",
"InfrastructureDevice",
"IpPhoneServices",
"IvrUserLocale",
"LbmGroup",
"LbmHubGroup",
"LdapDirectory",
"LdapFilter",
"LdapSyncCustomField",
"Line",
"LineGroup",
"LocalRouteGroup",
"Location",
"MediaResourceGroup",
"MediaResourceList",
"MeetMe",
"MessageWaiting",
"MlppDomain",
"MobileVoiceAccess",
"Mobility",
"MobilityProfile",
"MraServiceDomain",
"Mtp",
"NetworkAccessProfile",
"Phone",
"PhoneActivationCode",
"PhoneButtonTemplate",
"PhoneNtp",
"PhoneSecurityProfile",
"PhysicalLocation",
"PresenceGroup",
"PresenceRedundancyGroup",
"ProcessNode",
"RecordingProfile",
"Region",
"RemoteCluster",
"RemoteDestination",
"RemoteDestinationProfile",
"ResourcePriorityNamespace",
"ResourcePriorityNamespaceList",
"RouteFilter",
"RouteGroup",
"RouteList",
"RoutePartition",
"RoutePattern",
"SafCcdPurgeBlockLearnedRoutes",
"SafForwarder",
"SafSecurityProfile",
"SdpTransparencyProfile",
"ServiceProfile",
"SipDialRules",
"SIPNormalizationScript",
"SipProfile",
"SipRealm",
"SipRoutePattern",
"SipTrunk",
"SipTrunkSecurityProfile",
"SNMPCommunityString",
"SNMPUser",
"SoftKeyTemplate",
"Srst",
"TimePeriod",
"TimeSchedule",
"TodAccess",
"Transcoder",
"TransformationProfile",
"TransPattern",
"UcService",
"UnitsToGateway",
"UniversalDeviceTemplate",
"UniversalLineTemplate",
"User",
"UserGroup",
"UserPhoneAssociation",
"UserProfileProvision",
"Vg224",
"VohServer",
"VoiceMailPilot",
"VoiceMailPort",
"VoiceMailProfile",
"VpnGateway",
"VpnGroup",
"VpnProfile",
"WifiHotspot",
"WirelessAccessPointControllers",
"WLANProfile",
"WlanProfileGroup",
]

from appcore import *
import xmlschema
import json

schema = xmlschema.XMLSchema('../ciscoaxl/schema/12.5/AXLsoap.xsd')

def getType(element):
    Type = "Failed"
    try:
        if element.type == None:
            Type = "empty"
        elif element.type.name != None:
            Type = element.type.name.split('}')[-1]
        elif element.type.content != None and element.type.content.name != None:
            Type = element.type.content.name.split('}')[-1]
        elif element.type.is_element_only():
            Type = "element-only"
    except Exception as e:
        print(f"Failed to get type for {element} : {str(e)}")
    return Type

def getAllElements(element, myDataStructure):
    for e in element.type.content.iter_elements():
        Type = getType(e)

        myDataStructure[e.name] = [e.occurs, Type]
        if e.type != None and e.type.has_complex_content():
            myDataStructure[e.name].append(getAllElements(e, {}))
        else:
            pass
    return myDataStructure

def driver(command, axlMethodList):
    axlDS = []
    axlMethods = tqdm(axlMethodList)
    for methodName in axlMethods:
        try:
            method = schema.elements[command+methodName]
            axlDS.append({command+methodName:getAllElements(method, {})})
        except Exception as e:
            print("Failed-",methodName,str(e))
    return axlDS

command = "add"#["add","get"]#,"update","delete"]
# for command in commands:
axlDs = driver(command, axlMethodList)
with open("AXL_"+command+".json", 'w') as jsonObj:
    json.dump(axlDs, jsonObj, indent=2)
    print("Saved", command,"Axl Json.")
