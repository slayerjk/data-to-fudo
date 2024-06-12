#!/usr/bin/env python3

# DISABLE SSL WARNINGS
import urllib3
from time import perf_counter

# IMPORT PROJECTS PARTS
from app_scripts.project_helper import (
    files_rotate,
    check_file,
    check_create_dir,
    func_decor
)

from project_static import (
    appname,
    data_files,
    start_date_n_time,
    logging,
    logs_dir,
    logs_to_keep,
    operators_file,
    data_file,
    fudo_proxies,
    fudo_account_url,
    fudo_safe_url,
    fudo_user_url,
    fudo_modify_user_url,
    fudo_grant_access_user_url,
    fudo_grant_access_safe_url,
    fudo_grant_access_account_url,
    fudo_grant_access_server_url
)

from app_scripts.fudo_functions import (
    parse_operators_file,
    get_users_ids,
    get_servers_n_accounts_ids,
    get_safes_ids,
    set_operator_role,
    set_grants
)

# FUDO API AUTH
from project_static import fudo_auth_headers

# MAILING IMPORTS
# from app_scripts.project_static import mailing_data, smtp_server, smtp_port, smtp_login, smtp_pass, smtp_from_addr,\
#     mail_list_admins, mail_list_users
# from app_scripts.project_mailing import send_mail_report, send_mail


# DISABLE SSL WARNINGS
urllib3.disable_warnings()


# SCRIPT STARTED ALERT
logging.info(f'SCRIPT WORK STARTEDED: {appname}')
logging.info(f'Script Starting Date&Time is: {str(start_date_n_time)}')
logging.info('----------------------------\n')


# START PERF COUNTER
start_time_counter = perf_counter()


# CHECK DATA DIR EXIST/CREATE
check_create_dir(data_files)

# CHECK LOGS DIR EXIST/CREATE
check_create_dir(logs_dir)

# CHECK MAILING DATA EXIST
# func_decor(f'checking {mailing_data} exists', 'crit')(check_file)(mailing_data)

# CHECKING ALL APP FILES IS PRESENTED
func_decor(f'checking {operators_file} exists', 'crit')(check_file)(operators_file)
func_decor(f'checking {data_file} exists', 'crit')(check_file)(data_file)


# GET OPERATORS DATA
operators = parse_operators_file(operators_file)
logging.info('Current list of Operators:')
for operator in operators:
    logging.info(operator)
logging.info('SUCCEDED: getting Operators data\n')


# GET USER IDS
temp = list()

for operator in operators:
    result = (func_decor
              (f'getting user ids for {operator["operator"][0]}', 'crit')
              (get_users_ids)(fudo_user_url, fudo_proxies, fudo_auth_headers, operator))
    temp.append(result)

operators = temp.copy()
temp.clear()

logging.info('Listing current operators:')
for op in operators:
    logging.info(op)


# SET OPERATOR ROLE FOR OPERATOR
for operator in operators:
    (func_decor
     (f'setting operator role for {operator["operator"][0]}', 'crit')
     (set_operator_role)(fudo_modify_user_url, fudo_proxies, fudo_auth_headers, operator))


# GET SERVER & ACCOUNT IDS
for operator in operators:
    result = (func_decor
              (f'getting servers & accounts ids for {operator["operator"][0]}', 'crit')
              (get_servers_n_accounts_ids)(fudo_account_url, fudo_proxies, fudo_auth_headers, operator))
    temp.append(result)

operators = temp.copy()
temp.clear()

logging.info('Listing current operators:')
for op in operators:
    logging.info(op)


# GET SAFES IDS
for operator in operators:
    result = (func_decor
              (f'getting listener ids for {operator["operator"][0]}', 'crit')
              (get_safes_ids)(fudo_safe_url, fudo_proxies, fudo_auth_headers, operator))
    temp.append(result)

operators = temp.copy()
temp.clear()

logging.info('Listing current operators:')
for op in operators:
    logging.info(op)


# SET GRANTS
urls_for_grant = [
    fudo_grant_access_user_url,
    fudo_grant_access_account_url,
    fudo_grant_access_server_url,
    fudo_grant_access_safe_url
]
for operator in operators:
    (func_decor
     (f'SETTING GRANTS TO {operator["operator"][0]}', 'crit')
     (set_grants)(*urls_for_grant, fudo_proxies, fudo_auth_headers, operator))


# POST-WORK PROCEDURES

# FINISH JOBS
logging.info('#########################')
logging.info('SUCCEEDED: Script job done!')
logging.info(f'Estimated time is: {perf_counter() - start_time_counter}')
logging.info('----------------------------\n')
files_rotate(logs_dir, logs_to_keep)


# # MAIL REPORT
# logging.info('STARTED: sending email report')
# try:
#     send_mail_report(appname, mail_list_admins, smtp_from_addr, smtp_server, smtp_port, app_log_name, login=None,
#                          password=None)
# except Exception as e:
#     logging.warning(f'FAILED: sending email report\n{e}')
# else:
#     logging.info('DONE: sending email report')
