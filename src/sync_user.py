#!/usr/bin/env python
# Azure AD user/group FreeIPA sync utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

# Import functions from src/aad.py
import src.aad
import src.logger
import src.freeIPA
import src.configure

def sync_users(config, access_token):
    aad_users = src.aad.get_aad_users(access_token)
    conn = src.freeIPA.freeIPA_bind(
        config.get('freeipa', 'server'),
        config.get('freeipa', 'user'),
        config.get('freeipa', 'password')
    )

    base_dn = f'cn=users,cn=accounts,{config.get("freeipa", "basedn")}'
    #print (f"Base DN: {base_dn}")
    next_uid = src.freeIPA.get_next_uid_number(conn, base_dn)
    new_users = []

    for user in aad_users:
        if 'userPrincipalName' in user:
            uid = user['userPrincipalName'].split('@')[0]
            if not src.freeIPA.check_user_exists(conn, base_dn, uid):
                user_data = {
                    'uid'               : uid,
                    'password'          : config.get('newuser','password'),
                    'givenName'         : user.get('givenName', ''),
                    'sn'                : user.get('surname', ''),
                    'mail'              : user.get('mail', ''),
                    'homeDirectory'     : f'/home/{uid}',
                    'loginShell'        : '/bin/bash',
                    'displayName'       : user.get('displayName', ''),
                    'uidNumber'         : next_uid,
                    'gidNumber'         : next_uid,
                    'gecos'             : user.get('displayName', ''),
                    'krbPrincipalName'  : f"{uid}@{config.get('freeipa', 'realm')}",
                }
                src.freeIPA.create_user(conn, base_dn, user_data)
                #print(f"  o {uid} just created, UID/GID: {next_uid}")
                new_users.append(user_data)
                next_uid += 1            
            else:
            #    print(f"  - {uid} already exists")
                pass

    return new_users 