# Automating UCM Migration
**Automation UCM Migration using Collaboration APIs**  
*DevNet Workshop 2022 - DEVWKS-1016* | [Link to Presentation](xxx.pptx) 

Learn about [CUCM AXL](https://developer.cisco.com/docs/axl-developer-guide/) and how to effectively utilise CUCM APIs' and Python to automate migration task involving provisioning, modification and validation of CUCM Data.

* [Objectives](#objectives)
* [Prerequisites](#prerequisites)
  * [General Instructions](#install-python)
  * [Other Components & Credentials](#review-logins)
* [Workshop Tasks](#ws-tasks)
  * [Task 1: Setting Development Environment](#dev-env)
  * [Task 2: Understanding Repository](#understand-repo)
* [Workbooks](#wb-labs)
  * [Lab 1: CSS and Partition](#ei-css-partition)
  * [lab 2: Route Pattern + Dependencies](#ei-rp-rl-rs)
  * [lab 3: Phones + Dependencies](#ei-phones)
* [Help!](#help)

## Objectives

* Understand CUCM AXL API
* Learn how to write custom logic with python using CUCM AXL API's
* Hands-on with data migration labs

---

## Prerequisites

### General Instructions

* In order to complete this lab you will need a development workstation with [Python 3.5 and above](https://www.python.org/downloads/) installed.
    * If you are facing issues with installing python on your system, spin up a [Python container](https://hub.docker.com/_/python) to get started :)
* Access to a CUCM 11.5 Source Cluster and CUCM 12.5 Destination Cluster has been provisioned for you (see below for details).
* You need to use Cisco Anyconnect to connect to above CUCM labs (see below for details).
* We have already populated CUCM 11.5 Source Cluster with dummy dataset. This is done to proceed with lab task.

### Other Components & Credentials

#### VPN Details
> **VPN information**
◦ Address: `devnetsandbox-usw1-reservation.cisco.com:20244`
◦ Username: `sdmdev`
◦ Password: `VDCCLVXF` 

#### CUCM Lab Details
> **CUCM 11.5 IP (_Source Cluster_):**  10.10.20.15
> **CUCM 12.5 IP (_Destination Cluster_)** 10.10.20.1 

| Pod | Username | Password   | SiteCode |
| --- | -------- | ---------- | -------- |
| #1  | devnet01 | devnet@123 | POD1     |
| #2  | devnet02 | devnet@123 | POD2     |
| #3  | devnet03 | devnet@123 | POD3     |
| #4  | devnet04 | devnet@123 | POD4     |
| #5  | devnet05 | devnet@123 | POD5     |
| #6  | devnet06 | devnet@123 | POD6     |
| #7  | devnet07 | devnet@123 | POD7     |
| #8  | devnet08 | devnet@123 | POD8     |
| #8  | devnet09 | devnet@123 | POD9     |
| #8  | devnet10 | devnet@123 | POD10    |
| #8  | devnet11 | devnet@123 | POD11    |
| #8  | devnet12 | devnet@123 | POD12    |

_Please access cucm with your own username/password and access data with your site code._

### 🥁 **You're all set to workshop!**

---

## Workshop Tasks

### Task 1: Setting Development Environment
On your Terminal (Mac/Linux) or Command Prompt (Windows):

> **Task 0.1: Confirm Python3.x is installed**
```bash
python3
```

```bash
# Sample Output
Python 3.9.1 (default, Dec 29 2020, 09:45:39) 
[Clang 12.0.0 (clang-1200.0.32.28)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>>
```
> **Task 0.1.1: If Python3.x is not installed, then follow below steps**

- **Python Version**: 3.10.4
- Download Python based on your workstation OS:
  - _Windows(64 bit)_: https://www.python.org/ftp/python/3.10.4/python-3.10.4-amd64.exe
  - _Windows(32 bit)_: https://www.python.org/ftp/python/3.10.4/python-3.10.4.exe
  - _Mac OS_: https://www.python.org/ftp/python/3.10.4/python-3.10.4-macos11.pkg

- For _Windows_, Double-click the `exe` file to install Python. Make sure to tick ☑️ Add python to path
- For _Mac_, Double-click the `pkg` file to install Python

- Validate Installation with *Task 0.1*
  
> **Task 0.2: Confirm Python PIP is installed**
```bash
pip -V
```

```bash
# Sample Output
pip 21.1.3 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)
```
> **Task 0.2.1: If Python PIP is not installed, then follow below steps**

  > **Windows Workstation**
  - Download [Python PIP](https://bootstrap.pypa.io/get-pip.py) store it in the same directory as python is installed.
  - Install PIP with below command and wait through the installation process.
    
  ```bash
  python get-pip.py
  ```
 

  > **MAC OS Workstation**
  ```bash
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  ```

  - Install PIP with below command and wait through installation process
    ```bash
    python3 get-pip.py
    ```
 - Validate Installation with *Task 0.2*

> **Task 0.3: Take Git pull of this repository**

```bash
git clone https://github.com/shwetham09/UCM-Data-Migration.git
```

```bash
# Sample Output
Cloning into 'UCM-Data-Migration'...
remote: Enumerating objects: 86, done.
remote: Counting objects: 100% (86/86), done.
remote: Compressing objects: 100% (53/53), done.
remote: Total 86 (delta 29), reused 86 (delta 29), pack-reused 0
Unpacking objects: 100% (86/86), 952.36 KiB | 2.36 MiB/s, done.
 -- ommitted --
```

> **Task 0.4: Setup/Start Python Virtual Environment**
  > Install Python Library virtualenv
  ```bash
  python3 -m pip install virtualenv
  ```

  > Create Virtualenv
  ```bash
  python3 -m venv env
  ```

  > Activate Virtual Env
  *MAC*: `source env/bin/activate`
  *Windows*: `.\env\Scripts\activate`

> **Task 0.5: Install Required Python Libraries**

```bash
python3 -m pip install -r requirements.txt
```

> **Task 0.5: Login to CUCM to make sure your access is working**

1. Fire up your web browser and head over to `10.10.20.15`
2. Login with Username: `devnetxx` & Password: `devnet@123`
3. Repeat steps (1,2) with 12.5 CUCM Cluster `10.10.20.1`

#### 🤷 **Uff!!!, these were some serious setup**

### Task 2: Understanding Repository

```bash
< PROJECT ROOT >
   |
   |-- Workbooks/                          # Contains all lab use cases
   |    |-- ciscoaxl/                      # Base AXl Class Library
   |    |-- adapters/                       
   |    |-- lab1/                          # Contains all code base relevant to lab 1
   |    |-- lab2/                          # Contains all code base relevant to lab 2
   |    |-- lab3/                          # Contains all code base relevant to lab 3
   |
   |-- Workbooks/ciscoaxl/
   |    |
   |    |-- schema/                        # A simple app that serve HTML files
   |    |    |-- 11.5/
   |    |    |    |-- AXLAPI.wsdl                  # Serve HTML pages for authenticated users
   |    |    |    |-- AXLEnums.xsd                   # Define some super simple routes
   |    |    |    |-- AXLSoap.xsd
   |    |
   |         |-- 12.5/                # Handles auth routes (login and register)
   |    |    |    |-- AXLAPI.wsdl                  # Define authentication routes  
   |    |    |    |-- AXLEnums.xsd                  # Handles login and registration  
   |    |    |    |-- AXLSoap.xsd                  # Define auth forms (login and register)
   |    | 
   |    |    |-- axl.py
   |
   |-- Workbooks/adapter/
   |    |-- sourceJSON.json
   |    |-- ucmDestination.json
   |    |-- importLogic.json
   |    |-- importLogicBase.json
   |    |-- getDatFilter.json
   |    | 
   |
   |-- Workbooks/lab1/
   |    |-- exportConfigs.py
   |    |-- importConfigs.py
   |    |-- sanitise.py
   |    |-- validate.py
   
   |
   |-- requirements.txt                     # Development modules - SQLite storage
   |
   |-- Readme.md                                 # Inject Configuration via Environment
   |
   |-- ************************************************************************
```

<br />

## Workbooks

#### 🥁 **Let's get some action...**

### Pre-Setup

- Lets make sure our `adapters` are set with right configuration.
 > sourceCluster.json
  ```json
  {
    "sourceCUCM": "<Source Cluster IP/Hostname>",
    "username": "devnetXX",
    "password": "devnet@123",
    "version": "11.5",
    "siteCode": ["PODXX"]
  }
  ```
  > destinationCluster.json
  ```json
  {
    "cucm": "<Destination Cluster IP/Hostname>",
    "username": "devnetXX",
    "password": "devnet@123",
    "version": "12.5"
  }
  ```
  > importLogicJson.json: No modification needed
  ```json
  {
    "Partitions": {
        "file": "partition.json", 
        "axlMethod": "add_partition",
        "headersToRemove": [
          "dialPlanWizardGenId"
        ],
        "output": "name" 
      }
  }
  ```
  > excelJSONConversion.py
  - `excelJSONConversion.py`: Supplementary script which helps us convert the JSON output into Excel Workbook


### Lab 1: CSS and Partition

> **Requirements**

- Migrate all CSS and it's dependency record from Source Cluster (11.5) to Destination Cluster (12.5)
- Generate validation report to make sure data is successfully migrated

> **Data Understanding**
1. Login to Source Cluster and understand how CSS and Partions are created.
2. You will observe that CSS and Partition are created in following format:
   1. CSS: <siteCode>_<type>_CSS
   2. Partition: <siteCode>_<type>_PT

> **Let's Start Coding**

1. Generate 

### Lab 2: CSS and Partition 

> **Requirements**

- Migrate all CSS and it's dependency record from Source Cluster (11.5) to Destination Cluster (12.5)
- While adding Partitions to destination cluster, change the order of Parition




#### Task 1: Getting your data ready for indexing

> **Task 1.1: Working with the sample dataset**

> _In this section, you will be pulling data into Splunk that will be used as training data for your Machine Learning models._

1. Download & save this file to your desktop: https://devnet-preemptiveops.s3.us-east-2.amazonaws.com/sampledataset.csv
2. On Splunk, go to _Settings_ > _Add Data_ > _Upload (files from my computer)_
3. _Select File_ > Browse to & select the downloaded file & wait for upload to finish > Click _Next_
4. Confirm that _Source type: csv_ was automatically detected > click _Next_
5. Click _Create a new index_
    - Index Name: security_dataset
    - Leave all other options as is
6. Click _Review_ > _Submit_

-- insert screenshot here --

> **Task 1.2: Set up real-time logging**

> _In this section, you will be pulling data into Splunk that will be used to simulate real network traffic. Think of this as streaming telemetry from a firewall service or incoming access requests from a web service log.<br>
> Note: For the purposes of this lab, Splunk is pulling data in. In most production environments, to avoid polling latency, devices push telemetry data to Splunk._

1. On Splunk, go to _Settings_ > _Add Data_ > _Monitor (files and ports on this Splunk platform instance)_
2. Select _Scripts_, then populate the following & click _Next_:
    - Script Path: 
    - Command: 
    - Interval Input: 
    - Source name override: 
3. Select _Source type_ as _Structured_ > _.csv_
4. Click _Create a new index_
    - Index Name: security_telemetry
    - Leave all other options as is
5. Click _Review_ > _Submit_

-- insert screenshot here --

#### Task 2: Searching through events

> _It's time to SPL! You've got some data into the system - now let's query it._

On Splunk, go to _Apps_ > _Search & Reporting_

> **Task 2.1: Querying the sample dataset**

1. Set the time-period to _All time_ & type the following into the search bar:

```
index = security_dataset
```

2. Tabulate the results by adding the following statement:

```
| table _time source_ip source_port destination_ip destination_port
```

> **Task 2.2: Querying the streaming telemetry**

1. Open another _Search_ window, set the time-period to _All time_ & type the following into the search bar:

```
index = security_telemetry
| table _time source_ip source_port destination_ip destination_port
```

2. Wait for a minute and re-run the query. You should see the count next to 'Statistics' growing - indicating that events in real-time are coming in to Splunk!

**🚩 Checkpoint #1:** You are now **Reactive** _(meh)_. Your network's data is  making it to Splunk. This gives you the ability to search and quickly find events leading up to or following an incident report - assuming you know what you're looking for.

#### Task 3: Reporting, Dashboarding & Alerting

> _Ok, so you've got events & you've got the ability to query 'em. Wouldn't it be nicer if we could make this data more consumable for your IT team to monitor?_<br>
>_In this section, we're going to arrive at logic to group similar, recurring events together, present them on a single pane that refreshes automatically & trigger an email alert when specific conditions are met._

> **Task 3.1: Doing more with SPL**<br>

- In a _Search_ window, set the time-period to _All time_ & type the following into the search bar:

```
index = security_telemetry
| table 
| stats do something
```

> **Task 3.2: Creating a Dashboard**

- Click _Save As_ > _Dashboard Panel_
    - Dashboard Title: 
    - Dashboard Permissions: Shared in App
    - Panel Title: 
    - Click _Save_

- Add more panels to your dashboard with the following queries:

```
index = security_telemetry
| table 
| stats do something
```

```
index = security_telemetry
| table 
| stats do something
```

```
index = security_telemetry
| table 
| stats do something
```

```
index = security_telemetry
| table 
| stats do something
```

> _Alternatively, you could get the .xml code to a dashboard we already setup to work with this data from [here]()._

-- insert screenshot here --

> **Task 3.3: Basic Alerting**

1. In a _Search_ window, set the time-period to _All time_ & type the following into the search bar:

```
index = security_telemetry
| table 
| stats do something
```

2. Click _Save As_ > _Alert_
    - Title: 
    - Permissions: Shared in App
    - Alert type: Real-time
    - Expires: 24 hour(s)
    - Trigger alert when: Number of Results
        - is greater than: 0
        - in 1 minute(s)
    - Trigger: Once
    - Trigger Actions > Add Actions: Send email

**🚩 Checkpoint #2:** You are now **Proactive** _(still meh)_. Your network's data is making it to Splunk, you've added additional logic in place to group similar events together, made them available on a good lookin' Dashboard for IT to look at and have configured email alerts to warn you when certain conditions are met in case no one's looking at the dashboard. In other words, you're now staying on top of your data.

#### Task 4: Hands-on with the Machine Learning Toolkit (MLTK)

> _You've come a long way, but you're not quite there yet. Devices generate a lot of noise. Too many alerts/emails make it harder for IT to pay attention to the alerts that actually warrant attention. Many times, damage is imminent, however, not obvious._<br>
>_In this section, we're going to use historic data (lots of it), to predict if an attack is about to happen based on when similar symptoms & patterns are seen in real-time telemetry data._

> **Task 4.1: Overview of Splunk MLTK Capabilities**

1. From the app-switcher in the Splunk bar, select _Splunk Machine Learning Toolkit_
2. ..
3. ...

> **Task 4.2: Feature Extraction**

1. .
2. ..
3. ...

> **Task 4.3: Putting it all together on a Dashboard**

1. .
2. ..

-- insert screenshot here --

**🚩 Checkpoint #3:** You are now **Predictive** _(we're getting there!)_. The Machine Learning Toolkit on Splunk helped you put your data through ML models without having to worry about their programmatic implementation - letting you focus on your outcomes. The pre-packaged visualizations & dashboards offer a variety of ways you could present your data in for it to have the most meaningful impact on your IT organisation.

#### Task 5: Custom Alert Action Framework

> _Nice job putting those fancy charts together that let you look ahead of time. But hey - you still need someone to look at all of those insights you've put together and take action before it's too late. With all things security, a five minute window of negligience could cost you a lot of business. Enable automation to act on your predictions ahead of time. Better safe than sorry._<br>
>_In this section, we're going to tie your predictions into Splunk's native 'Actions' and then the custom alert action framework to pass control over to Action Orchestrator that will give you more control over the actions you'd like to automate._

> **Task 5.1: Get your MLTK search to trigger a webhook**

1. Here's the search we worked out in the previous section:

```
index = security_telemetry
| table 
| stats do something
```

2. Click _Save As_ > _Alert_
    - Title: 
    - Permissions: Shared in App
    - Alert type: Real-time
    - Expires: 24 hour(s)
    - Trigger alert when: Number of Results
        - is greater than: 0
        - in 1 minute(s)
    - Trigger: Once
    - Trigger Actions > Add Actions: Webhook
        - URL: 

> _You've just sent a POST to a web service that passes control over to our instance of Action Orchestrator (AO) that lives in the cloud. We're going to receive this trigger & do great things on AO in the next section!_

> **Task 5.2: Sneek-Peek into AO!**

1. Login to Cisco CloudCenter Suite using the information available in [Other Components & Credentials](#review-logins)<br><br>-- insert screenshot here --

2. Click on _Action Orchestrator_ > _Import_
    - Import From: Browse
    - In the _Paste JSON or Upload the Workflow to Import_ textbox, copy-paste the raw contents of [_ao-workflow.json_](/ao-workflow.json)
    - Click Import & wait for a minute > then Refresh the page
3. You should now see your imported workflow on the _My Workflows_ page, open it and investigate each activity block

> **Task 5.3: Get your MLTK search to trigger an on-box python script**

1. First, we need to get a custom alert action application (and our script within) to live on the Splunk container.
    - This step is already done for you when you pulled the container image.
    - The contents of the app are packaged on this repo in the folder [_preempt_custom_action_](/preempt_custom_action)

2. Repeat 5.1 > Step 1
3. Click _Save As_ > _Alert_
    - Title: 
    - Permissions: Shared in App
    - Alert type: Real-time
    - Expires: 24 hour(s)
    - Trigger alert when: Number of Results
        - is greater than: 0
        - in 1 minute(s)
    - Trigger: Once
    - Trigger Actions > Add Actions: preempt_custom_action
        - .
        - ..

**🚩 Checkpoint #4:** You are now **Preemptive** _(woohoo!)_. You made it! 🎉 <br>Your MLTK searches are triggering actions and passing control over to automation to remediate issues or take precautionary measures before issues occur. According to Cisco's IT Operations Readiness Index, only 14% of organisations are at this level today.


#### Task 6: Simulation

> _Lets do a quick test to validate if our dashboards, models & actions are indeed working as they should. In this section, you're going to simulate a Denial of Service attack by increasing the frequency of the streaming telemetry data making it to your Splunk instance and watch it take corrective actions._

> **Task 6.1: Generating additional events**

1. .
2. ..
3. ...

> **Task 6.2: Validating if corrective action took place**

1. .
2. ..
3. ...

---

### Use Case 2: Capacity

---

## Help & Resources

* Learn more about Splunk [here](https://www.splunk.com/en_us/training.html)
* Join the PreemptiveOps Framework Webex Teams space [here](https://eurl.io/)
* Add your use-cases to the [PreemptiveOps Framework](https://github.com/) repo
* Fancy a chat?
    * [Aman Sardana](https://amansardana.in) - [Email](mailto:amasarda@cisco.com)
    * [Saurabh Khaneja](https://github.com/sakhanej) - [Email](mailto:sakhanej@cisco.com)