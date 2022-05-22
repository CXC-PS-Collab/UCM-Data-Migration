# Automating UCM Migration (Lab Workbooks)
**Automation UCM Migration using Collaboration APIs**  
*DevNet Workshop 2022 - DEVWKS-1016* | [Link to Presentation](xxx.pptx) 

Learn about [CUCM AXL](https://developer.cisco.com/docs/axl-developer-guide/) and how to effectively utilise CUCM APIs' and Python to automate migration task involving provisioning, modification and validation of CUCM Data.



- [Automating UCM Migration (Lab Workbooks)](#automating-ucm-migration-lab-workbooks)
  - [Lab Readiness](#lab-readiness)
  - [Lab 1: CSS and Partition](#lab-1-css-and-partition)
    - [Requirements](#requirements)
    - [Data Understanding](#data-understanding)
    - [Migration Approach](#migration-approach)
  - [Lab 2: Route Pattern and dependencies](#lab-2-route-pattern-and-dependencies)


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

## Lab 1: CSS and Partition

> For this lab, start coding in **lab1/lab1-handsOn.py**

### Requirements

- Data Migration from Source to Destination:
  - CSS
  - Partitions
- Understanding how dependent data should be exported and imported in CUCM

### Data Understanding
1. Login to Source Cluster and understand how CSS and Partitions are created.
2. You will observe that CSS and Partition are created in following format:
   1. CSS: <siteCode>_<type>_CSS
   2. Partition: <siteCode>_<type>_PT

> Dependency Tree:
<img width="400" alt="image" src="https://user-images.githubusercontent.com/40081345/169704271-1393ef1d-c8be-430f-baa2-7a7ca8acde67.png">


> **Let's Start Coding**

### Migration Approach
> Refer **references/lab1-reference.py** if stuck anywhere


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
   1. We must supply CSS names as filter parameter to extract from Source Cluster
   2. In our lab, we have 4 CSS per site, but in production, we can have multiple sites following same data pattern
   3. Use `generate_config_patterns` func to dynamically create Input JSON. 
   4. Post completion, run `generate_config_patterns` to create a `getDataFilter.json` file

> _getDataFilter.json_: Contains list of all CSS that we need to export

4. Export Configurations:
   1. Head on to `SiteDataExport` func, to code CSS and Partition export logic. 
   2. Halt and understand the response from: `get_calling_search_space` and `get_partition` methods of AXL object.
   3. Post completion, run `export_CSS_Partition` func to export configs from Source Cluster
      1. You would find a new folder getting created `ConfigExports`. This folder will contain:
         1. *css.json*: Export of CSS Configs
         2. *partition.json*: Export of Partition Configs

5. Import Configurations:
  > _While importing configs, we need to ensure import order is followed i.e. Paritions before CSS_

   1. In this lab, we have created this import logic dynamically following the import order:
      1. `common/importLogic.json`
         1. This JSON contains the import order of CUCM configs and AXL methods required to import configs
   
      2. `common/importLogic.py`: 
         1. This file contains the `updateConfigs` func which dynamicaly import configuration based on parameters defined in `importLogic.json` file
   
   2. Head on to `import_CSS_Partition` func to import CSS and Partitions to destination cluster

6. Verify Configuration are imported properly by logging into destination CUCM. _This method can also be automated as extension to this script_


> 🥁 **You have successfully completed Lab 1**

> **_Head on to Lab 2 for some more fun..._**

## Lab 2: Route Pattern and dependencies

> **Requirements**

- Migrate all CSS and it's dependency record from Source Cluster (11.5) to Destination Cluster (12.5)
- While adding Partitions to destination cluster, change the order of Parition

