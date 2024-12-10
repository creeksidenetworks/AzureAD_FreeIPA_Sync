#!/usr/bin/env python
# Azure AD user/group FreeIPA sync utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.


import os
import time
# Import functions from src/aad.py
import src.aad
import src.logger
import src.freeIPA
import src.configure
import src.sync_user

from src.sendmail import send_email
from datetime import datetime

sample_config = """
[azure_ad]
client_id = <azure application client id>
client_secret = <azure application client id>
tenant_id = <azure tenant id>
scope = https://graph.microsoft.com/.default
token_cache = .token_cache

[freeipa]
server = <freeipa server ip or hostname>
realm = <freeipa realm>
user = cn=directory manager
password = <directory manager password>
basedn = dc=<your dc1>,dc=<your dc2>

[newuser]
password = <new user default password>

[sync]
interval = <sync period>

[mail]
recipients = <email recipients, separate by comma>
server = smtp.office365.com
port = 587
user = <email account used to send>
password = <account password or application password>

[logging]
level = INFO        
"""

# main function
def main():

    # main scripts started here
    title = """
***************************************************************************
*                 Azure AD to FreeIPA Sync Utility v1.0                   *
*          (c) 2024-2024 Jackson Tong, Creekside Networks LLC             *
***************************************************************************

"""
    print(title)

    # read and interpret the configuration file
    root_dir = os.path.abspath(os.path.dirname(__file__))
    cfg_dir = os.path.join(root_dir, 'cfg')
    config_file_path = os.path.join(cfg_dir, 'aad_freeipa_sync.conf')

    if not os.path.exists(cfg_dir):
        os.makedirs(cfg_dir)
    
    if not os.path.exists(config_file_path):
        # dump a sample configuration file        
        with open(config_file_path, 'w') as config_file:
            config_file.write(sample_config)
        print(f"Sample configuration file created at {config_file_path}")
        print("Please edit the configuration file and run the script again.")
        exit(0)
    
    config = src.configure.Config(config_file_path)

    # prepare logger
    log_dir = os.path.join(root_dir, 'logs')
    src.logger.logger = src.logger.get_logger(log_dir)

    # get the Azure AD access token
    token_cache_file = os.path.join(cfg_dir, config.get('azure_ad', 'token_cache'))

    access_token = src.aad.get_aad_access_token(
        token_cache_file    = token_cache_file,
        tenant_id           = config.get('azure_ad', 'tenant_id'),
        client_id           = config.get('azure_ad', 'client_id'),
        client_secret       = config.get('azure_ad', 'client_secret'),
        authority           = config.get('azure_ad', 'authority'),
        scopes              = [config.get('azure_ad', 'scope')]
    )

    while True:
        try:
            new_users = src.sync_user.sync_users(config, access_token)
            if new_users:
                report = "New Users Created in FreeIPA:\n\n"
                report += "{:<12} {:<20} {:<40} {:<10}\n".format("UIDNumber", "UID", "Email", "Password")
                report += "-" * 84 + "\n"
                for user in new_users:
                    report += "{:<12} {:<20} {:<40} {:<10}\n".format(user['uidNumber'], user['uid'], user['mail'], user['password'])
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                print (report)
                send_email(
                    server = config.get('mail', 'server'), 
                    port = config.get('mail', 'port'), 
                    user = config.get('mail', 'user'), 
                    password = config.get('mail', 'password'), 
                    subject = f"AAD to FreeIPA Sync Report - {timestamp}",
                    body   = report,
                    recipients = config.get('mail', 'recipients').split(','))
            else:
                src.logger.logger.info("No new users found.")
        except Exception as e:
            src.logger.logger.error(f"An error occurred: {e}")

        # rotate the log file
        src.logger.rotate_logger()

        # Wait for 5 minutes before running again
        time.sleep(int(config.get('sync', 'interval')))

if __name__ == "__main__":
    main()

