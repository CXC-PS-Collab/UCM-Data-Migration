# Automating UCM Migration
**Automation UCM Migration using Collaboration APIs**  
*DevNet Workshop 2022 - DEVWKS-1016* | [Link to Presentation](xxx.pptx) 

Learn about [CUCM AXL](https://developer.cisco.com/docs/axl-developer-guide/) and how to effectively utilise CUCM APIs' and Python to automate migration task involving provisioning, modification and validation of CUCM Data.

- [Automating UCM Migration](#automating-ucm-migration)
  - [Objectives](#objectives)
  - [Prerequisites](#prerequisites)
    - [General Instructions](#general-instructions)
    - [Logins & Credentials](#logins--credentials)
      - [VPN Details](#vpn-details)
      - [CUCM Lab Details](#cucm-lab-details)
    - [Development Environment Setup](#development-environment-setup)
      - [Task 1: Setting up Python Environment](#task-1-setting-up-python-environment)
      - [Task 2: Understanding Repository](#task-2-understanding-repository)
  - [Session Workbooks](#session-workbooks)
  - [Help & Resources](#help--resources)

## Objectives

* Understand CUCM AXL API
* Learn how to write custom logic with python using CUCM AXL Python Library
* Try it yourself workbooks

---

## Prerequisites

### General Instructions

* In order to complete this lab you will need a development workstation with [Python 3.5 and above](https://www.python.org/downloads/) installed.
    * If you are facing issues with installing Python on your system, spin up a [Python container](https://hub.docker.com/_/python) to get started :)
* Access to a CUCM 11.5 (_Source Cluster_) and CUCM 12.5 (_Destination Cluster_) has been provisioned for you (see below for details).
* You need to use `Cisco Anyconnect` to connect to above CUCM labs (see below for details).
* We have already populated _Source Cluster_ with dummy dataset. This is done to proceed with devNet workbooks.

### Logins & Credentials

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

_Please access cucm with your own username/password and access data with your site code only._


### Development Environment Setup

#### Task 1: Setting up Python Environment
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


#### Task 2: Understanding Repository

```bash
< PROJECT ROOT >
   |
   |-- configGraph/                        # Contains Visual Representation of CUCM Configs and it's dependencies
   |    |-- cucm.html                      # HTML page with CUCM Config Nodes
   |    |-- lib/                           # Supporting Configs for CUCM HTML page (no changes required)
   |
   |-- devNet-Workbooks                    # Contains all code base and files required for this devnet lab
   |    |
   |    |-- ciscoaxl/                      # Python Library for Cisco CUCM AXL API
   |    |    |-- schema/                   # Contains AXL schema files for CUCM 11.5 & CUCM 12.5
   |    |    |-- axl.py                    # Python Object Library from AXL schema
   |    |
   |    |-- common/                        # Contains python code base which is common across labs
   |    |-- inputs/                        # User provides Source/Destination cluster details in JSON's defined in this folder
   |    |-- lab1/                          # All hands-On code, data outputs pertaining to Lab 1 will be present in this folder
   |    |-- lab2/                          # All hands-On code, data outputs pertaining to Lab 2 will be present in this folder
   |    |-- lab2-DependencyImport/         # All = code, data outputs pertaining to Lab 2 SIP Trunk dependencies is present here
   |    |-- references/                    # Reference code base for lab 1 and lab 2
   |
   |-- supplementary/                      # Bundle of helpful scripts to extend the functionality
   |-- requirements.txt                     # Development modules - SQLite storage
   |-- Readme.md                                 # Inject Configuration via Environment
   |
   |-- ************************************************************************
```

> 🥁 **You're all set to workshop!**

---
## Session Workbooks

> 😎 **Let's get some action...**

- Head over to Session Workbooks present [here](link.com)

---

## Help & Resources

* Learn more about CUCM API's [here](https://www.splunk.com/en_us/training.html)
* Join the DEVWKS-1016 Webex Teams space [here](https://eurl.io/)
* Add your use-cases to the [PreemptiveOps Framework](https://github.com/) repo
* Fancy a chat?
    * [Aman Sardana](https://amansardana.in) - [Email](mailto:amasarda@cisco.com)
    * [Saurabh Khaneja](https://github.com/sakhanej) - [Email](mailto:sakhanej@cisco.com)