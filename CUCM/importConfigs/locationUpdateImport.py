# -*- coding: utf-8 -*-
"""
Created on Tue Nov 23 17:56:13 2021

@author: ashimis3
"""

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

locations = json.load(open(f"../ConfigExports/{Sites[0]}/location.json"))

locations = tqdm(locations)
for loc in locations:
    if "id" in loc:
        del loc["id"]
    PAUSE = True
    while PAUSE:
        locations.set_description(f"Processing {loc['name']}")
        try:
            resp = ucm_destination.update_location(**loc)
            if type(resp) == Fault:
                print("Error in updating Location: "+loc["name"]+" : "+str(resp))
                locations.set_description(f"Processing {loc['name']} : Major Issue : {resp}")

                In = input("\n Error Occured, Want to retry? (y/n): ")
                if In == "n" or In == "n":
                    PAUSE = False
            else:
                PAUSE = False
                locations.set_description(f"Processing {loc['name']} : Added")
        except Exception as e:
            print("Error while updating location: "+ str(loc) + " : " + str(e))
            In = input("\n Error Occured, Want to retry? (y/n): ")
            if In == "n" or In == "n":
                PAUSE = False

