# AzureAD_FreeIPA_Sync

## Description
A utility to sync Azure AD users and groups with FreeIPA.

## Usage
1. Prepare a config.ini file with following details

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
password = <default password>

[sync]
interval = 300

[mail]
recipients = <email recipients seperated by comma>
server = smtp.office365.com
port = 587
user = <your smtp account user namae>
password = <smtp password>

[logging]
level = INFO

2. Run the sync script:

python add_freeipa_sync.py --config <path to your config.ini file>
