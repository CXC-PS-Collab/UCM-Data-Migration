Great !!! So you have decided to take on this adventure 🥁, but before we get some action.. lets understand the pre-reqs.

# Prerequisites and Credentials

- Python 3.x - Provided in this lab browser environment
- Access to CUCM enviroment through VPN
  - CUCM 12.5 (_Source Cluster_): ```<IP address>```
  - CUCM 14 (_Destination Cluster_): ```<IP address>```
  - Login Credentials:
    - Username: ```devnetXX```
    - Password: ```devnet@123```
- VPN Credentials:
  - Server: ```<IP Address>```
  - Username: ```devnetXX```
  - Password: ```devnet@123```
  

# Setting Environment

> Clone Code Repository

```bash
git clone https://github.com/CXC-PS-Collab/DEVWKS-2116.git
```

> Setup python environment

```bash
cd ~/src/UCM-Data-Migration
python3 -m pip install -r requirements.txt
```

> Connect to Cisco VPN to access CUCM labs

```bash
export VPN_SERVER=vpn_server
export VPN_USERNAME=username
export VPN_PASSWORD=password
./startvpn.sh
```

# Understanding Repository

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
   |    |    |-- schema/                   # Contains AXL schema files for CUCM 11.5, CUCM 12.5 & CUCM 14
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

# Understanding CUCM Dependencies

> CUCM Config Dependency graph
- https://check-depencdy.html

