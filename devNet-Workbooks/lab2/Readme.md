# Automating UCM Migration (Lab 2)
**Automation UCM Migration using Collaboration APIs**  
*DevNet Workshop 2022 - DEVWKS-1016* | [DEVWKS1016.pdf](https://github.com/CXC-PS-Collab/UCM-Data-Migration/files/8893025/DEVWKS1016.pdf) 

Learn about [CUCM AXL](https://developer.cisco.com/docs/axl-developer-guide/) and how to effectively utilise CUCM APIs' and Python to automate migration task involving provisioning, modification and validation of CUCM Data.



- [Automating UCM Migration (Lab 2)](#automating-ucm-migration-lab-2)
  - [Lab Readiness](#lab-readiness)
  - [Route Pattern and dependencies](#route-pattern-and-dependencies)
    - [Requirements](#requirements)
    - [Data Understanding](#data-understanding)
    - [Migration Approach](#migration-approach)


## Lab Readiness

- Lets make sure our `inputs` are set with right values.
 > devNet-Workbooks/inputs/sourceCluster.json
  ```json
  {
    "sourceCUCM": "<Source Cluster IP/Hostname>",
    "username": "devnetXX",
    "password": "devnet@123",
    "version": "11.5",
    "siteCode": ["PODXX"]
  }
  ```
  > devNet-Workbooks/inputs/destinationCluster.json
  ```json
  {
    "cucm": "<Destination Cluster IP/Hostname>",
    "username": "devnetXX",
    "password": "devnet@123",
    "version": "12.5",
    "configsFolders": ["PODXX"]
  }
  ```
  > Naming Conventions:
  - Source Cluster or 11.5 or Source: Points to CUCM 11.5 Cluster
  - Destination Cluster or 12.5 or Destination: Points to CUCM 12.5 Cluster

## Route Pattern and dependencies

> For this lab, start coding in **lab2/lab2-handsOn.py**

### Requirements

- Data Migration from Source to Destination:
  - Route Pattern
  - Route List
  - Route Group
  - SIP Trunks
- Understanding how dependent data should be exported and imported in CUCM

### Data Understanding
1. Login to Source Cluster and understand how RP/RL/RG are created.
2. You will observe that Route Patterns belong to certain partition:
   1. Partition: <siteCode>_<type>_PT
3. Validate SIP Trunks are migrated from Source to Destination. This is done as part of lab setup

> Dependency Tree: Route Pattern

![image](https://user-images.githubusercontent.com/40081345/169755205-6f4966a4-af10-4580-9da8-fbb933998799.png)

> Dependency Tree: Route List

![image](https://user-images.githubusercontent.com/40081345/169755500-ae244b84-6087-43bb-b061-bd39efb22743.png)

> Dependency Tree: Route Group

![image](https://user-images.githubusercontent.com/40081345/169755343-7613817c-f6fe-4bb1-ac73-b05145767d8a.png)


> **Let's Start Coding**

### Migration Approach
> Refer **references/lab2-reference.py** if stuck anywhere


1. Read Input files:
   1. **sourceCluster.json**: _This file provides details required to connect to source cluster_ 
   2. **destinationCluster.json**: _This file provides details required to connect to destination cluster_

    > _Open and Read JSON Files into Python Dictionary
    ```python
    json.load(open(abc.json))
    ```

2. Create AXL objects for Source and Destination cluster
   
  ```python
  from ciscoaxl import axl

  ucm_axl_object = axl(
    username=,
    password=,
    cucm=,
    cucm_version=,
  )
  ```
3. Generate Configuration Patterns:
   1. In order to extract Route Patterns, we must either provide RP pattern as filter parameter OR provide Partition Name as filter parameter
   2. In this lab, we provide Partition Name as filter parameter to extract from Source Cluster
   3. In our lab, we have 4 PT per site, but in production, we can have multiple sites following same data pattern
   4. Use `generate_config_patterns` func to dynamically create Input JSON. 
   5. Post completion, run `generate_config_patterns` to create a `getDataFilter.json` file

> _getDataFilter.json_: Contains list of all CSS that we need to export

4. Export Configurations:
   1. Head on to `SiteDataExport` func, to code `Route Pattern --> Route List --> Route Group --> Parition` export logic. 
   2. Halt and understand the response from: `get_route_patterns`, `get_route_list` and `get_route_group` methods of AXL object.
   3. Post completion, run `export_RP_Dependencies` func to export configs from Source Cluster
      1. You would find a new folder getting created `ConfigExports`. This folder will contain:
         1. *routepattern.json*: Export of Route Pattern Configs
         2. *routelist.json*: Export of Route List Configs
         3. *routegroup.json*: Export of Route Group Configs
         4. *partition.json*: Export of Partition

5. Import Configurations:
  > _While importing configs, we need to ensure import order is followed i.e. Paritions, Route Group, Route List, Route Pattern_

  > All remaining dependecy configs (SIP Trunk, CMG) are already imported in the destination cluster for this lab. In production environment, your script should take of this export/import also. SIP Trunk export/import script present in _supplementary_ directory

   1. In this lab, we have created this import logic dynamically following the import order:
      1. `common/importLogic.json`
         1. This JSON contains the import order of CUCM configs and AXL methods required to import configs
   
      2. `common/importLogic.py`: 
         1. This file contains the `updateConfigs` func which dynamicaly import configuration based on parameters defined in `importLogic.json` file
   
   2. Head on to `import_RP_Dependencies` func to import CSS and Partitions to destination cluster

6. Verify Configuration are imported properly by logging into destination CUCM. _This method can also be automated as extension to this script_


> 🥁 **You have successfully completed Lab 2**

