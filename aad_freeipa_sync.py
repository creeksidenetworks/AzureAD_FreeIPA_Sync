#!/usr/bin/env python
# Azure AD user/group FreeIPA sync utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import sys
import time
import argparse
import textwrap
import json
# Import functions from src/aad.py
import src.aad
import src.logger
import src.freeIPA
import src.configure
import src.sync_user

from src.sendmail import send_email
from datetime import datetime

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

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Sync Azure AD users and groups to FreeIPA.')
    parser.add_argument('--config', required=True, help='Path to the configuration file')

    # Check if the configuration file is provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    else:
        args = parser.parse_args()

    # read and interpret the configuration file
    config = src.configure.Config(args.config)

    # prepare logger
    log_dir = config.get('logging', 'path')
    src.logger.logger = src.logger.get_logger(log_dir)

    # get the Azure AD access token

    access_token = src.aad.get_aad_access_token(
        token_cache_file    = config.get('azure_ad', 'token_cache'),
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
        except Exception as e:
            src.logger.logger.error(f"An error occurred: {e}")

        break
        # Wait for 5 minutes before running again
        time.sleep(int(config.get('sync', 'interval')))

if __name__ == "__main__":
    main()

