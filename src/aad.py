#!/usr/bin/env python
# Azure AD user/group sync utility
# Copyright (c) 2023 Jackson Tong, Creekside Networks LLC.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os
import msal
import requests
from   ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE
import src.logger

# Authenticate to Azure AD
def get_aad_access_token(token_cache_file, tenant_id, client_id, client_secret, authority, scopes):
    cache = msal.SerializableTokenCache()
    if os.path.exists(token_cache_file):
        cache.deserialize(open(token_cache_file, 'r').read())

    authority = str(f"https://login.microsoftonline.com/{tenant_id}")
    #print(f"Authority: {authority}")
    #print(f"Client ID: {client_id}")
    #print(f"Client Secret: {client_secret}")
    #print(f"Scope: {scope}")

    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret, token_cache=cache)
    result = app.acquire_token_silent(scopes=scopes, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=scopes)
    if 'access_token' in result:
        src.logger.logger.info("Access token obtained successfully")
        with open(token_cache_file, 'w') as f:
            f.write(cache.serialize())
        return result['access_token']
    else:
        error_message = result.get('error_description', 'No error description available')
        src.logger.logger.error(f"Could not obtain access token: {error_message}")
        raise Exception(f"Could not obtain access token: {error_message}")

# Get users from Azure AD
def get_aad_users(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    users = []
    url = 'https://graph.microsoft.com/v1.0/users'
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            src.logger.logger.error(f"Failed to retrieve users: {response.status_code} - {response.text}")
            break
        data = response.json()
        users.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    src.logger.logger.info(f"Retrieved {len(users)} users from Azure AD")
    return users

# Get groups from Azure AD
def get_aad_groups(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    groups = []
    url = 'https://graph.microsoft.com/v1.0/groups'
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            src.logger.logger.error(f"Failed to retrieve groups: {response.status_code} - {response.text}")
            break
        data = response.json()
        groups.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    src.logger.logger.info(f"Retrieved {len(groups)} groups from Azure AD")
    return groups

# Get group members from Azure AD
def get_aad_group_members(access_token, group_id):
    headers = {'Authorization': f'Bearer {access_token}'}
    members = []
    url = f'https://graph.microsoft.com/v1.0/groups/{group_id}/members'
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            src.logger.logger.error(f"Failed to retrieve group members: {response.status_code} - {response.text}")
            break
        data = response.json()
        members.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    return members

def get_aad_group_member_by_name(access_token, group_name):

    # Get group ID by name
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'https://graph.microsoft.com/v1.0/groups?$filter=displayName eq \'{group_name}\''
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        src.logger.logger.error(f"Failed to retrieve group ID named [{group_name}]: {response.status_code} - {response.text}")
        return None
    data = response.json()
    if 'value' in data and len(data['value']) > 0:
        group_id = data['value'][0]['id']
    else:
        return None

    members = []
    url = f'https://graph.microsoft.com/v1.0/groups/{group_id}/members'
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            src.logger.logger.error(f"Failed to retrieve group members: {response.status_code} - {response.text}")
            break
        data = response.json()
        members.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    return members