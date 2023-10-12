#!/usr/bin/env python3

# DISABLE SSL WARNINGS
import urllib3
from time import perf_counter

# IMPORT PROJECTS PARTS
from app_scripts.project_helper import files_rotate, check_file, check_create_dir, func_decor

from project_static import appname, data_files, start_date_n_time, logging, logs_dir, logs_to_keep,\
    operators_file, data_file, fudo_auth_url, fudo_headers, fudo_proxies, fudo_auth_creds,\
    fudo_server_url, fudo_account_url, fudo_safe_url, fudo_user_url, fudo_modify_user_url, fudo_grant_access_user_url,\
    fudo_grant_access_safe_url, fudo_grant_access_account_url, fudo_grant_access_server_url

from app_scripts.fudo_functions import get_sessionid, post_data_to_fudo, get_fudo_data, parse_operators_file,\
    modify_fudo_user, set_operators, set_grants_for_operator

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
operators_data = parse_operators_file(operators_file)
logging.info('Current list of Operators:')
for key in operators_data:
    logging.info(f'{key}, {operators_data[key]}')
logging.info('SUCCEDED: getting Operators data\n')


# GET FUDO SESSIONID
sessionid = get_sessionid(fudo_auth_url, fudo_headers, fudo_proxies, fudo_auth_creds)


# GET FUDO USER LIST
fudo_users_list = ((func_decor)('geting Fudo actual User list', 'crit')
                   (get_fudo_data)(fudo_user_url, sessionid, fudo_proxies))
# logging.info('Current list of Users in Fudo:')
# for user in fudo_users_list:
#     logging.info(user)


# SETTING OPERATORS FOR PATCHING ROLE
fudo_operators = set_operators(operators_data, fudo_users_list)
total_users_to_patch = len(fudo_operators)
logging.info('Current list of Operators to patch:')
for user in fudo_operators:
    logging.info(user)


# PATCHING USER TO BE OPERATOR
logging.info('STARTED: patching users to be Operator')
operator_patch_succeeded = []
operator_patch_failed = []
for user in fudo_operators:
    try:
        modify_fudo_user(fudo_modify_user_url, fudo_proxies, sessionid, user['id'])
    except Exception as e:
        operator_patch_failed.append(user)
        logging.exception(f'FAILED: PATCHING USERS TO BE OPERATOR({e})')
    else:
        operator_patch_succeeded.append(user)
logging.info('SUCCEDED: patching users to be Operator\n')


# JOB REPORT: PATCHING USERS RESUME
logging.info('STARTED: JOB REPORT - PATCHING USERS:\n-----')
if len(operator_patch_failed) > 0:
    logging.warning(f'FAILED USERS TOTAL: {len(operator_patch_failed)}/{total_users_to_patch}')
    for server in operator_patch_failed:
        logging.info(server)
if len(operator_patch_succeeded) > 0:
    logging.info(f'\nSUCCEEDED USERS TOTAL: {len(operator_patch_succeeded)}/{total_users_to_patch}')
    for server in operator_patch_succeeded:
        logging.info(server)
logging.info('\nDONE: JOB REPORT - PATCHING USERS\n')


# SET USERS FOR OPERATORS
fudo_users_for_operators = ((func_decor)('setting grants Users for Operators', 'crit')
                            (set_grants_for_operator)('users', fudo_operators, operators_data, fudo_users_list))
total_fudo_users_for_operators = len(fudo_users_for_operators)
logging.info('Current Data of Users for Operators:')
# for data in fudo_users_for_operators:
#     logging.info(data)


# GRANTING OPERATORS ACCESS TO USERS
logging.info('STARTED: granting Operators access to Users')
grant_user_failed = []
grant_user_succeeded = []
for data in fudo_users_for_operators:
    try:
        post_data_to_fudo(fudo_grant_access_user_url, fudo_proxies, sessionid, data)
    except Exception as e:
        grant_user_failed.append(data)
        logging.error(f'\nFAILED: GRANTING USERS({data}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        grant_user_succeeded.append(data)
        logging.info(f'{data} - granted!')
logging.info('DONE: granting Operators access to Users\n')


# JOB REPORT: GRANTING OPERATORS ACCESS TO USERS
logging.info('STARTED: JOB REPORT - GRANTING OPERATORS ACCESS TO USERS:\n-----')
if len(grant_user_failed) > 0:
    logging.warning(f'FAILED GRANTS TO USERS TOTAL: {len(grant_user_failed)}/{total_fudo_users_for_operators}')
    # for data in grant_user_failed:
    #     logging.info(data)
if len(grant_user_succeeded) > 0:
    logging.info(f'\nSUCCEEDED GRANTS TO USERS TOTAL: {len(grant_user_succeeded)}/{total_fudo_users_for_operators}')
    # for data in grant_user_succeeded:
    #     logging.info(data)
logging.info('\nDONE: JOB REPORT - GRANTING OPERATORS ACCESS TO USERS\n')


# GET FUDO SAFE LIST
fudo_safes_list = ((func_decor)('geting Fudo actual Safe list', 'crit')
                   (get_fudo_data)(fudo_safe_url, sessionid, fudo_proxies))
logging.info('Current list of Safes in Fudo:')
# for safe in fudo_safes_list:
#     logging.info(safe)


# SET SAFES FOR OPERATORS
fudo_safes_for_operators = ((func_decor)('setting grants Safes for Operators', 'crit')
                            (set_grants_for_operator)('safes', fudo_operators, operators_data, fudo_safes_list))
total_fudo_safes_for_operators = len(fudo_safes_for_operators)
# logging.info('Current Data of Safes for Operators:')
# for data in fudo_safes_for_operators:
#     logging.info(data)


# GRANTING OPERATORS ACCESS TO SAFES
logging.info('STARTED: granting Operators access to Safes')
grant_safes_failed = []
grant_safes_succeeded = []
for data in fudo_safes_for_operators:
    try:
        post_data_to_fudo(fudo_grant_access_safe_url, fudo_proxies, sessionid, data)
    except Exception as e:
        grant_safes_failed.append(data)
        logging.error(f'\nFAILED: GRANTING SAFES({data}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        grant_safes_succeeded.append(data)
        logging.info(f'{data} - granted!')
logging.info('DONE: granting Operators access to Safes\n')


# JOB REPORT: GRANTING OPERATORS ACCESS TO SAFES
logging.info('STARTED: JOB REPORT - GRANTING OPERATORS ACCESS TO SAFES:\n-----')
if len(grant_safes_failed) > 0:
    logging.warning(f'FAILED GRANTS TO SAFES TOTAL: {len(grant_safes_failed)}/{total_fudo_safes_for_operators}')
    # for data in grant_safes_failed:
    #     logging.info(data)
if len(grant_safes_succeeded) > 0:
    logging.info(f'\nSUCCEEDED GRANTS TO SAFES TOTAL: {len(grant_safes_succeeded)}/{total_fudo_safes_for_operators}')
    # for data in grant_safes_succeeded:
    #     logging.info(data)
logging.info('\nDONE: JOB REPORT - GRANTING OPERATORS ACCESS TO SAFES\n')


# GET FUDO ACCOUNTS LIST
fudo_accounts_list = ((func_decor)('geting Fudo actual Accounts list', 'crit')
                      (get_fudo_data)(fudo_account_url, sessionid, fudo_proxies))
# logging.info('Current list of Accounts in Fudo:')
# for account in fudo_accounts_list:
#     logging.info(account)


# SET ACCOUNTS FOR OPERATORS
fudo_accounts_for_operators = ((func_decor)('setting Accounts for Operators', 'crit')
                               (set_grants_for_operator)('accounts', fudo_operators, operators_data, fudo_accounts_list))
total_fudo_accounts_for_operators = len(fudo_accounts_for_operators)
# logging.info('Current Data of Accounts for Operators:')
# for data in fudo_accounts_for_operators:
#     logging.info(data)


# GRANTING OPERATORS ACCESS TO ACCOUNTS
logging.info('STARTED: granting Operators access to Accounts')
grant_accounts_failed = []
grant_accounts_succeeded = []
for data in fudo_accounts_for_operators:
    try:
        post_data_to_fudo(fudo_grant_access_account_url, fudo_proxies, sessionid, data)
    except Exception as e:
        grant_accounts_failed.append(data)
        logging.error(f'\nFAILED: GRANTING ACCOUNTS({data}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        grant_accounts_succeeded.append(data)
        logging.info(f'{data} - granted!')
logging.info('DONE: granting Operators access to Accounts\n')


# JOB REPORT: GRANTING OPERATORS ACCESS TO ACCOUNTS
logging.info('STARTED: JOB REPORT - GRANTING OPERATORS ACCESS TO ACCOUNTS:\n-----')
if len(grant_accounts_failed) > 0:
    logging.warning(f'FAILED GRANTS TO ACCOUNTS TOTAL: '
                    f'{len(grant_accounts_failed)}/{total_fudo_accounts_for_operators}')
    # for data in grant_accounts_failed:
    #     logging.info(data)
if len(grant_accounts_succeeded) > 0:
    logging.info(f'\nSUCCEEDED GRANTS TO ACCOUNTS TOTAL: '
                 f'{len(grant_accounts_succeeded)}/{total_fudo_accounts_for_operators}')
    # for data in grant_accounts_succeeded:
    #     logging.info(data)
logging.info('\nDONE: JOB REPORT - GRANTING OPERATORS ACCESS TO ACCOUNTS\n')


# GET FUDO SERVERS LIST
fudo_servers_list = ((func_decor)('getting Fudo actual Servers list', 'crit')
                     (get_fudo_data)(fudo_server_url, sessionid, fudo_proxies))
# logging.info('Current list of Servers in Fudo:')
# for server in fudo_servers_list:
#     logging.info(server)


# SET SERVERS FOR OPERATORS
fudo_servers_for_operators = ((func_decor)('setting Servers for Operators', 'crit')
                              (set_grants_for_operator)('servers', fudo_operators, operators_data,
                                                         fudo_accounts_list, fudo_servers_list))
total_fudo_servers_for_operators = len(fudo_servers_for_operators)
# logging.info('Current Data of Accounts for Operators:')
# for data in fudo_servers_for_operators:
#     logging.info(data)


# GRANTING OPERATORS ACCESS TO SERVERS
logging.info('STARTED: granting Operators access to Servers')
grant_servers_failed = []
grant_servers_succeeded = []
for data in fudo_servers_for_operators:
    try:
        post_data_to_fudo(fudo_grant_access_server_url, fudo_proxies, sessionid, data)
    except Exception as e:
        grant_servers_failed.append(data)
        logging.error(f'\nFAILED: GRANTING SERVERS({data}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        grant_servers_succeeded.append(data)
        logging.info(f'{data} - granted!')
logging.info('DONE: granting Operators access to Servers\n')


# JOB REPORT: GRANTING OPERATORS ACCESS TO SERVERS
logging.info('STARTED: JOB REPORT - GRANTING OPERATORS ACCESS TO SERVERS:\n-----')
if len(grant_servers_failed) > 0:
    logging.warning(f'FAILED GRANTS TO SERVERS TOTAL: {len(grant_servers_failed)}/{total_fudo_servers_for_operators}')
    for data in grant_servers_failed:
        logging.info(data)
if len(grant_servers_succeeded) > 0:
    logging.info(f'\nSUCCEEDED GRANTS TO SERVERS TOTAL: '
                 f'{len(grant_servers_succeeded)}/{total_fudo_servers_for_operators}')
    for data in grant_servers_succeeded:
        logging.info(data)
logging.info('\nDONE: JOB REPORT - GRANTING OPERATORS ACCESS TO SERVERS\n')


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
