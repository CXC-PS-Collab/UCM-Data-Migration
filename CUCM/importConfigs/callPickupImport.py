# -*- coding: utf-8 -*-
"""
Created on Tue Nov 23 17:56:13 2021

@author: ashimis3
"""

# -*- coding: utf-8 -*-
#Getting all the users and its dependencies - userprofiles, universaldevicetemplate, universallinetemplate
#Before import make sure you have the desired partition
import sys
sys.path.append("../")
import os
from ciscoaxl import axl
import json
from zeep.helpers import serialize_object
from collections import OrderedDict
from zeep.exceptions import Fault
from adapter.appcore import *

import time


ExceptionList = []
catchExceptionWords = ["exception", "error", "failed", "axl", "fault", "zeep",  "Item not valid"]

Sites = ucmDestinationContent["configsFolders"]

callpickupgroups = json.load(open(f"../ConfigExports/{Sites[0]}/callpickupgroup.json"))

callpickupgroups = tqdm(callpickupgroups)
for loc in callpickupgroups:
    PAUSE = True
    while PAUSE:
        callpickupgroups.set_description(f"Processing {loc['name']}")
        try:
            #On Addition always the first member added is itself.
            #Do not specify the first member as itself in an Add request .
            #Also make sure that the priority always starts with
            #1. It will internally be taken care of during Addition and Updation.

            if "members" in loc and loc["members"] != None:
                if loc["members"]["member"]:
                    for member in loc["members"]["member"].copy():
                        if member["pickupGroupName"] == loc["name"]:
                            loc["members"]["member"].remove(member)

            #Removing Key- usage
            if "usage" in loc:
                del loc["usage"]
            resp = ucm_destination.add_call_pickup_group(loc)
            if type(resp) == Fault:
                print("\nError in adding callPickup Group: "+loc["name"]+" : "+str(resp))
                callpickupgroups.set_description(f"Processing {loc['name']} : Major Issue : {resp}")

                In = input("\n Error Occured, Want to retry? (y/n): ")
                if In == "n" or In == "n":
                    PAUSE = False
            else:
                PAUSE = False
                callpickupgroups.set_description(f"Processing {loc['name']} : Added")
        except Exception as e:
            print("\nError while adding callPickup Group: "+ str(loc["name"]) + " : " + str(e))
            In = input("\n Error Occured, Want to retry? (y/n): ")
            if In == "n" or In == "n":
                PAUSE = False

