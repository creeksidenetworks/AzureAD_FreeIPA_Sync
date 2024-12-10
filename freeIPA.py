#!/usr/bin/env python
# Azure AD user/group FreeIPA sync utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import ldap3
import ssl
import src.logger

# check if an user exists in FreeIPA
def check_user_exists(conn, base_dn, uid):
    search_filter = f"(uid={uid})"
    conn.search(search_base=base_dn, search_filter=search_filter, search_scope=ldap3.SUBTREE, attributes=['uid'])
    return len(conn.entries) > 0


# Get the next available UID/GID number
def get_next_uid_number(conn, base_dn):
    #print("Getting next UID/GID number")
    conn.search(
        search_base=base_dn,
        search_filter='(objectClass=posixAccount)',
        search_scope=ldap3.SUBTREE,
        #attributes=['uidNumber']
        attributes=['uidNumber', 'gidNumber']
    )
    id_numbers = []
    for entry in conn.entries:
        if 'uidNumber' in entry.entry_attributes_as_dict:
            id_numbers.append(int(entry.entry_attributes_as_dict['uidNumber'][0]))
        if 'gidNumber' in entry.entry_attributes_as_dict:
            id_numbers.append(int(entry.entry_attributes_as_dict['gidNumber'][0]))

    if id_numbers:
        next_id = max(id_numbers) + 1
    else:
        next_id = 10000

    #print(f"Next UID/GID number: {next_id}")
    return next_id

# add an user to FreeIPA
def create_user(conn, base_dn, user_data):
    uid = user_data['uid']
    user_dn = f"uid={uid},{base_dn}"

    attributes = {
        "objectClass": [
            "top",
            "person",
            "organizationalPerson",
            "inetOrgPerson",
            "posixAccount",
            "ipaobject",
            "krbPrincipalAux",
            "ipaSshGroupOfPubKeys",
            "ipaUserAuthTypeClass"
        ],
        'uid': user_data['uid'],
        'cn': user_data['displayName'],
        'givenName': user_data['givenName'],
        'sn': user_data['sn'],
        'mail': user_data['mail'],
        'homeDirectory': user_data['homeDirectory'],
        'loginShell': user_data['loginShell'],
        'userPassword': user_data['password'],
        'gidNumber': user_data['gidNumber'],
        'uidNumber': user_data['uidNumber'],
        "krbPrincipalName": user_data['krbPrincipalName']
    }  

    try:
        conn.add(user_dn, attributes=attributes)
        if conn.result['result'] == 0:
            src.logger.logger.info(f"User '{uid}' created successfully.")
        else:
            src.logger.logger.error(f"Failed to create user '{uid}': {conn.result}")
    except Exception as e:
        src.logger.logger.error(f"An error occurred while creating user '{uid}': {e}")
        raise

def sync_users(conn, base_dn, users):
    for user in users:
        uid = user['uid']
        if not check_user_exists(conn, base_dn, uid):
            create_user(conn, base_dn, uid, user)

def freeIPA_bind(server_address, username, password):
    try:
        # Configure TLS
        tls_configuration = ldap3.Tls(validate=ssl.CERT_NONE)

        # Bind to FreeIPA server using StartTLS (port 389)
        #print(f"Binding to FreeIPA server {server_address} as user {username}")
        server = ldap3.Server(server_address, port=389, get_info=ldap3.ALL, use_ssl=False, tls=tls_configuration)
        conn = ldap3.Connection(server, user=username, password=password)
        if not conn.start_tls():
            src.logger.logger.error(f"Failed to start TLS: {conn.result}")
            raise Exception(f"Failed to start TLS: {conn.result}")
        if not conn.bind():
            src.logger.logger.error(f"Failed to bind to FreeIPA server: {conn.result}")
            raise Exception(f"Failed to bind to FreeIPA server: {conn.result}")
        src.logger.logger.info("Successfully bound to FreeIPA server")
        return conn
    except Exception as e:
        src.logger.logger.error(f"An error occurred while binding to FreeIPA server: {e}")
        raise

def check_group_exists(conn, base_dn, group_name):
    search_filter = f"(cn={group_name})"
    conn.search(search_base=base_dn, search_filter=search_filter, search_scope=ldap3.SUBTREE, attributes=['cn'])
    return len(conn.entries) > 0

def get_group_members(conn, base_dn, group_name):
    #group_dn = f"cn={group_name},{base_dn}"
    search_filter = f"(cn={group_name})"
    conn.search(search_base=base_dn, search_filter=search_filter, search_scope=ldap3.SUBTREE, attributes=['member'])
    if len(conn.entries) > 0:
        members = conn.entries[0]['member']
        return members
    else:
        src.logger.logger.error(f"Group '{group_name}' not found.")
        return []


def create_group(conn, base_dn, group_name, description):
    group_dn = f"cn={group_name},{base_dn}"
    attributes = {
        'objectClass': ['top', 'groupOfNames'],
        'cn': group_name,
        'description': description,
        'member': []  # Initialize with an empty member list
    }
    try:
        conn.add(group_dn, attributes=attributes)
        if conn.result['result'] == 0:
            src.logger.logger.info(f"Group '{group_name}' created successfully.")
        else:
            src.logger.logger.error(f"Failed to create group '{group_name}': {conn.result}")
    except Exception as e:
        src.logger.logger.error(f"An error occurred while creating group '{group_name}': {e}")
        raise

# Example usage
if __name__ == "__main__":
    server_address = 'ipa1.icm.corp'
    username = 'cn=Directory Manager'
    password = 'Good2Great+'
    base_dn = 'cn=groups,cn=accounts,dc=icm,dc=corp'
    group_name = 'hardware'
    description = 'Hardware team group'
    try:
        conn = freeIPA_bind(server_address, username, password)
        if check_group_exists(conn, base_dn, group_name):
            print(f"Group '{group_name}' already exists in FreeIPA.")
        else:
            create_group(conn, base_dn, group_name, description)
        conn.unbind()
    except Exception as e:
        src.logger.logger.error(f"Failed to connect to FreeIPA server: {e}")