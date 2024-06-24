# data-to-fudo
This script automatizes routine of adding Accounts, Servers, Safes, Operators to FUDO PAM

Use for FUDO PAM 5.4 and later!

Data to Fudo

Script is aumtomatization of:
 - Adding Servers/Accounts/Safes to Fudo based on corresponding CSV data file:
   -  Creating Servers
   -  Adding Servers to Pools(must be created manually)
   -  Creating Accounts; like "A_PAM-<USER>_<PROTOCOL>_<IP>"
   -  Creating Password Changers Accounts(Changer Servers(DC) must be added manually) like "A_CHANGER-<DOM>_PAM-<USER>"
   -  Creating Safes
   -  Assign Users to Safes(Users must be added previously)
   -  Assign Listeners to Safes
 - Setting Operators roles for Users based on corresponding CSV data file:
   - Patching Users to be Operators
   - Granting Operators access to Users
   - Granting Operators access to Safes
   - Granting Operators access to Accounts
   - Granting Operators access to Servers

# Project's structure

- app_scripts/fudo_functions.py - main app functions
- app_scripts/project_helper.py - va helper functions of all project
- app_scripts/project_mailing.py - mail functions for reports and simple mails(enable in main script if you need)
- data_files/con-data - connection data for FUDO, domains info
- data_files/mailing_data.json - mailing data file
- data_files/<YOUR-SCOPE-DATA>.csv - your hosts and users data
- data_files/<YOUR-OPERATORS-DATA>.csv - your operators data
- project_static.py - all vars, urls, mailing data, etc
- set_operators.py - script for setting Operators for FUDO
- ser_srv-pool-acc-safe.py - script for creating Accs, Servers, Safes and Assignings for Safes

# Data FILES

# data_files/<YOUR-SCOPE-DATA>.csv - CSV file for Servers/Accounts/Safes

Columns are:
```
SCOPE/DOMAIN,HOST'S OS/MODEL,HOST'S NAME/DESCRIPTION,HOST'S IP,HOSTS TYPE,"SSH USERS","RDP USERS","HTTP USERS"
```

My HOSTS' TYPES ARE
- HV - HyperVisors
- ND - VA NetworkDevices
- SC - StorageControl
- SM - ServerManager(iLOM, iRMC)
- SN - ServerNix(Linux, Solaris)
- SW - ServerWin

Example of data file(DON'T USE HEADERS) - this is example of only RDP users:
```
SCOPE1,Windows Server 2008 R2,stnd_win2008R2,10.*.*.*,SW,,"USER1, USER2, USER3",
```

Example of data file(DON'T USE HEADERS) - this is example of SSH & HTTP users:
```
SCOPE2,ESXI,esxi-srv-1,10.*.*.*,SW,"USER1, USER2, USER3",,"USER1, USER2, USER3"
```

# data_files/<YOUR-OPERATORS-DATA>.csv - CSV file for Operators

Colums are:
```
OPERATOR'S NAME,LIST OF USERS FOR THIS OPERATOR
```

Example of data file(DON'T USE HEADERS):
```
USER2, USER3 USER4 USER5
```

# data_files/con-data - Connection data file

Rename BLANK_con-data to con-data to use in script!

```
https://<FUDO-MANAGEMENT-SITE>
<FUDO BIND IP FOR SERVERS>
<FUDO API KEY>
<DEFAULT AD PASSWORD FOR PAM-USER MUST BE CHANGED BY CHANGERS>
<SCOPE MARK>|<DOMAIN SHORT MARK>|<DOMAIN FQDN>|<DC IP>
<SCOPE MARK>|<DOMAIN SHORT MARK>|<DOMAIN FQDN>|<DC IP>
<SCOPE MARK>|<DOMAIN SHORT MARK>|<DOMAIN FQDN>|<DC IP>
<SCOPE MARK>|<DOMAIN SHORT MARK>|<DOMAIN FQDN>|<DC IP>
<SCOPE MARK>|<DOMAIN SHORT MARK>|<DOMAIN FQDN>|<DC IP>
```

  * **SCOPE MARK**, for example might be **PCIDSS**
  * **DOMAIN SHORT NAME**, for exmaple might be **DOM1** if you have **domain1.example.com** domain
  * **DOMAIN FQDN**, for example might be **domain1.example.com**
  * **DC IP**, your domain's **Domain Controller's IP**

For scope section I personally need all five scopes. If you have less or more - edit code in **project_static.py** under **# PARSING DATA FILE FOR BASE URL, USER, PASSWORD** comment(**dcs** dict).

# data_files/mailing_data.json - mailing data

Rename BLANK_mailing_data.json to mailing_data.json to use in script!

```
{
  "smtp_server": "<YOUR SMTP SERVER>",
  "smtp_port": 25,
  "smtp_login": "<YOUR SMTP LOGIN>",
  "smtp_pass": "<YOUR SMTP PASSWORD>",
  "smtp_from_addr": "<MAIL FROM ADDRESS>",
  "list_admins": ["admin1@ex.com", "admin2@ex.com"],
  "list_users": ["user1@ex.com", "user2@ex.com"]
}
```

