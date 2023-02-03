Great !!! So you have decided to take on this adventure 🥁, but before we get some action, let's understand the pre-reqs.

# Pre-requisites and Credentials

- Python 3.x - Provided in this lab browser Environment
- Access to CUCM Environment through VPN
  - CUCM 12.5 (_Source Cluster_): ```https://10.10.20.15/```
  - CUCM 14 (_Destination Cluster_): ```https://10.10.20.1/```
  - Login Credentials:
    - ReadOnlyUser: ```devnetro/devnet@123```
    - AXLUser: ```devnetaxl/devnet@123```
- CUCM Config Dependency Graph: ```http://10.10.20.50/```

# Setting Environment

> Clone Code Repository

```bash
git clone https://github.com/CXC-PS-Collab/DEVWKS-2116.git
```

> Setup python environment

```bash
cd ~/src/DEVWKS-2116
python3 -m pip install -r requirements.txt
```

> Connect to Cisco VPN to access CUCM labs

```bash
export VPN_SERVER=devnetsandbox-usw1-reservation.cisco.com:20177
export VPN_USERNAME=sbxdemouser
export VPN_PASSWORD=Cisco@123

/usr/local/bin/startvpn.sh
```
- keep this terminal session open and hit "+" to open a new terminal session

# Understanding Repository

```bash
< PROJECT ROOT >
   |
   |-- common/                        # Contains python code base which is common across labs
   |    |-- baseFunctions.py          # Clean JSON object and write results to file functions
   |    |-- importLogic.json          # Import order of CUCM Configs
   |    |-- importlogic.py            # Import Logic Python Code
   |
   |-- ciscoaxl/                      # Python Library for Cisco CUCM AXL API
   |    |-- schema/                   # Contains AXL schema files for CUCM 11.5, CUCM 12.5 & CUCM 14
   |    |-- axl.py                    # Python Object Library from AXL schema
   |
   |-- CSS_Partition                   # Contains all code base pertaining to lab 1
   |    |-- lab1.py                    # Python code file for lab 1
   |
   |-- RP_RL_RG                        # Contains all code base pertaining to lab 2
   |    |-- lab2.py                    # Python code file for lab 2
   |    |
   |-- inputs                          # Details on Source and Destination clusters
   |    |-- sourceCluster.json         # Connection details for Source cluster (12.5)
   |    |-- destinationCluster.json    # Connection details for Destination cluster (14.0)
   |-- requirements.txt                # Development modules
   |
   |-- ************************************************************************
```