import requests
import csv
import re
from app_scripts.project_helper import func_decor
from project_static import fudo_bind_ip


# FUNCTION: GET SESSIONID FOR REQUESTS
@func_decor('getting Fudo sessionID', 'crit')
def get_sessionid(url, headers, proxies, ses_data):
    response = requests.post(url, headers=headers, proxies=proxies, json=ses_data, verify=False)
    if response.status_code == 200:
        return {'Authorization': response.json()['sessionid']}
    else:
        raise Exception(response.status_code)


# FUNCTION: PARSE AND PREPARE SERVERS DATA FROM INPUT CSV
@func_decor('parsing and setting server data', 'crit')
def parse_n_set_server_data(input_file):
    with open(input_file, 'r') as in_file:
        file_data = csv.reader(in_file)
        result = []
        pool_result = []
        protocols = ['ssh', 'rdp', 'http']
        for row in file_data:
            server_ip = row[3].strip()
            if not server_ip:
                raise Exception(f'IP COLUMN IS EMPTY: {row}')
            if not row[4]:
                raise Exception(f'EMPTY SYSTEM TYPE COLUMN! CHECK {server_ip}')
            for ind, proto_data in enumerate(row[5:]):
                server_data = dict()
                server_pool_data = dict()

                if len(proto_data) == 0:
                    continue
                else:
                    server_data['description'] = f'{row[1]}; {row[2]}'
                    server_data['address'] = server_ip
                    server_data['bind_ip'] = fudo_bind_ip

                    # _FILLED_ COLUMN 6 IN _ORIGINAL_ CSV = SSH, COL. 7 = RDP, COL 8 = HTTP
                    if ind == 0:  # SSHs
                        server_data['protocol'] = protocols[0]
                        server_data['port'] = 22
                    elif ind == 1:  # RDP
                        server_data['protocol'] = protocols[1]
                        server_data['port'] = 3389
                        server_data['rdp_nla_enabled'] = True
                        server_data['tls_enabled'] = True
                    elif ind == 2:  # HTTP
                        server_data['protocol'] = protocols[2]
                        server_data['port'] = 443
                        server_data['http_authentication'] = True
                        server_data['http_password_element'] = '[id="password"]'
                        server_data['http_username_element'] = '[id="username"]'
                        server_data['http_signon_realm'] = f'https://{server_data["address"]}'

                    server_data['name'] = f'API_S_{row[0]}_{server_data["protocol"].upper()}_{server_ip}'

                    result.append(server_data)

                    # DATA FOR POOL ASSIGNMENT
                    server_pool_data['name'] = f'API_S_{row[0]}_{server_data["protocol"].upper()}_{server_ip}'
                    server_pool_data['pool_mark'] = row[4]  # MARK FOR FUDO POOL ASSIGNMENT
                    server_pool_data['address'] = server_ip
                    server_pool_data['scope'] = row[0]

                    pool_result.append(server_pool_data)

    if not result:
        raise Exception('EMPTY RESULT OF PARSING SERVERS!')
    return result, pool_result


# FUNCTION: PARSE AND PREPARE ACCOUNTS DATA FROM INPUT CSV
def parse_n_set_account_data(servers_file, fudo_servers, fudo_accounts_list=None, dcs=None):
    # Check if there is changer accounts created
    account_changers = None
    zones = None
    if fudo_accounts_list:
        if not dcs:
            raise Exception('NO DCS PASSED TO FUNCTION, CAN\'t CREATE NORMAL ACCOUNTS')
        else:
            zones = [key for key in dcs.keys()]
        account_changers = list(filter(lambda x: re.findall('.*A_CHANGER-.*', x[0]), fudo_accounts_list))

    with open(servers_file, 'r') as in_file:
        file_data = csv.reader(in_file)
        result = []
        protocols = ['ssh', 'rdp', 'http']

        for row in file_data:
            """
            Example of row:
                ['SCOPE', 'Windows', 'Descr', '10.*.*.* ', 'SW', '', 'USER1, USER2']
            """
            server_ip = row[3].strip()
            if not server_ip:
                raise Exception(f'IP COLUMN IS EMPTY: {row}')
            for ind, proto_data in enumerate(row[5:]):
                if len(proto_data) == 0:
                    continue
                else:
                    """Check if there is a server in Fudo servers list with ip and proto"""
                    current_server = list(filter(lambda x: x['ip'] == server_ip, fudo_servers))
                    if len(current_server) == 0:
                        continue

                    users_list = [user.upper().strip() for user in proto_data.split(',')]

                    for user in users_list:
                        account_data = dict()
                        account_data['type'] = 'regular'
                        account_data['dump_mode'] = 'all'
                        account_data['login'] = f'PAM-{user}'

                        # SEARCH FOR ACCOUNT CHANGER'S ID FOR USER
                        # USE SCOPE FROM YOUR SCOPES FILE
                        if fudo_accounts_list:
                            if account_changers:
                                if row[0].upper() == 'SCOPE1':
                                    scope = zones[0]
                                elif row[0].upper() == 'SCOPE3' or row[0].upper() == 'SCOPE2':
                                    scope = zones[1]
                                elif row[0].upper() == 'SCOPE3' or row[0].upper() == 'SCOPE4':
                                    scope = zones[2]
                                elif row[0].upper() == 'SCOPE5':
                                    scope = zones[3]
                                else:
                                    raise Exception(f'NOT CORRECT SCOPE({row[0]},{server_ip})')

                            changer = list(
                                filter(
                                    lambda x: re.findall('.+-(.+)_.*$', x[0])[0] == scope and
                                              re.findall('.*PAM-(.+)$', x[0])[0] == user, account_changers
                                )
                            )
                            if changer:
                                account_data['method'] = 'account'
                                account_data['account_id'] = changer[0][1]
                            else:
                                continue  # NO CHANGER ID FOUND, SKIP USER

                        account_data['category'] = 'privileged'
                        account_data['password_change_policy_id'] = 1  # 1 for Static

                        if ind == 0:  # SSH
                            protocol = protocols[0]
                            current_server_ssh = list(filter(lambda x: x['protocol'] == protocol, current_server))
                            if current_server_ssh:
                                account_data['server_id'] = current_server_ssh[0]['id']
                            else:
                                continue

                        elif ind == 1:  # RDP
                            protocol = protocols[1]
                            current_server_rdp = list(filter(lambda x: x['protocol'] == protocol, current_server))
                            if current_server_rdp:
                                account_data['server_id'] = current_server_rdp[0]['id']
                            else:
                                continue
                            account_data['ocr_enabled'] = True
                            account_data['ocr_lang'] = 'eng+rus'

                        elif ind == 2:  # HTTP
                            protocol = protocols[2]
                            current_server_http = list(filter(lambda x: x['protocol'] == protocol, current_server))
                            if current_server_http:
                                account_data['server_id'] = current_server_http[0]['id']
                            else:
                                continue
                            account_data['ocr_enabled'] = True
                            account_data['ocr_lang'] = 'eng+rus'

                        account_data['name'] = f'A_PAM-{user}_{protocol.upper()}_{server_ip}'
                        result.append(account_data)

    if not result:
        raise Exception('EMPTY RESULT OF PARSING ACCOUNTS!')
    return result


# FUNCTION: GETTING FUDO DATA
def get_fudo_data(url, headers, proxies):
    response = requests.get(url, headers=headers, proxies=proxies, verify=False)
    if response.status_code == 200:
        if 'server' in response.json():  # to get server data
            return [
                {'name': i['name'],
                 'ip': i['address'].strip(),
                 'id': i['id'],
                 'protocol': i['protocol'],
                 'scope': re.findall('S_(.+)_.+_.+', i['name'])[0]
                 }
                for i in response.json()['server']]
        elif 'account' in response.json():  # to get account data
            return [(i['name'], i['id']) for i in response.json()['account']]
        elif 'user' in response.json():  # to get user data
            return [(i['name'], i['id']) for i in response.json()['user']]
        elif 'safe' in response.json():  # to get safe data
            return [(i['name'], i['id']) for i in response.json()['safe']]
        elif 'listener' in response.json():  # to get listener data
            return [(i['name'], i['id']) for i in response.json()['listener']]
        elif 'pool' in response.json():  # to get pool data
            return [
                {
                    'name': i['name'],
                    'id': i['id'],
                    'mark': re.findall('P_.+_.+_(.+)$', i['name'])[0],
                    'scope': re.findall('P_(.+)_.+_.+$', i['name'])[0],
                    'protocol': re.findall('P_.+_(.+)_.+$', i['name'])[0]
                } for i in response.json()['pool']]
        else:
            raise Exception('NEITHER SERVER NOR ACCOUNT RESPONSE')
    else:
        raise Exception(response.status_code)


# FUNCTION: SEND DATA TO FUDO
def post_data_to_fudo(url, proxies, auth_header, post_data):
    response = requests.post(url, proxies=proxies, headers=auth_header, json=post_data, verify=False)
    if response.status_code not in (200, 201):
        raise Exception(f'{response.status_code}\n{response.text}')


# FUNCTION: SET DATA FOR POOLS
@func_decor('setting FUDO Pools assignment data')
def set_pools_data(fudo_servers, parsed_servers, pool_list):
    pass
    """
    SERVER(PARSED): 
    {'name': 'API_S_SCOPE_SSH_10.*.*.*', 'pool_mark': 'SM', 'address': '10.*.*.*', 'scope': 'SCOPE'}
    
    SERVER(FILTERED): 
    {'name': 'API_S_SCOPE_SSH_10.*.*.*', 'ip': '10.*.*.*', 'id': '1774418253183977390', 'protocol': 'ssh', 
        'scope': 'SCOPE'}
    
    POOL MARKS: pool_marks = ('HV', 'ND', 'SC', 'SM', 'SN', 'SW')
          **HV** - HyperVisors
          **ND** - VA NetworkDevices
          **SC** - StorageControl
          **SM** - ServerManager(iLOM, iRMC)
          **SN** - ServerNix(Linux, Solaris)
          **SW** - ServerWin
    
    POOLS(CREATED)
    {'name': 'P_SCOPE_SSH_SC', 'id': '1774418253183975440', 'mark': 'SC', 'scope': 'SCOPE', 'protocol': 'SSH'}
    {'name': 'P_SCOPE_SSH_SC', 'id': '1774418253183975441', 'mark': 'SC', 'scope': 'SCOPE', 'protocol': 'SSH'}
    """
    result = []
    # EXCLUDE ALL SERVERS EXCEPT NEWLY CREATED(API_S_*)
    filtered_servers = list(filter(lambda x: not x['name'].startswith('S_'), fudo_servers))
    if len(filtered_servers) == 0:
        raise Exception('NO SERVERS TO ASSIGN TO POOL, PROBABLY ALREADY ASSIGNED!')

    for server in filtered_servers:
        for parsed in parsed_servers:
            if server['name'] == parsed['name']:
                if server['protocol'] == 'http':
                    pool_result = list(
                        filter(lambda x: x['scope'] == parsed['scope'] and x['protocol'] == 'HTTP', pool_list))[0]
                    data = {
                        'pool_id': pool_result['id'],
                        'server_id': server['id']
                    }
                else:
                    pool_result = list(filter(lambda x: x['mark'] == parsed['pool_mark']
                                                        and x['scope'] == parsed['scope'], pool_list))[0]
                    data = {
                        'pool_id': pool_result['id'],
                        'server_id': server['id']
                    }
                result.append(data)
                continue
    if not result:
        raise Exception('EMPTY RESULT OF SETTING POOL ASSIGNMENT! Probably already assigned!')
    return result


# FUNCTION: SET ACCOUNTS FOR CHANGERS
@func_decor('setting Accounts for Changers', 'crit')
def set_accounts_changers(fudo_servers, parsed_accounts, dcs, acc_pwd):
    # Adding Account for Changers Must be created prior
    result = []
    zones = [key for key in dcs.keys()]
    servers_changers = list(filter(lambda x: re.findall('^S_CHANGER-', x['name']), fudo_servers))
    accounts_for_changer = sorted(list(set(i['login'] for i in parsed_accounts)))
    if len(servers_changers) > 0:
        if len(accounts_for_changer) > 0:
            for server_changer in servers_changers:
                for account in accounts_for_changer:
                    account_data = dict()
                    if server_changer['ip'] == dcs[zones[0]][1]:
                        zone = zones[0]
                        account_data['domain'] = dcs[zones[0]][0]
                    elif server_changer['ip'] == dcs[zones[1]][1]:
                        zone = zones[1]
                        account_data['domain'] = dcs[zones[1]][0]
                    elif server_changer['ip'] == dcs[zones[2]][1]:
                        zone = zones[2]
                        account_data['domain'] = dcs[zones[2]][0]
                    elif server_changer['ip'] == dcs[zones[3]][1]:
                        zone = zones[3]
                        account_data['domain'] = dcs[zones[3]][0]
                    else:
                        raise Exception(f'NOT CORRECT DC ZONE/IP, CHECK({server_changer["ip"]})')
                    account_data['name'] = f'A_CHANGER-{zone}_{account}'
                    account_data['server_id'] = server_changer['id']
                    account_data['type'] = 'regular'
                    account_data['dump_mode'] = 'all'
                    account_data['method'] = 'password'
                    account_data['login'] = account
                    account_data['secret'] = acc_pwd
                    account_data['category'] = 'privileged'
                    account_data['password_change_policy_id'] = 1  # 1 for Static
                    result.append(account_data)
            if not result:
                raise Exception('EMPTY RESULT OF ACCOUNT CHANGERS!')
            return result
        else:
            raise Exception('ACCOUNTS FOR CHANGERS NOT FOUND')
    else:
        raise Exception('CHANGERS SERVERS NOT FOUND')


# FUNCTION: SET SAFES
@func_decor('setting FUDO Safes', 'crit')
def set_safes(changers_accounts):
    result = []
    accounts_for_safes = set([re.findall('.+_PAM-(.+)$', i['name'])[0] for i in changers_accounts])
    for account in accounts_for_safes:
        safe_data = {
            "name": f'SAFE-{account}',
            "inactivity_limit": 30,
            # "time_limit": 90, # unlimited
            "rdp_resolution": "1920x1080",
            "vnc_clipcli": False,
            "vnc_clipsrv": False
        }
        result.append(safe_data)
    if not result:
        raise Exception('EMPTY RESULT OF SAFES!')
    else:
        return result


# FUNCTION: SET USERS TO SAFE ASSIGNMENT
@func_decor('setting Users to Safes assignments', 'crit')
def set_user_to_safe_assignment(fudo_safes_list, fudo_users_list, parsed_users):
    user_parsed = set([re.findall('PAM-(.+)', i['login'])[0] for i in parsed_users])
    if not user_parsed:
        raise Exception('NO USERS FOR SAFE ASSIGNMENT FOUND!')
    result = []
    for user in fudo_users_list:
        assignment_data = dict()
        for safe in fudo_safes_list:
            try:
                match = re.findall('SAFE-(.+)', safe[0])[0].upper()
            except Exception:
                continue
            else:
                if user[0].upper() == match and user[0].upper() in user_parsed:
                    assignment_data['user_id'] = user[1]
                    assignment_data['safe_id'] = safe[1]
                    result.append([user[0], assignment_data])
                    break
    if not result:
        raise Exception('EMPTY RESULT OF USER TO SAFE ASSIGNMENTS!')
    return result


# SET ACCOUNT-SAFE-LISTENERS ASSIGNMENTS
@func_decor('setting FUDO Acoount-Safe-Listener assignments')
def set_asl_assignment(fudo_accounts, fudo_safes, fudo_listeners, parsed_users):
    user_parsed = set([re.findall('PAM-(.+)', i['login'])[0] for i in parsed_users])
    if not user_parsed:
        raise Exception('NO USERS FOR A-S-F ASSIGNMENTS FOUND!')
    result = []
    account_changer_filter = list(filter(lambda x: re.findall('^A_PAM-', x[0]), fudo_accounts))
    account_filter = list(filter(lambda x: re.findall('^A_PAM-(.+)_.+_.+', x[0])[0] in user_parsed,
                                 account_changer_filter))
    safe_user_filter = list(filter(lambda x: re.findall('^SAFE-', x[0]), fudo_safes))
    safe_filter = list(filter(lambda x: re.findall('^SAFE-(.+)', x[0])[0] in user_parsed, safe_user_filter))
    assignment_data = None
    for safe in safe_filter:
        for account in account_filter:
            if re.findall('^A_PAM-(.+)_.+_.+', account[0])[0] == re.findall('^SAFE-(.+)', safe[0])[0]:
                for listener in fudo_listeners:
                    if re.findall('^A_PAM-.+_(.+)_.+', account[0]) == re.findall('^L_(.+)_.+', listener[0]):
                        assignment_data = {
                            "account_id": account[1],
                            "safe_id": safe[1],
                            "listener_id": listener[1]
                        }
                result.append([safe[0], assignment_data])
    if not result:
        raise Exception('EMPTY RESULT OF A-S-L ASSIGNMENTS!')
    return result


# PARSE DATA FROM OPERATORS FILE
@func_decor('parsing Operators file', 'crit')
def parse_operators_file(input_file):
    result = dict()
    with open(input_file, encoding='utf-8') as file:
        data = csv.reader(file)
        for row in data:
            result[row[0]] = row[1].split()
    if not result:
        raise Exception('EMPTY RESULT OF PARSING OPERATORS FILE!')
    return result


# SET OPERATORS FOR FUDO
@func_decor('setting Users for patching to Operator role')
def set_operators(parsed_users, fudo_users):
    result = []
    for operator in parsed_users:
        for user, user_id in fudo_users:
            if operator == user:
                data = {
                    'name': user,
                    'id': user_id
                }
                result.append(data)
                break
    if not result:
        raise Exception('EMPTY RESULT OF SETTING OPERATORS!')
    return result


# MODIFY FUDO USER
def modify_fudo_user(url, proxies, auth_header, user_id):
    """
        Fullname, Email, Phone, AD domain, LDAP base fieldes must be filled!
    """
    response = requests.patch(f'{url}/{user_id}', proxies=proxies, headers=auth_header,
                              json={"role": "operator"}, verify=False)
    if response.status_code not in (200, 201):
        raise Exception(f'{response.status_code}\n{response.text}')


# SET GRANTS OF FUDO OBJECTS FOR OPERATORS
def set_grants_for_operator(mode, operators, parsed_users, fudo_objects, fudo_servers=None):
    """
    Args:
        modes: 'users'/'safes'/'accounts'/'servers'
        fudo_objects: tuple(name, id)
        fudo_servers: dict(name, ip, id, protocol, scope; use with fudo accounts data
    """
    result = []
    for operator in operators:
        for op_user in parsed_users[operator['name']]:
            if mode == 'users':
                for user, user_id in fudo_objects:
                    if op_user == user:
                        result.append({'to_user_id': operator['id'], 'for_user_id': str(user_id)})

            elif mode == 'safes':
                for safe, safe_id in fudo_objects:
                    if re.search(fr'SAFE-{op_user}', safe):
                        result.append({'to_user_id': operator['id'], 'for_safe_id': str(safe_id)})

            elif mode == 'accounts':
                fudo_accs_filtered = list(filter(lambda x: re.search(fr'{op_user}', x[0])
                                                           and 'CHANGER' not in x[0], fudo_objects))
                for acc, acc_id in fudo_accs_filtered:
                    result.append({'to_user_id': operator['id'], 'for_account_id': str(acc_id)})

            elif mode == 'servers':
                fudo_accs_filtered = filter(lambda x: re.search(fr'{op_user}', x[0])
                                                           and 'CHANGER' not in x[0], fudo_objects)
                # GET (NAME, IP, PROTOCOL)
                servers_to_process = ((re.search(r'^A_(L-)?PAM-(\w+)_\w+_\d+\.\d+\.\d+\.\d+$', x[0]).group(2),
                                          re.search(r'_(\d+\.\d+\.\d+\.\d+)$', x[0]).group(1),
                                           re.search(r'_(\w+)_\d+\.\d+\.\d+\.\d+$', x[0]).group(1).lower())
                                            for x in fudo_accs_filtered)
                for server in servers_to_process:
                    for fudo_server in fudo_servers:
                        if server[1] == fudo_server['ip'] and server[2] == fudo_server['protocol']:
                            result.append({'to_user_id': operator['id'], 'for_server_id': fudo_server['id']})
                            break

            else:
                raise Exception('WRONG MODE!')
    if not result:
        raise Exception('EMPTY RESULT OF SETTING FUDO OBJECTS FOR OPERATORS!')
    return result
