# -*- coding: utf-8 -*-
"""
Created on Wed Oct  6 18:12:58 2021

@author: ashimis3
"""

import sys
sys.path.append("../")
import os
import json
from adapter.appcore import *


siteCode = ucmSourceContent["siteCode"]

phones = json.load(open(f"../ConfigExports/{siteCode}/phone.json"))

dirn = []
for phone in phones:
    if "lines" in phone and phone["lines"] != None:
        if "line" in phone["lines"]:
            for line in phone["lines"]["line"]:
                if line["dirn"] not in dirn:
                    dirn.append(line["dirn"])


directory = f"../ConfigExports/{siteCode}"
if not os.path.exists(directory):
    os.makedirs(directory)
write_results(directory, dirn, "dirn-update")
