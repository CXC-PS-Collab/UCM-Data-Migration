### Repository

- This repository provides Steps and Procedure to export Configs from CUCM/CUC/Expressway and import those into new destination Cluster.
- It uses:
  - AXL for CUCM
  - CUPI API for CUC
  - REST API for Expressways
- Make sure users with appropriate rights are created on respective systems (CUCM/CUC/Expressway) for API's to work seamlessly


#### How to:
- Refer individual section Readmes' to understand how to export and import configurations

#### Enhacements:
  - Checkout Documents/features.md for capabilities in development and planned


#### Steps for Migration \[Import/Export Part\]-

1.  Create a virtual environment and install all requirements inside CUCM folder requirements.txt.

2.  Enter source and destination Credentials in sourceJSON.json and ucmDestination.json respectively. \[CUCM>adapter\]. Ping [@Sidharth R Menon (sirmenon)](mailto:sirmenon@cisco.com) or [@Guruprasad Bhat (guruprbh)](mailto:guruprbh@cisco.com) for more clarification if needed in this step.
- For sourceJSON modify the following keys- **sourceCUCM, username, password, version, siteCode, dataFilterJSONKeys**  \[make this a list with one element i.e., sitecode\]
- For ucmDestination modify the following keys- **cucm, username, password, version, configsFolders**  \[make this a list with one element i.e., "<sitecode>-SanitizedData"\]. Additionally turn on UPDATE\_MRGL, UPDATE\_USER etc other UPDATE\_ fields if needed by setting them true.

3.  Generate getDataFilter.json using following method (You can also add entity names manually) - Ping [@Guruprasad Bhat (guruprbh)](mailto:guruprbh@cisco.com) for any help with this:
-  Modify generateInputJson-RetailMapping.py as per your customer preference. \[CUCM>exportConfigs\].
-  Enter Sitecodes in siteInputs.xlsx. \[CUCM>exportConfigs\]
-  Run generateInputJson-RetailMapping.py \[cd into CUCM>exportConfigs\].
-  Modify getDataFilter.json as per the need.\[CUCM>exportConfigs\]

4.  Run exportSiteData.py \[cd into CUCM>exportConfigs\].
-  After exported new folders i.e., CUCM/ConfigExports/sitecode and CUCM/ConfigExports/sitecode-SanitizedData will be created which will have relevant configs in json format.
-  CUCM/ConfigExports/sitecode will also have export xlsx file.

5.  Run importConfigs-Common.py. \[cd into CUCM>importConfigs\].
-  Beware this will be adding resource entities to CUCM, Double check ucmDestination.json for right CUCM credentials.
-  This will generate logs in  CUCM/importConfigs/logs/sitecode folder.

6.  Run updateConfigs-Common.py to update fields.

For any clarification at any step, feel free to ping [@Guruprasad Bhat (guruprbh)](mailto:guruprbh@cisco.com), [@Sidharth R Menon (sirmenon)](mailto:sirmenon@cisco.com), [@Shwetha M (shwm)](mailto:shwm@cisco.com) or [@Ashish K. Mishra (ashimis3)](mailto:ashimis3@cisco.com).

There are some custom scripts as well to do separate tasks and validation. Once above steps are completed successfully, get in touch with us and we will provide info about other scripts.



