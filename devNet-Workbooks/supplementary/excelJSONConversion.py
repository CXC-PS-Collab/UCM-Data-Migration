import traceback
import pandas as pd
import json
import os
import glob
import xlsxwriter
from pandas.io.json import json_normalize
from flatten_json import unflatten_list,unflatten
from zeep.helpers import serialize_object
from collections import OrderedDict
from flatten_json import flatten
import sys
import shutil

sys.path.append("../")
from adapter.appcore import *

from ciscoaxl import axl

#Reference- https://xlsxwriter.readthedocs.io/working_with_pandas.html

siteCode = ucmSourceContent["siteCode"]
EXCEL_FILENAME = siteCode+'-ConfigExportsExcel.xlsx'

# Ref = '..\ConfigExports\\'+EXCEL_FILENAME
SrcDir = '..\ConfigExports\\'+siteCode
Src = SrcDir + '\\'+EXCEL_FILENAME
Dest = "..\ConfigExports\\Output"

#delete SiteCode and add the key,value pairs which were deleted during phone cleanup and cleandata
def cleanObjectJson(data,eachjsonentry_dfobj):
    returnedData = data
    if 'SiteCode' in returnedData:
        del returnedData['SiteCode']
    for key,value in eachjsonentry_dfobj.items():
        if key!="result":
            datavalue=getarraykey(key,value)
            keyvalues=key.split('_',1)
            returnedData[keyvalues[0]]=datavalue[keyvalues[0]]

    return returnedData


#Add SiteCode and Remove uuid for j2e
def cleanObjectJ2E(data,SiteCode):
    dictData = dict(serialize_object(data))
    returnedDict = {"SiteCode":SiteCode}
    for key,value in dictData.items():
        if not "uuid" in key:
            returnedDict[key]=value

    return returnedDict

# delete ['speeddials','lines','blfDirectedCallParks','vendorConfig'] from list for selected sitecode
def phonecleanUp(data):

    CompleteData={}
    Result=data
    removalList=['speeddials','lines','blfDirectedCallParks','vendorConfig']

    for eachentry in removalList:
        if eachentry in data:
            CompleteData[eachentry]=None
            del Result[eachentry]


    CompleteData["result"]=Result
    return CompleteData

#create key/value pair which has flattened key
def getarraykey(key,value):

    keysplit=key.split('_',1)
    if len(keysplit)==1:
        return {keysplit[0]:value}
    else:
        return {keysplit[0]:getarraykey(keysplit[1],value)}


#clean data and add to list which ends with _0
def CleanData(Data):

    #print(Data)
    result = {}
    CompleteData={}

    tempList=[]
    tempKeyname=""
    for key,value in Data.items():
        keyname=key.rsplit('_',1)
        if not value == None:
            if len(keyname)>1 and keyname[1].isdigit() and (tempKeyname==keyname[0] or tempKeyname==""):
                if int(keyname[1])==0:
                    tempKeyname=keyname[0]
                    tempList=[]
                #Added int by @ashimis3
                if value!=None and type(value) != int and value.isdecimal():
                    tempList.append(int(value))
                else:
                    tempList.append(value)
            else:
                if tempKeyname!="":
                    CompleteData[tempKeyname]=tempList
                    result[tempKeyname]=tempKeyname
                    tempKeyname=""
                    tempList=[]
                    if len(keyname)>1 and keyname[1].isdigit():
                        tempKeyname=keyname[0]
                        if value!=None and (not isinstance(value, int)) and isinstance(value, float):
                            tempList.append(int(value))
                        else:
                            tempList.append(value)
                    else:
                        if value!=None and (not isinstance(value, int)) and isinstance(value, float):
                            result[key]=int(value)
                        else:
                            result[key]=value
                else:
                    if value!=None and (not isinstance(value, int)) and isinstance(value, float):
                        result[key]=int(value)
                    else:
                        result[key]=value

    CompleteData["result"]=result

    return CompleteData

#Replace value "NotAvailable" with None
def replaceNoValueNone(data):
    Result={}

    for key,value in data.items():

        if isinstance(value,dict):
            Result[key]={}
            for eachkey,eachvalue in value.items():
                if isinstance(eachvalue,list):
                    listvalue=[]
                    for eachlistvalue in eachvalue:
                        if eachlistvalue=='NotAvailable':
                            listvalue.append(None)
                        else:
                            listvalue.append(eachlistvalue)
                    Result[key][eachkey]=listvalue
                else:
                    if eachvalue=='NotAvailable':
                        Result[key][eachkey]=None
                    else:
                        Result[key][eachkey]=eachvalue
        elif isinstance(value,list):
            Result[key]=[]
            for eachlistvalue in value:
                if eachlistvalue=='NotAvailable':
                    Result[key].append(None)
                else:
                    Result[key].append(eachlistvalue)
    return Result

def ConvertToJSON(EXCEL_FILENAME):

    #Copying Xlsx file
    # shutil.copy(Ref, SrcDir)
    # workbook = xlsxwriter.Workbook(Src)
    # workbook.close()
    print("Start Excel to Json Conversion")
    Src = '..\ConfigExports\\' + EXCEL_FILENAME
    loc = os.path.abspath(Src)
    xl = pd.ExcelFile(loc)
    sheets=xl.sheet_names

    if not os.path.exists(os.path.abspath(Dest)):
        os.makedirs(os.path.abspath(Dest))
    #sheetsEmpty=[]
    print("Get each sheet to convert")
    for eachsheet in sheets:

        SiteCodes={}
        CurrentSiteCode=""
        if not eachsheet=='Sheet':
            print(eachsheet)
            excel_data_df = pd.read_excel(loc, sheet_name=eachsheet)
            jsondata = excel_data_df.to_json(orient = 'records')
            jsonsetdf=json.loads(jsondata)
            cleanedData=[]
            for eachjsonentry_df in jsonsetdf:
                eachjsonentry_dfobj=CleanData(eachjsonentry_df)
                eachjsonentry_dfobj= replaceNoValueNone(eachjsonentry_dfobj)
                if eachsheet=="phone":
                    eachjsonentry_dfobj=phonecleanUp(eachjsonentry_dfobj["result"])
                unflattenjson=unflatten_list(eachjsonentry_dfobj["result"])
                if not unflattenjson["SiteCode"] in SiteCodes.keys():
                    SiteCodes[unflattenjson["SiteCode"]]=[]
                    CurrentSiteCode=unflattenjson["SiteCode"]
                CleanUnflattenJson=cleanObjectJson(unflattenjson,eachjsonentry_dfobj)
                SiteCodes[CurrentSiteCode].append(CleanUnflattenJson)
            #Create folders with SiteCode and json files in each folder
            if len(SiteCodes)>0:
                for eachSiteCode in SiteCodes:
                    jsonContent = SiteCodes[eachSiteCode]
                    if not os.path.exists(os.path.abspath("..\ConfigExports\\Output\\"+eachSiteCode)):
                        os.makedirs(os.path.abspath("..\ConfigExports\\Output\\"+eachSiteCode))
                    
                    with open(os.path.abspath("..\ConfigExports\\Output\\"+eachSiteCode+"\\"+eachsheet+".json"), "w") as jsonFile:
                        json.dump(jsonContent, jsonFile, indent = 2)
            """else:
                sheetsEmpty.append(eachsheet)"""


    """ print("Create empty json files")
    folderPath='.\\ConfigExports\\Output\\'

    SiteCodesFolders=glob.glob(folderPath+'*\\')
    for eachSiteCodesFolder in SiteCodesFolders:
        for eachemptysheet in sheetsEmpty:
            jsonFile = open(os.path.abspath(eachSiteCodesFolder+eachemptysheet+".json"), "w")
            jsonFile.close() """

    print("End EXCEL to JSON Conversion")

def ConvertToExcel(siteCode = []):

    #Copying Xlsx file
    # shutil.copy(Ref, SrcDir)
    workbook = xlsxwriter.Workbook(Src)
    workbook.close()
    print("Start JSON to EXCEL Conversion")
    folderPath='..\ConfigExports\\'
    if siteCode == []:
        SiteCodesFolders=glob.glob(folderPath+'*\\')   #get all folders inside ConfigExports
        SiteCodes=[]

        for eachSiteCodesFolders in SiteCodesFolders:    #Get just folder names which will be used as SiteCode
            SiteCodes.append(eachSiteCodesFolders.rsplit('\\', 2)[1].rsplit('\\',1)[0])

    else:
        SiteCodes = siteCode


    # - Generate Excel Sheet from All JSON Outputs for a particular site

    # In[5]:
    # wb = openpyxl.Workbook()
    dest_filename = os.path.join(os.path.abspath(SrcDir), EXCEL_FILENAME)  #Create a single excel file
    workbook = xlsxwriter.Workbook(dest_filename)
    workbook.close()   
    # wb.save(dest_filename)
    # wb.close()
    print(dest_filename)

    # writer = pd.ExcelWriter(dest_filename, engine='openpyxl')
    cleanedContent={}
    sheets=[]
    print("Get Data for Each SiteCode")
    print(SiteCodes)
    for eachSiteCode in SiteCodes:
        # print(eachSiteCode)
        jsonFiles=glob.glob(folderPath+eachSiteCode+'\\*.json')
        # print(jsonFiles)
        for jfile in jsonFiles:
            try:
                filepath= os.path.abspath(jfile)
                filename = filepath.split('.')[0]
                sheetname=filename.rsplit('\\', 1)
                if not sheetname[1] in sheets:
                    sheets.append(sheetname[1])
                jsonFileContent = json.load(open(filepath))
                jsonString=json.dumps(jsonFileContent).replace('"null"','null')
                jsonString=jsonString.replace('null','"NotAvailable"')
                jsonFileContent=json.loads(jsonString)
                if jsonFileContent:
                    if not sheetname[1] in cleanedContent.keys():
                        cleanedContent[sheetname[1]]=[flatten(cleanObjectJ2E(data,eachSiteCode)) for data in jsonFileContent]
                    else:
                        cleanData=[flatten(cleanObjectJ2E(data,eachSiteCode)) for data in jsonFileContent]
                        cleanedContent[sheetname[1]]=cleanedContent[sheetname[1]]+cleanData
                else:
                    if not sheetname[1] in cleanedContent.keys():
                        cleanedContent[sheetname[1]]=[]
            except:
                print("Error for",jfile)
                traceback.print_exc()
                continue

    contentkeys=cleanedContent.keys()
    
    if os.path.exists(dest_filename):
        # try:
        writer = pd.ExcelWriter(dest_filename, engine='xlsxwriter')
        # except:
        #     writer = pd.ExcelWriter(dest_filename, engine='openpyxl')
        #     book = openpyxl.load_workbook(dest_filename)
        #     writer.book = book
    print("Create sheet in excel for each JSON")
    for sheetname in sheets:
        print(sheetname)
        df = pd.DataFrame(cleanedContent[sheetname])
        df.to_excel(writer, sheet_name=sheetname, index=False)
    writer.save()

    print("End JSON to EXCEL Conversion")


def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

#Uncomment Any one to execute
# ConvertToExcel([siteCode])
ConvertToJSON(EXCEL_FILENAME)