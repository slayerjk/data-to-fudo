import requests
import csv
import re
from app_scripts.project_helper import func_decor
from project_static import logging, fudo_bind_ip


# FUNCTION: GETTING FUDO DATA
def get_fudo_data(url, headers, proxies) -> None:
    resp = requests.get(url, headers=headers, proxies=proxies, verify=False)
    if resp.status_code not in (200, 201):
        raise Exception(f'FAILED TO GET FUDO DATA:{resp.status_code}\n{resp.url}\n{resp.text}')


# FUNCTION: SEND DATA TO FUDO
def post_data_to_fudo(url, proxies, auth_header, post_data):
    resp = requests.post(url, proxies=proxies, headers=auth_header, json=post_data, verify=False)
    if resp.status_code not in (200, 201):
        raise Exception(f'{resp.status_code}\n{resp.url}\n{resp.text}')


# FUNCTION: PARSE AND PREPARE SERVERS DATA FROM INPUT CSV
@func_decor('parsing and setting server data', 'crit')
def parse_n_set_server_data(input_file: bytes) -> list:
    """
    Parse and enrich data from input csv file

    :param input_file: CSV file
    :return: list of parsed and enriched data

    ROWS of CSV:
        1 Auth Domain: authentication domain(short name)
        2 Scope: your own definitons of scope/group of network segment/compliance
        3 OS
        4 Name(DNS)
        5 IP
        6 Device Type
            SW-windows;
            SN-*nix;
            SC-storage control;
            SM-server management;
            ND-network device
        7 User List for SSH - ("User1, User2, ...")
        8 User List for RDP - ("User1, User2, ...")
        9 User List for HTTP - ("User1, User2, ...")

    Return example:
    # SERVER DATA(RDP EXAMPLE
    [
        {
            'server_data': {
                'description': 'eset-edr.xxx.org; Windows Server 2022',
                'address': '10.x.x.x',
                'bind_ip': '10.x.x.x',
                'auth': 'AUTH'
                'protocol': 'rdp',
                'port': 3389,
                'rdp_nla_enabled': True,
                'tls_enabled': True,
                'name': 'API_S_BANK_RDP_10.x.x.x'
            },
            'pool_data': {
                'name': 'API_S_SCOP_RDP_10.x.x.x',
                'pool_mark': 'SW',
                'scope': 'SCOPE',
                'address': '10.x.x.x'
            },
            'user_data':
                [
                    {'name': 'USER1', 'account_name': 'A_PAM-USER1_RDP_10.x.x.x'},
                    {'name': 'USER2', 'account_name': 'A_PAM-USER2_RDP_10.x.x.x'},
                    {'name': 'USER3', 'account_name': 'A_PAM-USER3_RDP_10.x.x.x'}
                ]
        }
        # ... OTHER IP-PROTOCOL DATA
    ]

    """
    with (open(input_file, 'r') as in_file):
        file_data = csv.reader(in_file)
        result = []

        protocols = ['ssh', 'rdp', 'http']

        for row in file_data:
            server_ip = str(row[4].strip())

            if not server_ip:
                raise Exception(f'IP COLUMN IS EMPTY: {row}')
            if not row[5]:
                raise Exception(f'EMPTY SYSTEM TYPE COLUMN! CHECK {server_ip}')

            # for ind, proto_data in enumerate(row[5:]):
            for ind, proto_data in enumerate(row[6:]):
                server_data = dict()
                temp = dict()
                users = []

                if len(proto_data) == 0:
                    continue
                else:
                    # server_data['description'] = f'{row[2].strip()}; {row[1].strip()}'
                    server_data['description'] = f'{row[3].strip()}; {row[2].strip()}'
                    server_data['address'] = server_ip.strip()
                    server_data['bind_ip'] = fudo_bind_ip

                    server_data['auth'] = row[1]
                    if not server_data['auth']:
                        raise Exception(f'NO AUTH DOMAIN FOUND FOR {row[4]}, FIX FIRST!')

                    if ind == 0:  # SSHs
                        server_data['protocol'] = protocols[0]
                        server_data['port'] = 22
                        if not proto_data[0]:
                            raise Exception(f'NO USERS FILLED FOR SERVER!({server_data["name"]})')
                        # users = [i.replace(',', '') for i in row[5].split()]
                        users = [i.replace(',', '') for i in row[6].split()]
                    elif ind == 1:  # RDP
                        server_data['protocol'] = protocols[1]
                        server_data['port'] = 3389
                        server_data['rdp_nla_enabled'] = True
                        server_data['tls_enabled'] = True
                        if not proto_data[1]:
                            raise Exception(f'NO USERS FILLED FOR SERVER!({server_data["name"]})')
                        # users = [i.replace(',', '').strip() for i in row[6].split()]
                        users = [i.replace(',', '').strip() for i in row[7].split()]
                    elif ind == 2:  # HTTP
                        server_data['protocol'] = protocols[2]
                        server_data['port'] = 443
                        server_data['http_authentication'] = True
                        server_data['http_password_element'] = '[id="password"]'
                        server_data['http_username_element'] = '[id="username"]'
                        server_data['http_signon_realm'] = f'https://{server_data["address"]}'
                        # server_data['http_timeout'] = 900  # inactivity period, default value = 900 sec(15min)
                        if not proto_data[2]:
                            raise Exception(f'NO USERS FOR SERVER!({server_data["ip"]}({server_data["protocol"]})')
                        # users = [i.replace(',', '') for i in row[7].split()]
                        users = [i.replace(',', '') for i in row[8].split()]

                    server_data['name'] = f'API_S_{row[0]}_{server_data["protocol"].upper()}_{server_ip}'

                temp['server_data'] = server_data

                # POOL DATA
                pool_data = dict()

                pool_data['name'] = server_data['name']
                # pool_data['pool_mark'] = row[4].strip()
                pool_data['pool_mark'] = row[5].strip()
                pool_data['scope'] = row[0].strip()
                pool_data['address'] = server_data['address']

                temp['pool_data'] = pool_data

                # USER DATA
                users_temp = list()

                for user in users:
                    user_data = {
                        'name': user,
                    }

                    acc_prefix = ''
                    if server_data['auth'].strip().upper() == 'LOCAL':
                        acc_prefix = 'A_L-PAM-'
                    else:
                        acc_prefix = 'A_PAM-'

                    if server_data['protocol'] == protocols[0]:  # SSH
                        user_data['account_name'] = f'{acc_prefix}{user}_SSH_{server_ip}'
                    elif server_data['protocol'] == protocols[1]:  # RDP
                        user_data['account_name'] = f'{acc_prefix}{user}_RDP_{server_ip}'
                    elif server_data['protocol'] == protocols[2]:  # HTTP
                        user_data['account_name'] = f'{acc_prefix}{user}_HTTP_{server_ip}'

                    users_temp.append(user_data)

                    temp['user_data'] = users_temp

                result.append(temp)

    if not result:
        raise Exception('EMPTY RESULT OF PARSING SERVERS!')
    return result


# CREATE SAFE
def create_fudo_safe(safe_url: str, user_url: str, us_url: str, proxies: dict, headers: dict, user: str) -> None:
    """
    Create FUDO Safe based on parsed data created by parse_n_set_server_data
    Create User to Safe assignment

    :param safe_url: str, FUDO API Save URL
    :param user_url: str, FUDO API User URL
    :param us_url: str, FUDO API User to Safe assignment URL
    :param proxies: dict, proxies
    :param headers: dict, headers(AUTH)
    :param user: str, list of users to create safe
    """
    # getting user id
    try:
        user_resp = requests.get(
            f'{user_url}?filter=name.eq({user})',
            headers=headers,
            proxies=proxies,
            verify=False
        )
    except Exception as e:
        raise Exception(e)

    if user_resp.status_code != 200:
        raise Exception(f'FAILED TO GET USER ID\n{user_resp.status_code}\n, {user_resp.url}\n, {user_resp.text}')
    else:
        try:
            user_id = user_resp.json()['user'][0]['id']
        except Exception as e:
            raise Exception(f'FAILED TO FIND USER DATA IN API: {user}\n{e}')

    # creating safe
    safe_data = {
        "name": f"SAFE-{user}",
        "inactivity_limit": 30,
        "rdp_resolution": "1920x1080",
        "webclient": True,
        "vnc_clipcli": False,
        "vnc_clipsrv": False
    }

    create_resp = None
    try:
        create_resp = requests.post(safe_url, proxies=proxies, headers=headers, verify=False, json=safe_data)
    except Exception:
        raise Exception(
            f'FAILED TO CREATE SAFE{user}:\n{create_resp.status_code}\n{create_resp.text}'
        )
    else:
        if create_resp.status_code not in (200, 201):
            raise Exception(create_resp.text)

    # getting safe id
    safe_resp = None
    try:
        safe_resp = requests.get(
            f'{safe_url}?filter=name.eq(SAFE-{user})',
            proxies=proxies,
            headers=headers,
            verify=False
        )
    except Exception:
        raise Exception(
            f'FAILED TO GET SAFE{user}:\n{safe_resp.status_code}\n{safe_resp.text}'
        )
    else:
        if safe_resp.status_code not in (200, 201):
            raise Exception(safe_resp.text)
        else:
            safe_id = safe_resp.json()['safe'][0]['id']

    # try to make User to Safe assignment
    logging.info(f'STARTED: assigning {user} to {safe_data["name"]}')
    us_data = {
            "user_id": user_id,
            "safe_id": safe_id
        }

    try:
        us_resp = requests.post(us_url, proxies=proxies, headers=headers, verify=False, json=us_data)
    except Exception as e:
        logging.error(f'FAILED: assigning {user} to {safe_data["name"]}:\n{e}')
    else:
        if us_resp.status_code not in (200, 201):
            raise Exception(f'{us_resp.status_code}\n{us_resp.text}')

    logging.info(f'DONE: assigning {user} to {safe_data["name"]}')


# FUNCTION: ENRICH SERVER DATA
@func_decor('enriching parsed data', 'crit')
def enrich_data(
        server_url: str,
        listener_url: str,
        pool_url: str,
        user_url: str,
        safe_url: str,
        headers: dict,
        proxies: dict,
        parsed_data: dict
) -> dict:
    """
    :param server_url: str, FUDO API URL for Server
    :param listener_url: str, FUDO API URL for Listener
    :param pool_url: str, FUDO API URL for Pool
    :param user_url: str, FUDO API URL for User
    :param safe_url: str, FUDO API URL for Safe
    :param headers: dict, FUDO Auth header
    :param proxies: dict, proxies
    :param parsed_data: dict, result of "parse_n_set_server_data(input_file: bytes)"
    :return list: same list with servers id
    """
    server_data = parsed_data['server_data']
    pool_data = parsed_data['pool_data']
    user_data = parsed_data['user_data']

    # TRY TO GET SERVER'S INFO
    server_resp = requests.get(
        f'{server_url}&filter=name.eq({server_data["name"]})',
        headers=headers, proxies=proxies, verify=False
    )

    if server_resp.status_code == 200:
        try:
            server_id = server_resp.json()['server'][0]['id']
        except Exception as e:
            logging.warning(f'FAILED TO FIND SERVER\'S ID, skip this server({server_data["name"]}):\n{e}')
        else:
            server_data['server_id'] = server_id
    else:
        logging.warning(f'FAILED TO GET SERVER INFO\n{server_resp.status_code}\n, '
                        f'{server_resp.url}\n, {server_resp.text}')
    # response = requests

    # TRY TO GET LISTENERS DATA AND MATCH WITH SERVERS
    """
    Listeners example:
    {'result': 'success', 
    'listener': [
        {'id': '***977', 
        'name': 'L_RDP_bastion:3389', 
        'blocked': False, 
        'protocol': 'rdp', 
        'mode': 'bastion', 
        'listen_ip': '10.X.X.X', 
        ...
    ]
    """
    try:
        listeners_resp = requests.get(
            listener_url,
            proxies=proxies,
            headers=headers,
            verify=False
        )
    except Exception as e:
        raise Exception(f'FAILED TO GET LISTENERS:\n{e}')
    else:
        if listeners_resp.status_code not in (200, 201):
            raise Exception(f'FAILED TO GET LISTENERS, check response:\n{listeners_resp.text}')

        listeners = [i for i in listeners_resp.json()['listener']]

        # I'm using only one HTTP listener
        for listener in listeners:
            if server_data['protocol'] == 'http':
                if server_data['protocol'] == listener['protocol']:
                    server_data['listener_name'] = listener['name']
                    server_data['listener_id'] = listener['id']
                    break
            else:
                if server_data['protocol'] == listener['protocol'] and server_data['port'] == listener['listen_port']:
                    server_data['listener_name'] = listener['name']
                    server_data['listener_id'] = listener['id']
                    break

    # TRY TO GET SEVER'S POOL TO ASSIGN TO
    # get current pools list
    pools_resp = requests.get(pool_url, headers=headers, proxies=proxies, verify=False)

    if pools_resp.status_code != 200:
        raise Exception(f'FAILED TO GET POOL INFO\n{pools_resp.status_code}\n, {pools_resp.url}\n, {pools_resp.text}')

    acc_match_pattern = r'.+?_.+?_(.+?)_(.+?)_.*'

    account_mark = pool_data['pool_mark']
    acc_match_re = re.match(acc_match_pattern, pool_data['name'])
    try:
        account_scope = acc_match_re.group(1)
        account_proto = acc_match_re.group(2)
    except Exception as e:
        raise Exception(f'FAILED TO GET ACCOUNT DETAILS FOR POOL:\n{e}')

    """
    TRY TO FILTER SUCH POOL DATA(Example):
    
    'pool_data': {'name': 'API_S_TEST_RDP_10.1.1.1', 'pool_mark': 'SW', 'scope': 'TEST', 'address': '10.1.1.1'}
    SCOPE = TEST
    MARK = SW
    PROTO = RDP
    
    AND
    
    FUDO POOL(Example):
    "result": "success",
    "pool": [
        {
            "id": "***988",
            "name": "P_ALL_LDAPS_PC"
        },
        ...
    ]
    """
    try:
        pools = [i for i in pools_resp.json()['pool']]
    except Exception as e:
        raise Exception(f'FAILED TO GET POOLS,\n{e}')
    """
    Pools list example(1 item):
    
    {'id': '***988', 
    'name': 'P_ALL_LDAPS_PC', 
    'description': 'PwdChangers Servers(DC)', 
    'created_at': '202*-**-** 14:35:51.074676+**', 
    'modified_at': '202*-**-** 11:09:59.6911+**', 
    'servers': ['***971', '***972', '***973', '***581'], 
    'protocol': 'rdp', 
    'builtin': False, 
    'hidden': False}
    """
    pool_match_pattern = r'._(.+?)_(.+?)_(.+)'
    flag = False

    for pool in pools:
        pool_match_re = re.match(pool_match_pattern, pool['name'])
        try:
            # separate rule for HTTP, because my pools for HTTP looks like: P_SCOPE_HTTP_VA; VA - for VArious
            if account_proto == 'HTTP':
                if pool_match_re.group(1) == account_scope and pool_match_re.group(2) == account_proto and \
                        pool_match_re.group(3) == 'VA':
                    pool_data['pool_name'] = pool['name']
                    pool_data['pool_id'] = pool['id']
                    flag = True
                    break

            else:
                if pool_match_re.group(1) == account_scope and pool_match_re.group(2) == account_proto and \
                        pool_match_re.group(3) == account_mark:
                    pool_data['pool_name'] = pool['name']
                    pool_data['pool_id'] = pool['id']
                    flag = True
                    break

        except Exception as e:
            raise Exception(f'FAILED TO MATCH ACC & POOL DATA:\n{pool["name"]}\n{e}')

    if not flag:
        raise Exception(f'FAILED TO FIND CORRECT POOL({pool_data["name"]})')

    # TRY TO ENRICH USER DATA
    """
    !USER MUST EXIST IN FUDO!
    
    User data example:
    'user_data':
                [
                    {'name': 'MELIKHOD',
                    'account_name': 'A_PAM-MELIKHOD_RDP_10.15.116.40'},
                    {'name': 'PRASSOLA', 'account_name': 'A_PAM-PRASSOLA_RDP_10.15.116.40'},
                    {'name': 'LIVITALI', 'account_name': 'A_PAM-LIVITALI_RDP_10.15.116.40'}
                ]
                
    User response example:
    {'result': 'success', 
    'user': [
        {'id': '***996', 
        'name': 'USER1', 
        ...}]
    ...
    """
    # # trying to get user_id
    for user in user_data:
        user_resp = requests.get(
            f'{user_url}?filter=name.eq({user["name"]})',
            headers=headers,
            proxies=proxies,
            verify=False
        )

        if user_resp.status_code != 200:
            raise Exception(f'FAILED TO GET POOL INFO\n{user_resp.status_code}\n, {user_resp.url}\n, {user_resp.text}')
        else:
            try:
                user['user_id'] = user_resp.json()['user'][0]['id']
            except Exception as e:
                raise Exception(f'FAILED TO FIND USER DATA IN API: {user["name"]}\n{e}')

        # set changer data
        user['changer'] = parsed_data['pool_data']['scope']

        # trying to get user's safe_id
        safe_resp = requests.get(
            f'{safe_url}?filter=name.eq(SAFE-{user["name"]})',
            headers=headers,
            proxies=proxies,
            verify=False
        )

        if safe_resp.status_code != 200:
            raise Exception(
                f'FAILED TO GET USER SAFE INFO\n{safe_resp.status_code}\n, {safe_resp.url}\n, {safe_resp.text}'
            )
        else:
            try:
                user['safe_name'] = safe_resp.json()['safe'][0]['name']
                user['safe_id'] = safe_resp.json()['safe'][0]['id']
            except Exception as e:
                raise Exception(f'FAILED TO FIND USER SAFE DATA IN API: {user["name"]}\n{e}')

    return parsed_data


# ASSIGN SERVERS TO POOLS
def assign_server_to_pool(
        pools_url: str,
        proxies: dict,
        headers: dict,
        parsed_data: dict
) -> None:
    """
        Assign Server to Pool based on enriched data created by
        Skip if safe is already created.

        :param pools_url: str, FUDO API Save URL
        :param proxies: dict, proxies
        :param headers: dict, headers(AUTH)
        :param parsed_data: dict, enriched data
    """
    data = {
        'server_id': parsed_data['server_data']['server_id'],
        'pool_id': parsed_data['pool_data']['pool_id']
    }
    try:
        resp = requests.post(
            f'{pools_url}/server',
            proxies=proxies,
            headers=headers,
            json=data,
            verify=False
        )
    except Exception as e:
        raise Exception(f'FAILED TO DO ASP:\n{e}')
    else:
        if resp.status_code not in (200, 201):
            raise Exception(f'{resp.status_code}\n{resp.text}')


# CREATE ACCOUNTS
def create_accounts(
        acc_url: str,
        server_url: str,
        proxies: dict,
        headers: dict,
        parsed_data: dict,
        acc_pwd: str,
        dcs: dict
) -> dict:
    """
    Create changers for LDAP based on parsed data
    Then create accounts

    !Changers Servers must exist! example to search S_CHANGER-<SCOPE>_LDAPS_<DC IP>

    :param acc_url: str, FUDO API URL for Account
    :param server_url: str, FUDO API URL for Server
    :param proxies: dict, proxies
    :param headers: dict, headers(AUTH)
    :param parsed_data: dict, one obj of parsed data
    :param acc_pwd: str, default password for changers
    :param dcs: dict, dict with DOMAIN short/long DN
    """
    # get changers servers
    try:
        servers_resp = requests.get(
            f'{server_url}&filter=name.match(CHANGER)',
            proxies=proxies,
            headers=headers,
            verify=False
        )
    except Exception as e:
        raise Exception(f'FAILED TO GET SERVERS CHANGERS, check request:\n{e}\n')
    else:
        if servers_resp.status_code not in (200, 201):
            raise Exception(f'{servers_resp.status_code}\n{servers_resp.text}')
        else:
            changers = servers_resp.json()['server']

    # creating corresponding changer account
    for user in parsed_data['user_data']:
        domain = dcs[parsed_data['pool_data']['scope']][1]
        changer_zone = dcs[parsed_data['pool_data']['scope']][0]
        pattern = f'S_CHANGER-({changer_zone})_.*'

        for changer in changers:
            changer_zone_match = re.match(pattern, changer['name'])

            try:
                changer_zone_match_result = changer_zone_match.group(1)
            except AttributeError:
                continue

            if changer_zone != changer_zone_match_result:
                continue
            else:
                # create changer account
                logging.info(f'STARTED: creating changer account: {user["changer"]}')

                changer_acc_data = {
                    "name": f'A_CHANGER-{changer_zone}_PAM-{user["name"]}',
                    "type": "regular",
                    "dump_mode": "all",
                    "category": "privileged",
                    "server_id": changer['id'],
                    "domain": domain,
                    "login": f'PAM-{user["name"]}',
                    "method": "password",
                    "secret": acc_pwd
                }

                user['changer'] = changer_acc_data['name']
                user['domain'] = domain

                try:
                    create_changer_resp = requests.post(
                        acc_url,
                        proxies=proxies,
                        headers=headers,
                        verify=False,
                        json=changer_acc_data
                    )
                except Exception as e:
                    # logging.warning(f'ERROR({user["changer"]}):\n{e}\n')
                    raise Exception(f'ERROR({user["changer"]}):\n{e}\n')
                else:
                    if create_changer_resp.status_code not in (200, 201):
                        logging.warning(
                            f'ERROR({user["changer"]}):'
                            f'\n{create_changer_resp.status_code}'
                            f'\n{create_changer_resp.text}\n'
                        )

                logging.info(f'DONE creating changer account: {user["changer"]}\n')

                # trying to get changer id
                try:
                    changer_resp = requests.get(
                        f'{acc_url}&filter=name.eq({user["changer"]})',
                        proxies=proxies,
                        headers=headers,
                        verify=False
                    )
                except Exception as e:
                    # logging.warning(f'FAILED TO GET CHANGER ID({user["changer"]}):\n{e}\n')
                    raise Exception(f'FAILED TO GET CHANGER ID({user["changer"]}):\n{e}\n')
                else:
                    if changer_resp.status_code not in (200, 201):
                        logging.warning(f'ERROR({user["changer"]}):\n{changer_resp.status_code}\n{changer_resp.text}\n')
                    else:
                        user['changer_id'] = changer_resp.json()['account'][0]['id']

            break

    for user in parsed_data['user_data']:
        # now trying to create usual account
        logging.info(f'CREATING REGULAR ACCOUNT NOW({user["account_name"]})')

        acc_data = {
            "name": user["account_name"],
            "type": "regular",
            "dump_mode": "all",
            "category": "privileged",
            "server_id": parsed_data["server_data"]["server_id"],
            # "domain": domain,
            "login": f'PAM-{user["name"]}',
            "method": "account",
            "account_id": user["changer_id"]
        }

        try:
            create_acc_resp = requests.post(acc_url, proxies=proxies, headers=headers, verify=False, json=acc_data)
        except Exception as e:
            # logging.warning(f'FAILED TO CREATE REGULAR ACCOUNT({user["account_name"]}):\n{e}')
            raise Exception(f'CHECK CREATE REGULAR ACCOUNT REQUEST({user["account_name"]}):\n{e}')
        else:
            if create_acc_resp.status_code not in (200, 201):
                logging.warning(
                    f'ERROR({user["account_name"]}):\n{create_acc_resp.status_code}\n{create_acc_resp.text}\n'
                )
            else:
                logging.info(f'DONE: CREATING REGULAR ACCOUNT NOW({user["account_name"]})')

        # get created account id
        logging.info(f'STARTED: getting newly created account id({user["account_name"]})')
        try:
            acc_resp = requests.get(
                f'{acc_url}&filter=name.eq({user["account_name"]})',
                proxies=proxies,
                headers=headers,
                verify=False
            )
        except Exception as e:
            # logging.warning(f'FAILED TO CREATE REGULAR ACCOUNT({user["account_name"]}):\n{e}')
            raise Exception(f'FAILED TO GET REGULAR ACCOUNT ID, check request({user["account_name"]}):\n{e}')
        else:
            if acc_resp.status_code not in (200, 201):
                logging.warning(
                    f'ERROR({user["account_name"]}):\n{create_acc_resp.status_code}\n{create_acc_resp.text}\n'
                )
            else:
                logging.info(f'DONE: getting newly created account id({user["account_name"]})')
                user['account_id'] = acc_resp.json()['account'][0]['id']

    return parsed_data


# CREATE USER TO SAFE ASSINMENT & ACCOUNT, LISTENER TO SAFE ASSIGNMENT
def assign_data_to_safe(
        # us_url: str,
        als_url: str,
        proxies: dict,
        headers: dict,
        parsed_data: dict,
) -> None:
    """
    Create Accounts-Listeners to Safe assignment

    !Changers Servers must exist! example to search S_CHANGER-<SCOPE>_LDAPS_<DC IP>

    #:param us_url: str, FUDO API USER TO SAFE URL
    :param als_url: str, FUDO API ACCOUNT-LISTENER TO SAFE URL
    :param proxies: dict, proxies
    :param headers: dict, headers(AUTH)
    :param parsed_data: dict, one obj of parsed data
    """
    # trying to make Account-Listener to Safe assingment
    listener_name = parsed_data['server_data']['listener_name']
    listener_id = parsed_data['server_data']['listener_id']

    for user in parsed_data['user_data']:
        logging.info(
            f'STARTED: assigning {user["account_name"]} and {listener_name} to {user["safe_name"]}')

        als_data = {
            "account_id": user['account_id'],
            "safe_id": user['safe_id'],
            "listener_id": listener_id
        }

        try:
            als_resp = requests.post(als_url, proxies=proxies, headers=headers, verify=False, json=als_data)
        except Exception as e:
            logging.error(f'FAILED: assigning {user["account_name"]} and {listener_name} to {user["safe_name"]}:\n{e}')
            continue
        else:
            if als_resp.status_code not in (200, 201):
                logging.error(
                    f'FAILED: assigning {user["account_name"]} and {listener_name} to {user["safe_name"]}:'
                    f'\n{als_resp.status_code}'
                    f'\n{als_resp.text}'
                )
                continue
        logging.info(
            f'DONE: assigning {user["account_name"]} and {listener_name} to {user["safe_name"]}')


# PARSE DATA FROM OPERATORS FILE
@func_decor('parsing Operators file', 'crit')
def parse_operators_file(input_file: bytes) -> list:
    """
    Parse input CSV

    :param input_file: bytes, CSV file

    :retrun list: list of dicts

    return example:
    [
        {'OP-TEST-1': {'users': ['user1', 'user2'], 'user_ids': None, 'servers': None, 'accounts': None, 'safes': None}}
        {'OP-TEST-2': {'users': ['user3'], 'user_ids': None, 'servers': None, 'accounts': None, 'safes': None}}
    ]
    """
    keys = ('operator', 'users', 'user_ids', 'servers', 'accounts', 'safes')
    result = list()

    with (open(input_file, encoding='utf-8') as file):
        data = csv.reader(file)

        for row in data:
            temp = dict.fromkeys(keys)
            temp['operator'] = [row[0]]
            temp['users'] = row[1].split()
            result.append(temp)
    if not result:
        raise Exception('EMPTY RESULT OF PARSING OPERATORS FILE!')
    return result


# GET USER IDs
def get_users_ids(user_url: str, proxies: dict, headers: dict, parsed_data: dict) -> dict:
    """
    1. Get Operator id - result is list of [operator, operator_id]
    2. Get user ids granted for operator

    :param user_url: str, API URL to get user data
    :param proxies: dict, proxies
    :param headers: dict, auth headers
    :param parsed_data: dict, parsed result of parse_operators_file

    :return dict: same parsed data enriched with user ids
    """
    # first get operator's id
    operator = parsed_data['operator'][0]

    try:
        resp = requests.get(
            f'{user_url}?filter=name.eq({operator})',
            proxies=proxies,
            headers=headers,
            verify=False
        )
    except Exception as e:
        raise Exception(e)

    if resp.status_code not in (200, 201):
        raise Exception(f'{resp.status_code}\n{resp.text}')

    try:
        operator_id = resp.json()['user'][0]['id']
    except (IndexError, KeyError):
        raise Exception(f'NOT FOUND OPERATOR ID({operator})')

    parsed_data['operator'].append(operator_id)

    # not try to get every user' id granted for operator
    parsed_data['user_ids'] = list()

    for user in parsed_data['users']:
        try:
            resp = requests.get(
                f'{user_url}?filter=name.eq({user})',
                proxies=proxies,
                headers=headers,
                verify=False
            )
        except Exception as e:
            raise Exception(e)
        else:
            if resp.status_code not in (200, 201):
                raise Exception(f'{resp.status_code}\n{resp.text}')

            try:
                user_id = resp.json()['user'][0]['id']
            except (IndexError, KeyError):
                raise Exception(f'NOT FOUND USER ID FOR {user}')

            parsed_data['user_ids'].append(user_id)

    return parsed_data


# MODIFY USER TO BE OPERATOR
def set_operator_role(modify_user_url: str, proxies: dict, headers: dict, parsed_data: dict) -> None:
    """
    Get user ids granted for operator

    :param modify_user_url: str, API URL modify user(set Operator role)
    :param proxies: dict, proxies
    :param headers: dict, auth headers
    :param parsed_data: dict, parsed result of parse_operators_file

    :return dict: same parsed data enriched with user ids
    """
    operator_id = parsed_data['operator'][1]
    data = {"role": "operator"}

    try:
        resp = requests.patch(
            f'{modify_user_url}/{operator_id}',
            proxies=proxies,
            headers=headers,
            verify=False,
            json=data
        )
    except Exception as e:
        raise Exception(e)
    else:
        if resp.status_code not in (200, 201):
            raise Exception(f'{resp.status_code}\n{resp.text}\n{resp.url}\n')


# GET SERVERS IDs AND ACCOUNTS IDs
def get_servers_n_accounts_ids(acc_url: str, proxies: dict, headers: dict, parsed_data: dict) -> dict:
    """
    Get Servers ids & Account ids based on Users granted for operator

    :param acc_url: str, API URL to get Accounts data
    :param proxies: dict, proxies
    :param headers: dict, auth headers
    :param parsed_data: dict, parsed result of parse_operators_file

    :return dict: same parsed data enriched with user ids
    """
    parsed_data['servers'] = set()
    parsed_data['accounts'] = set()

    for user in parsed_data['users']:
        try:
            resp = requests.get(
                f'{acc_url}&filter=name.match({user})',
                proxies=proxies,
                headers=headers,
                verify=False
            )
        except Exception as e:
            raise Exception(e)
        else:
            if resp.status_code not in (200, 201):
                raise Exception(f'{resp.status_code}\n{resp.text}')
            # exclude PASSWORD CHANGER accounts and servers
            servers = [i for i in resp.json()['account'] if 'CHANGER' not in i['name']]
        """
        Example of server in servers:
        
        [
            {
                'id': '***0491', 
                'name': 'A_PAM-TEST1_RDP_172.X.X.X', 
                'server_id': '***972', 
                'ocr_enabled': False
            }
            ...
        ]
        """
        for server in servers:
            parsed_data['servers'].add(server['server_id'])
            parsed_data['accounts'].add(server['id'])

    return parsed_data


# GET LISTENER IDs(NOT NECESSARY FOR OPERATORS!)
def get_listeners_ids(listener_url: str, proxies: dict, headers: dict, parsed_data: dict) -> dict:
    """
    Get ALL Listener ids

    :param listener_url: str, API URL to get Accounts data
    :param proxies: dict, proxies
    :param headers: dict, auth headers
    :param parsed_data: dict, parsed result of parse_operators_file

    :return dict: same parsed data enriched with user ids
    """
    try:
        resp = requests.get(
            f'{listener_url}?fields=id,name',
            proxies=proxies,
            headers=headers,
            verify=False
        )
    except Exception as e:
        raise Exception(e)
    else:
        if resp.status_code not in (200, 201):
            raise Exception(f'{resp.status_code}\n{resp.text}')
        listeners = [i for i in resp.json()['listener']]
        """
        Listeners example:
        
        [
            {
                'id': '5665528331232083977', 
                'name': 'L_RDP_bastion:9833'
            }, 
            ...
        ]
        """
        parsed_data['listeners'] = [i['id'] for i in listeners]

    return parsed_data


# GET SAFES IDs
def get_safes_ids(safe_url: str, proxies: dict, headers: dict, parsed_data: dict) -> dict:
    """
    Get Safes ids based on Users granted for operator

    :param safe_url: str, API URL to get Accounts data
    :param proxies: dict, proxies
    :param headers: dict, auth headers
    :param parsed_data: dict, parsed result of parse_operators_file

    :return dict: same parsed data enriched with user ids
    """
    parsed_data['safes'] = list()

    for user in parsed_data['users']:
        try:
            resp = requests.get(
                f'{safe_url}?fields=id,name&filter=name.eq(SAFE-{user})',
                proxies=proxies,
                headers=headers,
                verify=False
            )
        except Exception as e:
            raise Exception(e)
        else:
            if resp.status_code not in (200, 201):
                raise Exception(f'{resp.status_code}\n{resp.text}')
            # there is only one/none safe like SAFE-<USER>
            try:
                safe = resp.json()['safe'][0]['id']
            except (IndexError, KeyError):
                raise Exception(f'NOT FOUND SAFE FOR {user}')
            else:
                parsed_data['safes'].append(safe)

    return parsed_data


# SET GRANTS
def set_grants(
        grant_user_url: str,
        grant_acc_url: str,
        grant_srv_url: str,
        grant_safe_url: str,
        proxies: dict,
        headers: dict,
        parsed_data: dict
) -> None:
    """
    Get Safes ids based on Users granted for operator

    :param grant_user_url: str, API URL to grant User to User
    :param grant_acc_url: str, API URL to grant Account to User
    :param grant_srv_url: str, API URL to grant Server to User
    :param grant_safe_url: str, API URL to grant Safe to User
    :param proxies: dict, proxies
    :param headers: dict, auth headers
    :param parsed_data: dict, parsed result of parse_operators_file

    :return dict: same parsed data enriched with user ids
    """
    operator = parsed_data['operator'][0]
    operator_id = parsed_data['operator'][1]

    # grant users to operator
    logging.info(f'STARTED: granting Users to {operator}')

    for user in parsed_data['user_ids']:
        data = {
            "to_user_id": operator_id,
            "for_user_id": user
        }

        try:
            resp = requests.post(grant_user_url, proxies=proxies, headers=headers, verify=False, json=data)
        except Exception as e:
            raise Exception(e)

        if resp.status_code not in (200, 201):
            logging.warning(f'FAILED TO GRANT {user} TO {operator}:\n{resp.status_code}\n{resp.text}\n')

    logging.info(f'DONE: granting Users to {operator}\n')

    # grant accounts to operator
    logging.info(f'STARTED: granting Accounts to {operator}')
    for account in parsed_data['accounts']:
        data = {
            "to_user_id": operator_id,
            "for_account_id": account
        }

        try:
            resp = requests.post(grant_acc_url, proxies=proxies, headers=headers, verify=False, json=data)
        except Exception as e:
            raise Exception(e)

        if resp.status_code not in (200, 201):
            logging.warning(f'FAILED TO GRANT {account} TO {operator}:\n{resp.status_code}\n{resp.text}\n')

    logging.info(f'DONE: granting Accounts to {operator}\n')

    # grant servers to operator
    logging.info(f'STARTED: granting Servers to {operator}')
    for server in parsed_data['servers']:
        data = {
            "to_user_id": operator_id,
            "for_server_id": server
        }

        try:
            resp = requests.post(grant_srv_url, proxies=proxies, headers=headers, verify=False, json=data)
        except Exception as e:
            raise Exception(e)

        if resp.status_code not in (200, 201):
            logging.warning(f'FAILED TO GRANT {server} TO {operator}:\n{resp.status_code}\n{resp.text}\n')

    logging.info(f'DONE: granting Servers to {operator}\n')

    # grant safes to operator
    logging.info(f'STARTED: granting Safes to {operator}')
    for safe in parsed_data['safes']:
        data = {
            "to_user_id": operator_id,
            "for_safe_id": safe
        }

        try:
            resp = requests.post(grant_safe_url, proxies=proxies, headers=headers, verify=False, json=data)
        except Exception as e:
            raise Exception(e)

        if resp.status_code not in (200, 201):
            logging.warning(f'FAILED TO GRANT {safe} TO {operator}:\n{resp.status_code}\n{resp.text}\n')

    logging.info(f'DONE: granting Safes to {operator}\n')
