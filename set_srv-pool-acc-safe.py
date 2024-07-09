#!/usr/bin/env python3

# DISABLE SSL WARNINGS
import urllib3
from time import perf_counter

# IMPORT PROJECTS PARTS
from app_scripts.project_helper import check_file, check_create_dir, func_decor, files_rotate

from project_static import (
    appname,
    data_files,
    start_date_n_time,
    logging,
    logs_dir,
    logs_to_keep,
    servers_file,
    data_file,
    fudo_proxies,
    fudo_server_url,
    fudo_pools_url,
    fudo_safe_url,
    fudo_user_url,
    fudo_listener_url,
    fudo_account_url,
    fudo_user_to_safe_assignment_url,
    fudo_account_safe_listener_url,
    acc_pwd,
    dcs
)

from app_scripts.fudo_functions import (
    post_data_to_fudo,
    parse_n_set_server_data,
    enrich_data,
    create_fudo_safe,
    assign_server_to_pool,
    create_accounts,
    assign_data_to_safe
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
func_decor(f'checking {servers_file} exists', 'crit')(check_file)(servers_file)
func_decor(f'checking {data_file} exists', 'crit')(check_file)(data_file)


# PARSE AND SET SERVERS DATA FILE
parsed_data = parse_n_set_server_data(servers_file)
logging.info('Server file parsing result is:', )

for server in parsed_data:
    logging.info(server)

total_parsed_servers = len(parsed_data)


# CREATING SERVERS
logging.info('STARTED: creating Fudo servers\n')
temp_failed = []
temp_succeeded = []
for obj in parsed_data:
    server = obj['server_data']
    try:
        post_data_to_fudo(fudo_server_url, fudo_proxies, fudo_auth_headers, server)
    except Exception as e:
        temp_failed.append((server["name"]))
        logging.error(f'\nFAILED: CREATING SERVER({server["name"]}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        temp_succeeded.append((server["name"]))
        logging.info(f'{server["name"]} - created!')
logging.info('DONE: creating Fudo servers\n')


# JOB REPORT: CREATE SERVER RESUME
logging.info('STARTED: JOB REPORT - CREATE SERVER:\n-----')
if len(temp_failed) > 0:
    logging.warning(f'FAILED SERVERS TOTAL: {len(temp_failed)}/{total_parsed_servers}')
    for server in temp_failed:
        logging.info(server)
if len(temp_succeeded) > 0:
    logging.info(f'\nSUCCEEDED SERVERS TOTAL: {len(temp_succeeded)}/{total_parsed_servers}')
    for server in temp_succeeded:
        logging.info(server)
logging.info('\nDONE: JOB REPORT - CREATE SERVER\n')

temp_succeeded.clear()
temp_failed.clear()


# CREATING SAFES

logging.info('STARTED: creating Fudo Safes\n')
# get all distinct users for safes from parsed data
users_for_safes = set(user['name'] for obj in parsed_data for user in obj['user_data'])
total_set_safes = len(users_for_safes)

for user in users_for_safes:
    logging.info(f'STARTED: creating safe for {user}')
    try:
        create_fudo_safe(
            fudo_safe_url,
            fudo_user_url,
            fudo_user_to_safe_assignment_url,
            fudo_proxies,
            fudo_auth_headers,
            user
        )
    except Exception as e:
        temp_failed.append(user)
        logging.error(f'\nFAILED: Creating safe for {user}:\n{e}')
    else:
        temp_succeeded.append(user)
        logging.info(f'{user} - created!')
logging.info('DONE: creating Fudo Safes\n')

users_for_safes.clear()

# JOB REPORT: CREATE SAFE RESUME
logging.info('STARTED: JOB REPORT - CREATE SAFE:\n-----')
if len(temp_failed) > 0:
    logging.warning(f'FAILED SAFES TOTAL: {len(temp_failed)}/{total_set_safes}')
    for safe in temp_failed:
        logging.info(safe)
if len(temp_succeeded) > 0:
    logging.info(f'\nSUCCEEDED SAFES TOTAL: {len(temp_succeeded)}/{total_set_safes}')
    for safe in temp_succeeded:
        logging.info(safe)
logging.info('\nDONE: JOB REPORT - CREATE SAFE\n')


# ENRICH PARSED DATA
temp = []
enrich_urls = [fudo_server_url, fudo_listener_url, fudo_pools_url, fudo_user_url, fudo_safe_url]

for obj in parsed_data:
    temp.append(enrich_data(*enrich_urls, fudo_auth_headers, fudo_proxies, obj))

logging.info('ENRICHED DATA:\n')
for data in temp:
    logging.info(f'{data}\n')

parsed_data = temp.copy()
temp.clear()


# ASSIGN SERVER TO POOL
temp_succeeded.clear()
temp_failed.clear()

logging.info('STARTED: assigning Server to Pool(ASP)\n')
for obj in parsed_data:
    try:
        assign_server_to_pool(fudo_pools_url, fudo_proxies, fudo_auth_headers, obj)
    except Exception as e:
        temp_failed.append((obj['server_data']['name']))
        logging.error(f'\nFAILED: CREATING ASP({obj["server_data"]["name"]}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        temp_succeeded.append((obj['server_data']['name']))
        logging.info(f'{obj["server_data"]["name"]} - created!')
logging.info('DONE: creating ASP\n')


# JOB REPORT: CREATE SERVER RESUME
logging.info('STARTED: JOB REPORT - CREATE ASP:\n-----')
if len(temp_failed) > 0:
    logging.warning(f'FAILED ASP TOTAL: {len(temp_failed)}/{total_parsed_servers}')
    for server in temp_failed:
        logging.info(server)

if len(temp_succeeded) > 0:
    logging.info(f'\nSUCCEEDED ASP TOTAL: {len(temp_succeeded)}/{total_parsed_servers}')
    for server in temp_succeeded:
        logging.info(server)

logging.info('\nDONE: JOB REPORT - CREATE ASP\n')

temp_succeeded.clear()
temp_failed.clear()

# CREATE ACCOUNTS
for obj in parsed_data:
    logging.info('STARTED: CREATING ACCOUNTS\n')
    try:
        logging.info(f'STARTED: creating Accounts for {obj["user_data"]}')
        result = create_accounts(
            fudo_account_url,
            fudo_server_url,
            fudo_proxies,
            fudo_auth_headers,
            obj,
            acc_pwd,
            dcs
        )
    except Exception as e:
        logging.error(f'FAILED: creating Accounts for {obj["user_data"]}:\n{e}\n')
    else:
        temp.append(result)
        logging.info(f'DONE: CREATING ACCOUNTS\n')

parsed_data = temp.copy()
temp.clear()

for obj in parsed_data:
    logging.info(f'{obj["user_data"]}\n')


# CREATE DATA TO SAFE ASSIGNMENT
for obj in parsed_data:
    assign_data_to_safe(
        fudo_account_safe_listener_url,
        fudo_proxies,
        fudo_auth_headers,
        obj
    )


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
