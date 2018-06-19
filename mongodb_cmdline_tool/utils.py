import os
import pathlib
import sys

import keyring
import yaml

config_path = pathlib.Path.home() / '.config' / 'mongodb-cmdline-tool' / 'config'


def print_bold(msg):
    if sys.stdout.isatty():
        print(format_bold(msg))
    else:
        print(msg)


def format_bold(msg):
    return f'\n\033[1m{msg}\033[0m'


def get_jira_pwd():
    return keyring.get_password('jira', 'dummy_user')


def save_jira_pwd(c, pwd):
    keyring.set_password('jira', 'dummy_user', pwd)