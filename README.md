# data-to-fudo
This script automatizes routine of adding Accounts, Servers, Safes, Operators to FUDO PAM

Data to Fudo

Script is aumtomatization of:
 - Adding Servers/Accounts/Safes to Fudo based on corresponding CSV data file:
   -  Creating Servers
   -  Adding Servers to Pools(must be created manually)
   -  Creating Accounts
   -  Creating Password Changers Accounts(Changer Servers(DC) must be added manually)
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

Assumed that:
- corresponding PAM-users created in your AD/local hosts, for ex. for user USER1 created PAM-USER1 account wiht DEFAULT password(see below in con-data)
- point to all your domain names and dc's IP(for Password changers) if you need several

```
https://<YOUR-FUDO-MGMT-URL>
<YOUR FUDO BIND IP>
<YOUR FUDO API USER - MUST BE SUPERADMIN>
<YOUR FUDO API USER'S PASSWORD>
<YOUR DEFAULT AD PASSWORD FOR PAM-USERS>
<YOUR.DOMAIN1.LOCAL>|<DOMAIN'S DC IP>
<YOUR.DOMAIN2.LOCAL>|<DOMAIN'S DC IP>
```

Domains info will be used in dcs dict in project_static.py - check it carefully.

# data_files/mailing_data.json - mailing data
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

