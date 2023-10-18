#!/usr/bin/env python3

# DISABLE SSL WARNINGS
import urllib3
from time import perf_counter

# IMPORT PROJECTS PARTS
from app_scripts.project_helper import check_file, check_create_dir, func_decor, files_rotate

from project_static import appname, data_files, start_date_n_time, logging, logs_dir, servers_file, data_file, \
    fudo_proxies, fudo_server_url, fudo_pools_url, dcs, acc_pwd, fudo_account_url, fudo_safe_url, \
    fudo_user_url, fudo_listener_url, logs_to_keep, fudo_account_safe_listener_url, fudo_user_to_safe_assignment_url, \
    fudo_pools_server_url

from app_scripts.fudo_functions import post_data_to_fudo, parse_n_set_server_data, get_fudo_data, \
    set_pools_data, parse_n_set_account_data, set_accounts_changers, set_safes, set_user_to_safe_assignment, \
    set_asl_assignment

# FUDO API AUTH
# from project_static import fudo_auth_headers

# DEPRECATED IN FUDO 5.4, USE API AUTH
from project_static import fudo_auth_url, fudo_auth_creds, fudo_headers
from app_scripts.fudo_functions import get_sessionid


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


# GET FUDO SESSIONID
# DEPRECATED IN FUDO 5.4, USE API KEY
sessionid = get_sessionid(fudo_auth_url, fudo_headers, fudo_proxies, fudo_auth_creds)


# PARSE AND SET SERVERS DATA FILE
result_parse_server_data, result_parse_pool_data = parse_n_set_server_data(servers_file)
# logging.info('Server file parsing result is:', )
# for server in result_parse_server_data:
#     logging.info(server)
total_parsed_servers = len(result_parse_server_data)


# CREATING SERVERS
logging.info('STARTED: creating Fudo servers')
servers_failed = []
servers_succeeded = []
for server in result_parse_server_data:
    try:
        # DEPRECATED IN FUDO 5.4, USE API KEY
        post_data_to_fudo(fudo_server_url, fudo_proxies, sessionid, server)
        # post_data_to_fudo(fudo_server_url, fudo_proxies, fudo_headers, server)

    except Exception as e:
        servers_failed.append((server["name"]))
        logging.error(f'\nFAILED: CREATING SERVER({server["name"]}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        servers_succeeded.append((server["name"]))
        logging.info(f'{server["name"]} - created!')
logging.info('DONE: creating Fudo servers\n')


# JOB REPORT: CREATE SERVER RESUME
logging.info('STARTED: JOB REPORT - CREATE SERVER:\n-----')
if len(servers_failed) > 0:
    logging.warning(f'FAILED SERVERS TOTAL: {len(servers_failed)}/{total_parsed_servers}')
    for server in servers_failed:
        logging.info(server)
if len(servers_succeeded) > 0:
    logging.info(f'\nSUCCEEDED SERVERS TOTAL: {len(servers_succeeded)}/{total_parsed_servers}')
    for server in servers_succeeded:
        logging.info(server)
logging.info('\nDONE: JOB REPORT - CREATE SERVER\n')


# GET FUDO SERVERS LIST
# DEPRECATED IN FUDO 5.4, USE API KEY
fudo_servers_list = (func_decor('getting actual FUDO Servers list', 'crit')
                     (get_fudo_data)(fudo_server_url, sessionid, fudo_proxies))
# fudo_servers_list = (func_decor('getting actual FUDO Servers list', 'crit')
#                       (get_fudo_data)(fudo_server_url, fudo_headers, fudo_proxies))

# logging.info('Current list of Servers in Fudo:')
# for server in fudo_servers_list:
#     logging.info(server)


# GET FUDO POOLS LIST
# DEPRECATED IN FUDO 5.4, USE API KEY
fudo_pools_list = (func_decor('getting actual FUDO Pools list', 'crit')
                   (get_fudo_data)(fudo_pools_url, sessionid, fudo_proxies))
# fudo_pools_list = (func_decor('getting actual FUDO Pools list', 'crit')
#                    (get_fudo_data)(fudo_pools_url, fudo_headers, fudo_proxies))

logging.info('Current list of Pools in Fudo:')
for pool in fudo_pools_list:
    logging.info(pool)
logging.info('Moving on\n')


# SET POOLS ASSIGNMENT DATA
result_set_pool_assignment_data = set_pools_data(fudo_servers_list, result_parse_pool_data, fudo_pools_list)
if result_set_pool_assignment_data:
    logging.info('Pools assignment data is:', )
    for data in result_set_pool_assignment_data:
        logging.info(data)
logging.info('Moving on\n')


# CREATING POOL ASSIGNMENT
if not result_set_pool_assignment_data:
    logging.warning('NO SERVERS TO ASSIGN TO POOL, PROBABLY ALREADY ASSIGNED, SKIPPING CREATING POOL ASSIGNMENTS\n')
else:
    logging.info('STARTED: creating Fudo Pool Assignments')
    pool_assignment_failed = []
    pool_assignment_succeeded = []
    for pool_assignment in result_set_pool_assignment_data:
        try:
            # DEPRECATED IN FUDO 5.4, USE API KEY
            post_data_to_fudo(fudo_pools_server_url, fudo_proxies, sessionid, pool_assignment)
            # post_data_to_fudo(fudo_pools_server_url, fudo_proxies, fudo_headers, pool_assignment)

        except Exception as e:
            pool_assignment_failed.append((pool_assignment["server_id"]))
            logging.error(f'\nFAILED: CREATING POOL ASSIGNMENTS({pool_assignment["server_id"]}), '
                          f'CHECK STATUS CODE/ERROR({e})\n')
        else:
            pool_assignment_succeeded.append((pool_assignment["server_id"]))
            logging.info(f'{pool_assignment["server_id"]} - created!')
    logging.info('DONE: creating Fudo Pool Assignments\n')
    # JOB REPORT: CREATE POOL ASSIGNMENT RESUME
    logging.info('STARTED: JOB REPORT - CREATE POOL ASSIGNMENTS:\n-----')
    if len(pool_assignment_failed) > 0:
        logging.warning(f'FAILED POOL ASSIGNMENTS TOTAL: {len(pool_assignment_failed)}/{total_parsed_servers}')
        for pool_assignment in pool_assignment_failed:
            logging.info(pool_assignment)
    if len(pool_assignment_succeeded) > 0:
        logging.info(f'\nSUCCEEDED POOL ASSIGNMENTS TOTAL: {len(pool_assignment_succeeded)}/{total_parsed_servers}')
        for pool_assignment in pool_assignment_succeeded:
            logging.info(pool_assignment)
    logging.info('\nDONE: JOB REPORT - CREATE POOL ASSIGNMENTS\n')


# PARSE SERVERS DATA FILE FOR ACCOUNT CHANGERS
result_parse_account_data = (func_decor('parsing server data for Account Changers', 'crit')
                             (parse_n_set_account_data)(servers_file, fudo_servers_list))
# logging.info('STARTED: parsing server data for Account Changers')
# try:
#     result_parse_account_data = parse_n_set_account_data(servers_file, fudo_servers_list)
# except Exception as e:
#     logging.exception(f'FAILED: PARSE SERVERS FILE FOR ACCOUNT CHANGERS, exiting\n{e}')
#     exit()
# else:
logging.info('Accounts parsing result is:')
for account in result_parse_account_data:
    logging.info(account)
total_parsed_accounts = len(result_parse_account_data)
logging.info('Moving on\n')


# SET ACCOUNTS FOR CHANGER
result_set_accounts_changers = set_accounts_changers(fudo_servers_list, result_parse_account_data, dcs, acc_pwd)
# logging.info('Accounts for changers are:')
# for account in result_set_accounts_changers:
#     logging.info(account)


# CREATE ACCOUNTS FOR CHANGERS
logging.info('STARTED: creating Fudo Accounts for Changers')
accounts_changer_failed = []
accounts_changer_succeeded = []
for account in result_set_accounts_changers:
    try:
        # DEPRECATED IN FUDO 5.4, USE API KEY
        post_data_to_fudo(fudo_account_url, fudo_proxies, sessionid, account)
        # post_data_to_fudo(fudo_account_url, fudo_proxies, fudo_headers, account)

    except Exception as e:
        accounts_changer_failed.append((account["name"]))
        logging.error(f'\nFAILED: CREATING account({account["name"]}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        accounts_changer_succeeded.append((account["name"]))
        logging.info(f'{account["name"]} - created!')
logging.info('DONE: creating Fudo Accounts for Changers\n')


# JOB REPORT: CREATE ACCOUNT CHANGER
logging.info('STARTED: JOB REPORT - CREATE ACCOUNT CHANGER:\n-----')
if len(accounts_changer_failed) > 0:
    logging.warning(f'FAILED ACCOUNTS CHANGER TOTAL: '
                    f'{len(accounts_changer_failed)}/{len(result_set_accounts_changers)}')
    for account in accounts_changer_failed:
        logging.info(account)
if len(accounts_changer_succeeded) > 0:
    logging.info(f'\nSUCCEEDED ACCOUNTS CHANGER TOTAL: '
                 f'{len(accounts_changer_succeeded)}/{len(result_set_accounts_changers)}')
    for account in accounts_changer_succeeded:
        logging.info(account)
logging.info('\nDONE: JOB REPORT - CREATE ACCOUNT CHANGER\n')


# GET FUDO ACCOUNT LIST
# DEPRECATED IN FUDO 5.4, USE API KEY
fudo_accounts_list = (func_decor('geting Fudo actual Accounts list', 'crit')
                      (get_fudo_data)(fudo_account_url, sessionid, fudo_proxies))
# fudo_accounts_list = ((func_decor)('geting Fudo actual Accounts list', 'crit')
#                       (get_fudo_data)(fudo_account_url, fudo_headers, fudo_proxies))

# logging.info('Current list of Accounts in Fudo:')
# for account in fudo_accounts_list:
#     logging.info(account)


# PARSE SERVERS DATA FILE FOR ACCOUNTS(INCLUDING ACCOUNT CHANGERS)
result_parse_account_data = (func_decor('parsing server data for Accounts incl. Changers', 'crit')
                             (parse_n_set_account_data)(servers_file, fudo_servers_list, fudo_accounts_list, dcs))
# logging.info('Accounts parsing result is:')
# for account in result_parse_account_data:
#     logging.info(account)
total_parsed_accounts = len(result_parse_account_data)


# CREATING ACCOUNTS
logging.info('STARTED: creating Fudo Accounts')
accounts_failed = []
accounts_succeeded = []
for account in result_parse_account_data:
    try:
        # DEPRECATED IN FUDO 5.4, USE API KEY
        post_data_to_fudo(fudo_account_url, fudo_proxies, sessionid, account)
        # post_data_to_fudo(fudo_account_url, fudo_proxies, fudo_headers, account)

    except Exception as e:
        accounts_failed.append((account["name"]))
        logging.error(f'\nFAILED: CREATING account({account["name"]}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        accounts_succeeded.append((account["name"]))
        logging.info(f'{account["name"]} - created!')
logging.info('DONE: creating Fudo accounts\n')

# JOB REPORT: CREATE ACCOUNT
logging.info('STARTED: JOB REPORT - CREATE ACCOUNT:\n-----')
if len(accounts_failed) > 0:
    logging.warning(f'FAILED ACCOUNTS TOTAL: {len(accounts_failed)}/{total_parsed_accounts}')
    for account in accounts_failed:
        logging.info(account)
if len(accounts_succeeded) > 0:
    logging.info(f'\nSUCCEEDED ACCOUNTS TOTAL: {len(accounts_succeeded)}/{total_parsed_accounts}')
    for account in accounts_succeeded:
        logging.info(account)
logging.info('\nDONE: JOB REPORT - CREATE ACCOUNT\n')


# GET FUDO ACCOUNT LIST
# DEPRECATED IN FUDO 5.4, USE API KEY
fudo_accounts_list = (func_decor('geting Fudo actual Accounts list', 'crit')
                      (get_fudo_data)(fudo_account_url, sessionid, fudo_proxies))
# fudo_accounts_list = ((func_decor)('geting Fudo actual Accounts list', 'crit')
#                       (get_fudo_data)(fudo_account_url, fudo_headers, fudo_proxies))

# logging.info('Current list of Accounts in Fudo:')
# for account in fudo_accounts_list:
#     logging.info(account)


# SET FUDO SAFES(BASED ON FUDO ACCOUNTS LIST)
result_set_safes = set_safes(result_set_accounts_changers)
# logging.info('Safes settings are:')
# for safe in result_set_safes:
#     logging.info(safe)
total_set_safes = len(result_set_safes)


# CREATING SAFES
logging.info('STARTED: creating Fudo Safes')
safes_failed = []
safes_succeeded = []
for safe in result_set_safes:
    try:
        # DEPRECATED IN FUDO 5.4, USE API KEY
        post_data_to_fudo(fudo_safe_url, fudo_proxies, sessionid, safe)
        # post_data_to_fudo(fudo_safe_url, fudo_proxies, fudo_headers, safe)

    except Exception as e:
        safes_failed.append((safe["name"]))
        logging.error(f'\nFAILED: CREATING Safe({safe["name"]}), CHECK STATUS CODE/ERROR({e})\n')
    else:
        safes_succeeded.append((safe["name"]))
        logging.info(f'{safe["name"]} - created!')
logging.info('DONE: creating Fudo Safes\n')


# JOB REPORT: CREATE SAFE RESUME
logging.info('STARTED: JOB REPORT - CREATE SAFE:\n-----')
if len(safes_failed) > 0:
    logging.warning(f'FAILED SAFES TOTAL: {len(safes_failed)}/{total_set_safes}')
    for safe in safes_failed:
        logging.info(safe)
if len(safes_succeeded) > 0:
    logging.info(f'\nSUCCEEDED SAFES TOTAL: {len(safes_succeeded)}/{total_set_safes}')
    for safe in safes_succeeded:
        logging.info(safe)
logging.info('\nDONE: JOB REPORT - CREATE SAFE\n')


# GET FUDO SAFE LIST
# DEPRECATED IN FUDO 5.4, USE API KEY
fudo_safes_list = (func_decor('geting Fudo actual Safe list', 'crit')
                   (get_fudo_data)(fudo_safe_url, sessionid, fudo_proxies))
# fudo_safes_list = ((func_decor)('geting Fudo actual Safe list', 'crit')
#                    (get_fudo_data)(fudo_safe_url, fudo_headers, fudo_proxies))

# logging.info('Current list of Safes in Fudo:')
# for safe in fudo_safes_list:
#     logging.info(safe)


# GET FUDO USER LIST
# DEPRECATED IN FUDO 5.4, USE API KEY
fudo_users_list = (func_decor('geting Fudo actual User list', 'crit')
                   (get_fudo_data)(fudo_user_url, sessionid, fudo_proxies))
# fudo_users_list = ((func_decor)('geting Fudo actual User list', 'crit')
#                    (get_fudo_data)(fudo_user_url, fudo_headers, fudo_proxies))

# logging.info('Current list of Users in Fudo:')
# for user in fudo_users_list:
#     logging.info(user)


# SET FUDO USERS ASSIGNMENT TO SAFES
result_set_user_to_safe_assignment = sorted(set_user_to_safe_assignment(fudo_safes_list, fudo_users_list,
                                                                        result_parse_account_data))
logging.info('Assinments are:')
for assinment in result_set_user_to_safe_assignment:
    logging.info(assinment)
total_set_user_to_safe_assignment = len(result_set_user_to_safe_assignment)


# CREATE USERS TO SAFE ASSIGNMENT
logging.info('STARTED: creating Users to Safe Assignments')
user_to_safe_assignments_failed = []
user_to_safe_assignments_succeeded = []
for assignment in result_set_user_to_safe_assignment:
    try:
        # DEPRECATED IN FUDO 5.4, USE API KEY
        post_data_to_fudo(fudo_user_to_safe_assignment_url, fudo_proxies, sessionid, assignment[1])
        # post_data_to_fudo(fudo_user_to_safe_assignment_url, fudo_proxies, fudo_headers, assignment[1])

    except Exception as e:
        user_to_safe_assignments_failed.append((assignment[0]))
        logging.error(f'\nFAILED: CREATING USER TO SAFE ASSIGNMENT({assignment[0]}), '
                      f'CHECK STATUS CODE/ERROR({e})\n')
    else:
        user_to_safe_assignments_succeeded.append((assignment[0]))
        logging.info(f'{assignment[0]} - created!')
logging.info('DONE: creating Users to Safe Assignments\n')


# JOB REPORT: CREATE USERS TO SAFE ASSIGNMENT
logging.info('STARTED: JOB REPORT - CREATING USER TO SAFE ASSIGNMENT:\n-----')
if len(user_to_safe_assignments_failed) > 0:
    logging.warning(f'FAILED USERS TO SAFE ASSIGNMENTS TOTAL: {len(user_to_safe_assignments_failed)}/'
                    f'{total_set_user_to_safe_assignment}')
    for assinment in user_to_safe_assignments_failed:
        logging.info(assinment)
if len(user_to_safe_assignments_succeeded) > 0:
    logging.info(f'\nSUCCEEDED USERS TO SAFE ASSIGNMENTS TOTAL: {len(user_to_safe_assignments_succeeded)}/'
                 f'{total_set_user_to_safe_assignment}')
    for assinment in user_to_safe_assignments_succeeded:
        logging.info(assinment)
logging.info('\nDONE: JOB - CREATING USER TO SAFE ASSIGNMENT\n')


# GET FUDO LISTENERS LIST
# DEPRECATED IN FUDO 5.4, USE API KEY
fudo_listeners_list = (func_decor('geting Fudo actual Listeners list', 'crit')
                       (get_fudo_data)(fudo_listener_url, sessionid, fudo_proxies))
# fudo_listeners_list = ((func_decor)('geting Fudo actual Listeners list', 'crit')
#                        (get_fudo_data)(fudo_listener_url, fudo_headers, fudo_proxies))

logging.info('Current list of Listener in Fudo:')
for listener in fudo_listeners_list:
    logging.info(listener)


# SET FUDO ACCOUNT-SAFE-LISTENER ASSIGNMENT
result_set_asl_assignment = set_asl_assignment(fudo_accounts_list, fudo_safes_list, fudo_listeners_list,
                                               result_parse_account_data)
# logging.info('Assinments are:')
# for assinment in result_set_asl_assignment:
#     logging.info(assinment)
total_set_asl_assignment = len(result_set_asl_assignment)


# CREATE ACCOUNT-SAFE-LISTENER ASSIGNMENT
logging.info('STARTED: creating A-S-L Assignments')
asl_assignments_failed = []
asl_assignments_succeeded = []
for assignment in result_set_asl_assignment:
    try:
        # DEPRECATED IN FUDO 5.4, USE API KEY
        post_data_to_fudo(fudo_account_safe_listener_url, fudo_proxies, sessionid, assignment[1])
        # post_data_to_fudo(fudo_account_safe_listener_url, fudo_proxies, fudo_headers, assignment[1])

    except Exception as e:
        asl_assignments_failed.append((assignment[0]))
        logging.error(f'\nFAILED: CREATING A-S-L ASSIGNMENT({assignment}), '
                      f'CHECK STATUS CODE/ERROR({e})\n')
    else:
        asl_assignments_succeeded.append((assignment[0]))
        logging.info(f'A-S-L {assignment[0]} - created!\n')
logging.info('DONE: creating A-S-L Assignments\n')


# JOB REPORT: CREATE ACCOUNT-SAFE-LISTENER ASSIGNMENT
logging.info('STARTED: JOB REPORT - CREATING ACCOUNT-SAFE-LISTENER ASSIGNMENT:\n-----')
if len(asl_assignments_failed) > 0:
    logging.warning(f'FAILED ACCOUNT-SAFE-LISTENER ASSIGNMENTS TOTAL: {len(asl_assignments_failed)}/'
                    f'{total_set_asl_assignment}')
    for assinment in asl_assignments_failed:
        logging.info(assinment)
if len(safes_succeeded) > 0:
    logging.info(f'\nSUCCEEDED ACCOUNT-SAFE-LISTENER TOTAL: {len(asl_assignments_succeeded)}/'
                 f'{total_set_asl_assignment}')
    for assinment in asl_assignments_succeeded:
        logging.info(assinment)
logging.info('\nDONE: JOB REPORT - ACCOUNT-SAFE-LISTENER ASSIGNMENT\n')


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
