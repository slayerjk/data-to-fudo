"""
- logging settings
- date settings
- static initial project's data
"""

import logging
from datetime import datetime
import json
from os import path, mkdir

# COMMON DATA

# SCRIPT APPNAME(FOR SEND MAIL FUNCTION, LOGNAME, ETC)
appname = 'DATA-TO-FUDO'

# SCRIPT DATA DIR
'''
By default script uses script's location dir.
If you need custom path for script(sensitive) data
'''
data_files = 'data_files'

# SET TIME TO
start_date_n_time = datetime.now()
start_date = start_date_n_time.strftime('%d-%m-%Y')

# LOGGING SECTION

# LOGS LOCATION
'''
By default script uses script's location dir.
'''
logs_dir = 'logs'

# CHECK LOGS DIR EXIST/CREATE
if not path.isdir(logs_dir):
    mkdir(logs_dir)

# LOGS FORMAT
'''
logging_format: is for string of log representation
logging_datefmt: is for representation of %(asctime) param
'''
logging_format = '%(asctime)s - %(levelname)s - %(message)s'
logging_datefmt = '%d-%b-%Y %H:%M:%S'

# LOG FILEMODE
'''
a - for "append" to the end of file
w - create new/rewrite exist
'''
log_filemode = 'w'

# LOGS TO KEEP AFTER ROTATION
logs_to_keep = 30

# DEFINE LOG NAME
app_log_name = f'{logs_dir}/{appname}_{str(start_date)}.log'

# DEFINE LOGGING SETTINGS
logging.basicConfig(filename=app_log_name, filemode=log_filemode, level=logging.INFO,
                    format=logging_format, datefmt=logging_datefmt)


# MAILING DATA
mailing_data = f'{data_files}/mailing_data.json'
with open(mailing_data, encoding='utf-8') as file:
    data = json.load(file)
    smtp_server = data['smtp_server']
    smtp_port = data['smtp_port']
    smtp_login = data['smtp_login']
    smtp_pass = data['smtp_pass']
    smtp_from_addr = data['smtp_from_addr']
    mail_list_admins = data['list_admins']
    mail_list_users = data['list_users']

# VA PROJECT REGARDING DATA

# SERVERS FILES
# servers_file = f'{data_files}/KIA(PCI)_plus_NESTEROM.csv'
servers_file = f'{data_files}/TSOIB-Systems_TEST.csv'


# OPERATORS FILE
operators_file = f'{data_files}/Operators-TEST-1.csv'

# CONNECTION DATA
data_file = f'{data_files}/con-data'

# PARSING DATA FILE FOR BASE URL, USER, PASSWORD
with open(data_file, 'r') as file:
    data = [string.strip() for string in file.readlines() if len(string) > 0]
    fudo_base_url = data[0]
    fudo_bind_ip = data[1]
    fudo_api_key = data[2]
    acc_pwd = data[3]

    # scope: [changer_zone, domain, dc-ip]
    dcs = {
        data[4].split('|')[0]: data[4].split('|')[1:],
        data[5].split('|')[0]: data[5].split('|')[1:],
        data[6].split('|')[0]: data[6].split('|')[1:],
        data[7].split('|')[0]: data[7].split('|')[1:],
        data[8].split('|')[0]: data[8].split('|')[1:]
    }

fudo_headers = {
    'Content-Type': 'application/json'
}

# FUDO API AUTH
fudo_auth_headers = {
    'Authorization': fudo_api_key
}

# FUDO REQUESTS DATA ###
fudo_proxies = {
    'http': None,
    'https': None
}

# FUDO URL PARAMETERES
server_url_parameters = '?fields=id,name,address,protocol,description'
account_url_parameters = '?fields=id,name,server_id,ocr_enabled'

# FUDO URLS

# DEPRECATED IN FUDO 5.4, USE API KEY
fudo_auth_url = f'{fudo_base_url}/api/system/login'

fudo_server_url = f'{fudo_base_url}/api/v2/server{server_url_parameters}'
fudo_account_url = f'{fudo_base_url}/api/v2/account{account_url_parameters}'
fudo_safe_url = f'{fudo_base_url}/api/v2/safe'
fudo_user_url = f'{fudo_base_url}/api/v2/user'
fudo_pools_url = f'{fudo_base_url}/api/v2/pool'
fudo_listener_url = f'{fudo_base_url}/api/v2/listener'

fudo_user_to_safe_assignment_url = f'{fudo_base_url}/api/v2/user/safe'
fudo_account_safe_listener_url = f'{fudo_base_url}/api/v2/account/safe/listener'
fudo_pools_server_url = f'{fudo_base_url}/api/v2/pool/server'

fudo_modify_user_url = f'{fudo_base_url}/api/v2/user'
fudo_modify_account_url = f'{fudo_base_url}/api/v2/account'
fudo_modify_server_url = f'{fudo_base_url}/api/v2/server'

fudo_grant_access_user_url = f'{fudo_base_url}/api/v2/grant/user'
fudo_grant_access_safe_url = f'{fudo_base_url}/api/v2/grant/safe'
fudo_grant_access_account_url = f'{fudo_base_url}/api/v2/grant/account'
fudo_grant_access_server_url = f'{fudo_base_url}/api/v2/grant/server'
