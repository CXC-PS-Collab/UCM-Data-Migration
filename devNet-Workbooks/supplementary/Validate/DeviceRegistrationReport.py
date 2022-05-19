from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from zeep.exceptions import Fault
import requests
from requests import Session
from requests.auth import HTTPBasicAuth
from lxml import etree
import urllib3,getpass,gc,os,time,datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re, math
import pandas as pd
from pandas import DataFrame as df
from xlsxwriter import *
import xlrd
import os
# import Firmwareanalysis
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
from tqdm import tqdm
import traceback

VERSION = "12.5"
BaseDir = "schema/"
class Service:
    def __init__(self):
        self.status="N/A"
    def setstatus(self,status,sttime,utime):
        self.status=status
        self.starttime=sttime
        self.uptime=utime
    def getstatus(self):
        return [self.status,self.starttime,self.uptime]
    def getsttime(self):
        return self.starttime
    def getutime(self):
        return self.uptime

class UCNode:
    def __init__(self,name):
        self.name=name
        self.servicelist={}
    def setservices(self,servicenamelist):
        for service in servicenamelist:
            self.servicelist[service]=Service()
    def setserviceStatus(self,servicename,statusname,starttime,uptime):
        self.servicelist[servicename].setstatus(statusname,starttime,uptime)
    def getoneService(self,servicename):
        return self.servicelist[servicename].getstatus()
    def getAllServices(self):
        responseServiceDict={}
        for key,value in self.servicelist.items():
            responseServiceDict[key]=value.getstatus()
        return responseServiceDict
class Device:
    def __init__(self,name):
        self.name=name
        self.setattr(model="N/A",node="N/A",protocol="N/A",status="None",desc="N/A",Aload="N/A",Inload="N/A",DeviceClass="N/A",DirectoryNumber="N/A",LoginUserId="N/A",TimeStamp="N/A",Devicepool="N/A",IPAddress="N/A",proximity="N/A")
    def setattr(self,**kwargs):
        for k,v in kwargs.items():
            self.__dict__[k]=v
    def getRisStatus(self):
        return str(self.status)
    def getattr(self):
        return ([self.DeviceClass,self.Devicepool,self.name,self.model,self.status,self.desc,self.IPAddress,self.node,self.Aload,self.Inload,self.LoginUserId,self.TimeStamp,self.DirectoryNumber])

class CustomTransport(Transport):
    def load(self, url):
        # Custom URL overriding to local file storage
        if url and url == "http://schemas.xmlsoap.org/soap/encoding/":
            url = BaseDir+"ServSoapSchema.xsd"

        # Call zeep.transports.Transport's load()
        return super(CustomTransport, self).load(url)

# cluster
class Server:
    ## WSDL initialisations and Make Session
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    def __init__(self, ipaddress, username, auth, workbook, title, option):
        self.ipaddress = ipaddress
        self.username = username
        self.auth = auth
        self.workbook = workbook
        self.title = title
        self.riswsdl = 'https://' + self.ipaddress + ':8443/realtimeservice2/services/RISService70?wsdl'
        self.version = VERSION
        self.axlwsdl = BaseDir+'/'+self.version+'//AXLAPI.wsdl'
        self.servicewsdl = BaseDir+'/'+self.version+'//ServiceWSDL.wsdl'
        # self.servicewsdl = 'file://' + os.getcwd() + '//Files//ServiceWSDL.wsdl'
        self.AXL_BINDING_NAME = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"
        self.ADDRESS = "https://" + self.ipaddress + ":8443/axl/"
        self.SERVICE_BINDING_NAME = "{http://cisco.com/ccm/serviceability/soap/ControlCenterServices/}ControlCenterServicesBinding"
        # logging.debug('All Inputs Correctly Initialised\n')
        self.session = Session()
        self.session.verify = False
        self.session.auth = HTTPBasicAuth(self.username, self.auth)
        self.transport = CustomTransport(cache=SqliteCache(), session=self.session, timeout=60)
        self.history = HistoryPlugin()
        self.axldict = {}
        self.uclist = {}
        self.option = option

    def getRiswsdl(self):
        #Getting riswsdl for 12.5 and replacing localhost with IP
        headers = {
            'Content-Type': 'text/plain',
        }
        try:
            response = requests.request("GET", self.riswsdl, headers=headers, auth=self.session.auth, verify=self.session.verify)
            with open("RISService70.wsdl", 'w') as f:
                print(response.text, file=f)
            self.riswsdl = 'RISService70.wsdl'
            
            # Read in the file
            with open(self.riswsdl, "r") as file:
                filedata = file.read()

            # Replace the target string
            filedata = filedata.replace("localhost", self.ipaddress)

            # Write the file out again
            with open(self.riswsdl, "w") as file:
                file.write(filedata)
        except Exception as e:
            print("Error in getting riswsdl file: "+str(e))
            exit()


    def fetchnodes(self):
        try:
            # print(self.axlwsdl)
            client = Client(wsdl=self.axlwsdl, transport=self.transport, plugins=[self.history])
            axl = client.create_service(self.AXL_BINDING_NAME, self.ADDRESS)

            sql = "select name from processnode where systemnode=='f' and isactive=='t'"
            QueryResult = axl.executeSQLQuery(sql=sql)
            for dev in QueryResult['return']['row']:
                self.uclist[dev[0].text] = UCNode(dev[0].text)
            return "FetchOk"
        except (Fault, Exception) as error:
            print("Error Fetching Nodes!! Please Check Credentials ")
            print(error)
            return "FetchNotOk"
            # for hist in [history.last_sent, history.last_received]:
            #   print(etree.tostring(hist["envelope"], encoding="unicode", pretty_print=True))

    def inputfunction(self):
        userinput = 7
        try:
            while int(userinput) >= 7:
                userinput = input('1. All Services Status \n2. Phone Registration \n3. (Gateways/Media Resources/Sip Trunk) Registration \n4. All Devices Registration \n5. Phone Firmware Analysis\n 6. Exit\n Select  option (1-6) : ')
        except ValueError:
            print("Please Enter option (1-6). Exiting Now...")
            exit()
        return int(userinput)

    def main(self, selection):
        if (selection == 1):
            try:
                print("Fetching Services Status")
                self.getservices()
            except:
                print("Error while fetching Services Status")
                # logging.debug("Error while fetching Services Status")
        elif (selection == 5):
            self.phone_firmware_analysis()
        elif (1 < selection < 5):
            try:
                print("Executing AXL")
                self.AXLSQLMaker(int(selection))
            except:
                print("Error while Executing AXL")

        recur = input("Type \"yes\" to Continue, Return to Exit : ")
        return recur

    def getservices(self):
        for ip in self.uclist.keys():
            print("Connecting to " + ip)
            try:
                client = Client(wsdl=self.servicewsdl, transport=self.transport, plugins=[self.history])
                SERVICE_ADDR = "https://" + ip + ":8443/controlcenterservice/services/ControlCenterServicesPort"
                Servicexl = client.create_service(self.SERVICE_BINDING_NAME, self.SERVICE_ADDR)
                result = Servicexl.soapGetServiceStatus([''])
                self.uclist[ip].setservices([Service['ServiceName'] for Service in result['ServiceInfoList']])
                for Service in result['ServiceInfoList']:
                    if Service['ReasonCode'] == -1:
                        self.uclist[ip].setserviceStatus(Service['ServiceName'],
                                                    ('Activated || ' + Service['ServiceStatus']), Service['StartTime'],
                                                    str(datetime.timedelta(seconds=int(Service['UpTime']))))
                    else:
                        self.uclist[ip].setserviceStatus(Service['ServiceName'],
                                                    (Service['ReasonCodeString'] + ' || ' + Service['ServiceStatus']),
                                                    "N/A", "N/A")
            except (Fault, Exception) as error:
                print("Cannot Get Services From " + ip + "\n")
                print(error)

        print("Generating Excel")
        self.GenerateServiceExcel()
        # for hist in [history.last_sent, history.last_received]:
        #   print(etree.tostring(hist["envelope"], encoding="unicode", pretty_print=True))

    def GenerateServiceExcel(self):
        Riswb = self.workbook
        ws = Riswb.active
        ws.title = "Services Status Report"
        ws.append(['NodeName', 'Service Name', 'Status', 'StartTime', 'UpTime'])
        for ip in self.uclist.keys():
            outputdict = self.uclist[ip].getAllServices()
            for k, v in outputdict.items():
                v.insert(0, ip)
                v.insert(1, k)
                ws.append(v)
        timestr = time.strftime("%Y%m%d-%H%M%S")
        Riswb.save('ServiceStatusreport_' + self.ipaddress + '_' + timestr + '.xlsx')
        del Riswb

    def phone_firmware_analysis(self):
        rispath = self.AXLSQLMaker(4)
        if rispath != '':
            analysis = self.perform_analysis(os.getcwd() + '/' + rispath)
            self.write_analyis_to_excel(analysis)


    def perform_analysis(self, filepath):
        print("Analysing Firmwares based on the Registration Report Generated!")
        df1 = pd.read_excel(filepath, sheet_name=self.title)
        model_types = df1['model'].unique()
        # print(model_types)
        analysis = dict()
        for model_type in model_types:
            model_analysis = dict()
            provisioned_df = df1.loc[df1['model'] == model_type]
            model_analysis['provisioned_devices'] = provisioned_df.shape[0]
            # print(model_type,':' ,provisioned_devices)
            registered_df = provisioned_df.loc[provisioned_df['status'] == 'Registered']
            model_analysis['registered_devices'] = registered_df.shape[0]
            firmware_types = registered_df['Active_load'].unique()
            firmware_analysis = dict()
            for firmware_type in firmware_types:
                firmware_df = registered_df.loc[registered_df['Active_load'] == firmware_type]
                firmware_analysis[firmware_type] = firmware_df.shape[0]
            model_analysis['firmware_analysis'] = firmware_analysis
            analysis[model_type] = model_analysis
        # print(analysis)
        return analysis

    def write_analyis_to_excel(self, analysis):
        print("Writing Analysis to the Excel!")
        wb = load_workbook(os.getcwd() + '\Files\Firmware analysis.xlsx')
        ws = wb.get_sheet_by_name(r'Phone FW Analysis')
        written_dict = dict(analysis)
        for i in range(1, ws.max_row):
            if ws.cell(row=i, column=1).value in analysis:
                phone_model_dict = analysis[ws.cell(row=i, column=1).value]
                written_dict[ws.cell(row=i, column=1).value] = 'Done'
                firmware_str = ''
                count_str = ''
                firmware_analysis_dict = phone_model_dict['firmware_analysis']
                if firmware_analysis_dict != {}:
                    for key, value in firmware_analysis_dict.items():
                        firmware_str = firmware_str + str(key) + '\n'
                        count_str = count_str + str(value) + '\n'
                for j in range(3, 7):
                    # print (j,ws.cell(row=i, column=j).value)
                    if j == 3:
                        ws.cell(row=i, column=j).value = phone_model_dict['provisioned_devices']
                    elif j == 4:
                        ws.cell(row=i, column=j).value = phone_model_dict['registered_devices']
                    elif j == 5:
                        ws.cell(row=i, column=j).value = count_str
                    elif j == 6:
                        ws.cell(row=i, column=j).value = firmware_str
        remaining_analysis = {k: v for k, v in written_dict.items() if v != 'Done'}
        # print(remaining_analysis)
        counter = 1
        for k, v in remaining_analysis.items():
            ws.cell(row=counter + 68, column=1).value = k
            firmware_analysis_dict = v['firmware_analysis']
            firmware_str = ''
            count_str = ''
            if firmware_analysis_dict != {}:
                for key, value in firmware_analysis_dict.items():
                    firmware_str = firmware_str + str(key) + '\n'
                    count_str = count_str + str(value) + '\n'
            ws.cell(row=counter + 68, column=3).value = v['provisioned_devices']
            ws.cell(row=counter + 68, column=4).value = v['registered_devices']
            ws.cell(row=counter + 68, column=5).value = count_str
            ws.cell(row=counter + 68, column=6).value = firmware_str
            counter = counter + 1

        timestr = time.strftime("%Y%m%d-%H%M%S")
        wb.save('firmware_analysis' + ipaddress + '_' + timestr + '.xlsx')

    def chunks(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def GenerateRisExcel(self):
        if not os.path.exists(os.getcwd()+'//temp'):
            os.makedirs(os.getcwd()+'//temp')
        finalDevices = [vars(value) for key, value in self.axldict.items()]
        timestr = time.strftime("%Y%m%d-%H%M%S")
        rispath=""
        print("Self Option : "+str(type(self.option)))
        if int(self.option)==1:
            self.name='risreport_' + self.ipaddress + '_' + timestr + '.xlsx'
            writer = pd.ExcelWriter(self.name, engine='xlsxwriter')
            finalDevicesdf = df.from_dict(finalDevices)
            finalDevicesdf.to_excel(writer, sheet_name=self.title, index=False)
            rispath = self.name
            writer.save()
            del finalDevicesdf,finalDevices
        elif int(self.option)==2:
            print('Generate Ris option 2')
            self.name=os.getcwd()+'//temp//risreport_temp_' + self.title + '.xlsx'
            writer = pd.ExcelWriter(self.name, engine='xlsxwriter')
            finalDevicesdf = df.from_dict(finalDevices)
            finalDevicesdf.to_excel(writer, sheet_name=self.title, index=False)
            rispath = self.name
            writer.save()
            del finalDevicesdf,finalDevices
        return rispath




    def AXLSQLMaker(self, option):
        basesql = " d.name as DeviceName, tm.name as Model, CASE WHEN tm.name LIKE '%Webex%' THEN 'Video Endpoint' WHEN tm.name LIKE 'Cisco Unified Client Services Framework' THEN 'Jabber' WHEN tm.name LIKE '% TelePresence%' THEN 'Video Endpoint' WHEN tm.name LIKE '%Spark%' THEN 'Video Endpoint' else tc.name end as deviceclass,dp.name as Devicepool,d.description as description, SUBSTR( dx4.xml, CHARINDEX('<ProximityMode>', dx4.xml) + Len('<ProximityMode>'), CHARINDEX('</ProximityMode>', dx4.xml) - CHARINDEX('<ProximityMode>', dx4.xml) - Len('</ProximityMode>') + 1 ) as proximity from device d left join devicepool as dp on d.fkdevicepool=dp.pkid LEFT JOIN devicexml4k dx4 on d.pkid=dx4.fkdevice LEFT JOIN devicexml8k dx8 on d.pkid=dx8.fkdevice LEFT JOIN devicexml16k dx16 on d.pkid=dx16.fkdevice LEFT JOIN typemodel tm on tm.enum=d.tkmodel LEFT JOIN typeclass tc on tc.enum=d.tkclass"
        if option == 2:  # phone and Analog phones(SCCP Ports)
            sql = basesql + " where d.tkclass=1 and tkmodel!=645 order by DeviceName "
        elif option == 3:  # gateway / Media Resources / SIP Trunk
            sql = basesql + " where d.tkclass in (2,4,5,19,12,18) order by DeviceName"
        elif option == 4:  # All of the above - Including CTI Route Point
            sql = basesql + " where d.tkclass in (1,2,4,5,10,12,18,19) and tkmodel!=645 order by DeviceName"
        elif option == 5:
            print("Coming soon ...")
        ## Normal SQL try
        #print("select" + sql)
        sqlaxlanswer = self.DeviceAxl("select" + sql)

        if sqlaxlanswer == "okay":
            print("Generating Registration Excel")
            rispath = self.GenerateRisExcel()
        else:
            print(str(sqlaxlanswer))
            z = re.search(r'Total[\s\S]+:\s?(\d+)[\s\S]+less\s?than\s?(\d+)\s?rows', str(sqlaxlanswer))
            if z:
                print("DeviceCount is high!! This report might take little more time")
                rispath = self.AXLSQLBreaker(sql, int(z.group(1)), int(z.group(2)))
            else:
                print("Error in regex search. Exiting !!!")
                rispath = ''
                exit()
        return rispath


    def DeviceAxl(self, sql):
        #print (sql)
        try:
            client = Client(wsdl=self.axlwsdl, transport=self.transport, plugins=[self.history])
            axl = client.create_service(self.AXL_BINDING_NAME, self.ADDRESS)
        except (Fault,Exception) as error:
            print ("Error making Client Connection\n\n" + error)
            exit()
        try:
            QueryResult=axl.executeSQLQuery(sql=sql)
            print ("Parsing AXL")
            self.parseAXLResult(QueryResult)
            return "okay"
        except (Fault,Exception) as error:
            return ("Error in the SQL Query\n\n" +str(error))
            exit()

    def parseAXLResult(self, QueryResult):
        if QueryResult['return']!=None:
            for dev in QueryResult['return']['row']:
                #print(dev)
                self.axldict[dev[0].text.upper()]=Device(dev[0].text)
                self.axldict[dev[0].text.upper()].setattr(model=dev[1].text,DeviceClass=dev[2].text,Devicepool=dev[3].text,desc=dev[4].text,proximity=dev[5].text)
            hostname=[dev[0].text for dev in QueryResult['return']['row']]
            print ("Fetching Registration Report for "+str(len(hostname))+" devices. Please hold tight!!")
            try:
                #Parallel Threshold
                THRESHOLD = 315
                chunked_hostname_list=list(self.chunks(hostname,THRESHOLD))
                chunked_hostname_list = tqdm(chunked_hostname_list)
                i = THRESHOLD
                for hostnameSubList in chunked_hostname_list:
                    i+=THRESHOLD
                    chunked_hostname_list.set_description("Processing Max-"+str(THRESHOLD)+" Devices")
                    self.getregisteration(hostnameSubList)

            except Exception as e:
                print ("Error Getting Registeration Report: ",str(e))
                print("Lower the Threshold value to check again.")
        else:
            print ("No Device Found")
    
    def getregisteration(self, macs):
        try:
            client = Client(wsdl=self.riswsdl, transport=self.transport, plugins=[self.history])
            factory = client.type_factory('ns0')
            item=[]
            for mac in macs:
                item.append(factory.SelectItem(Item=mac))
            Item = factory.ArrayOfSelectItem(item)
            stateInfo = ''
            criteria = factory.CmSelectionCriteria(MaxReturnedDevices = 1000,Status='Any',NodeName='',SelectBy='Name',SelectItems=Item)
            result = client.service.selectCmDevice(stateInfo, criteria)
            try:
                # print (result)
                self.setdevicesStatus(result)
            except:
                print ("Error while parsing RIS Report")
        except Exception as error:
            print ("Error in getting RIS report from publisher\n"+str(error))
            #Traceback Error
            traceback.print_exc()

            # for hist in [history.last_sent, history.last_received]:
            #   print(etree.tostring(hist["envelope"], encoding="unicode", pretty_print=True))

    def setdevicesStatus(self, RisReport):
        #print ("Set Device Function TotalDevicesFound:"+str(RisReport['SelectCmDeviceResult']['TotalDevicesFound']))
        for noderesult in RisReport['SelectCmDeviceResult']['CmNodes']['item']:
            code=noderesult['ReturnCode']
            if code=='Ok':
                node=noderesult['Name']
                CmDevices=noderesult['CmDevices']['item']
                for phones in CmDevices:
                    try:
                        if phones['Name'].upper() in self.axldict:
                            if self.axldict[phones['Name'].upper()].getRisStatus() != 'Registered':
                                self.axldict[phones['Name'].upper()].setattr(node=node,protocol=phones['Protocol'],status=phones['Status'],Aload=phones['ActiveLoadID'],Inload=phones['InactiveLoadID'],DirectoryNumber=phones['DirNumber'],IPAddress=phones['IPAddress']['item'][0]['IP'],LoginUserId=phones['LoginUserId'],TimeStamp=time.strftime("%d %b %Y %H:%M:%S %Z", time.localtime(phones['TimeStamp'])))
                    except (Fault,Exception) as error:
                        print ("Set Device Function error :"+str(error))
    

    def AXLSQLBreaker(self, sql,total,chunk):
        runtimes=math.ceil(total/chunk)
        for i in range(0,int(runtimes)+1):
            if i==0:
                out=self.DeviceAxl("select first "+str(chunk)+sql)
            else:
                out=self.DeviceAxl("select skip "+str(chunk*i)+" first "+str(chunk)+sql)
        print ("Generating Registration Excel")
        rispath = self.GenerateRisExcel()
        return rispath

def consolidatedExcelPandas(cluster_list, workbookname):
    writer = pd.ExcelWriter(workbookname + '.xlsx', engine='xlsxwriter')
    columns = ['Cluster','name', 'model','protocol','DeviceClass','Devicepool','desc', 'status', 'node', 'IPAddress' , 'Aload', 'Inload', 'DirectoryNumber', 'LoginUserId', 'TimeStamp','proximity']
    consolidateddf = pd.read_excel(os.getcwd()+'//temp//risreport_temp_' + cluster_list[0] + '.xlsx')
    consolidateddf['Cluster']=str(cluster_list[0])
    consolidateddf = consolidateddf[columns]
    #os.remove(os.getcwd()+'//temp//risreport_temp_' + cluster_list[0] + '.xlsx')
    print("cluster_list="+str(cluster_list))
    for cluster in cluster_list[1:]:
        dataframetemp = pd.read_excel(os.getcwd()+'//temp//risreport_temp_' + cluster + '.xlsx')
        #print('dataframetemp')
        #print(dataframetemp)
        dataframetemp['Cluster']=str(cluster)
        dataframetemp = dataframetemp[columns]
        #print('dataframetemp')
        #print(dataframetemp)
        consolidateddf = consolidateddf.append(dataframetemp)
        #print('consolidateddf')
        #print(consolidateddf)
        os.remove(os.getcwd()+'//temp//risreport_temp_' + cluster + '.xlsx')
    consolidateddf.to_excel(writer, sheet_name="GlobalRegReport",index=False)
    writer.save()


def consolidatedExcel(option, cluster_list, workbookname, cluster_file):
    writer = pd.ExcelWriter(workbookname + '.xlsx', engine='xlsxwriter')
    wb = xlrd.open_workbook(cluster_file)
    sheet = wb.sheet_by_index(0)
    i=1
    for cluster in cluster_list:
        dataframe = pd.read_excel(cluster)
        dataframe.to_excel(writer, sheet_name="registration_report_"+sheet.cell_value(i, 0))
        if int(option)==2:
            firmwaredataframe = Firmwareanalysis.write_analysis_to_excel_pandas(Firmwareanalysis.perform_analysis(dataframe))
            firmwaredataframe.to_excel(writer, sheet_name="firmware_analysis_"+sheet.cell_value(i, 0))
        os.remove(cluster)
        i=i+1
    writer.save()

def fetchregirationreport(cluster_list, cluster_option ,server_row):
    ipaddress = server_row['IP Address']
    username = server_row['Username']
    auth = server_row['Password']
    clusterName = server_row['Name']
    server = Server(ipaddress, username, auth, workbook, clusterName,cluster_option)
    recursion='yes'
    print ("\nFetching All Nodes for "+clusterName)
    fetchresult=server.fetchnodes()
    if fetchresult=="FetchOk":
        print ("\nChecking for the cluster")
        server.AXLSQLMaker(2)
        server.axldict.clear()
        cluster_list.append(clusterName)
    

if __name__ == '__main__':
    cluster_option = input('1. Particular Cluster \n2. Multiple Cluster \n Enter Number: ')
    if int(cluster_option)==1:
        ipaddress = input("Enter Publisher IPAddress/Hostname : ")
        username = input("Please Enter the username with AXL roles : ")
        # username = 'HSBC_PCAT_AXL'
        # print("Please Enter Password for AXLUSER : " + username)
        auth = input("Please Enter Password for AXLUSER - " + username+" : ")

        # auth = getpass.getpass('Enter Password : ')        
        VERSION = input("Enter CUCM version: ")
        server = Server(ipaddress, username, auth, Workbook(), "Regis", cluster_option)
        recursion='yes'
        print ("\nFetching All Nodes in this Cluster")
        fetchresult=server.fetchnodes()
        #Getting Riswsdl from the server
        server.getRiswsdl()
        if fetchresult=="FetchOk":
            print ("\nDone !! Please Select Below Options")
            while recursion=='yes':
                cluster_option=server.inputfunction()
                recursion=server.main(cluster_option)
                server.axldict.clear()

    elif int(cluster_option)==2:
        option = input('1. Registration Report \n2. Firmware Analysis\n Enter Number: ')
        print('Checking for multiple cluster')
        cluster_file_path=input('Enter Cluster File Path:')
        cluster_file = input('Enter Cluster File Name (without .xlsx):')
        clustersdf = pd.read_excel(cluster_file_path+'//'+cluster_file+'.xlsx')
        cluster_list = []
        cluster_dict = clustersdf.T.to_dict().values()
        pool = ThreadPool(3)
        func = partial(fetchregirationreport,cluster_list,cluster_option)
        pool.map(func,cluster_dict)
        pool.close()
        pool.join()
        if int(option)==1:
            consolidatedExcelPandas(cluster_list, "multipleclusterregistrationreport"+time.strftime("%Y%m%d-%H%M%S"))
        if int(option)==2:
            consolidatedExcel(option, cluster_list, "multipleclusterfirmwareanalysis" + time.strftime("%Y%m%d-%H%M%S"), cluster_file)
