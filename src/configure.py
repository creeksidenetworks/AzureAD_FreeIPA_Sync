# Azure AD user/group FreeIPA sync utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import os
import json
import configparser

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    MANDATORY_SECTIONS = ['azure_ad', 'freeipa', 'sync', 'mail', 'logging']
    MANDATORY_KEYS = {
        'azure_ad': ['client_id', 'client_secret', 'tenant_id', 'scope', 'token_cache'],
        'freeipa': ['server', 'user', 'password', 'basedn'],
        'sync': ['interval'],
        'mail': ['server', 'port', 'user', 'password'],
        'logging': ['level']
    }

    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.config = configparser.ConfigParser()
        self.config_dict = {}

        self.read_config()
        self.validate_config()

    def read_config(self):
        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file_path}")

        self.config.read(self.config_file_path)

        for section in self.config.sections():
            self.config_dict[section] = {}
            for key, value in self.config.items(section):
                self.config_dict[section][key] = value.strip('\'"')  # Remove quotes if present

    def validate_config(self):
        for section in self.MANDATORY_SECTIONS:
            if section not in self.config_dict:
                raise ConfigError(f"Mandatory section '{section}' is missing in the configuration file.")
            for key in self.MANDATORY_KEYS[section]:
                if key not in self.config_dict[section]:
                    raise ConfigError(f"Mandatory key '{key}' is missing in section '{section}'.")

    def get(self, section, key):
        return self.config_dict.get(section, {}).get(key)

# Example usage
if __name__ == "__main__":
    config_file_path = '/Users/jtong/python/aad_sync/cfg/aad_sync.conf'
    try:
        config = Config(config_file_path)
        print(json.dumps(config.config_dict, indent=4))
    except (FileNotFoundError, ConfigError) as e:
        print(f"Configuration error: {e}")