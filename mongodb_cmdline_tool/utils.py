import os
import pathlib
import sys

import yaml

config_path = pathlib.Path.home() / '.config' / 'mongodb-cmdline-tool' / 'config'


def print_bold(msg):
    if sys.stdout.isatty():
        print(format_bold(msg))
    else:
        print(msg)


def format_bold(msg):
    return f'\n\033[1m{msg}\033[0m'


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_jira_pwd():
    if not os.path.isfile(config_path):
        return None

    with open(config_path) as config_file:
        config = yaml.load(config_file)
        return config['jira_pwd']


def save_jira_pwd(c, pwd):
    print(f'[INFO] Because of an issue with keyring, the Jira password is stored in a config file at the moment'
          f' at {config_path}. (For detail on keyring issue, see https://github.com/jaraco/keyring/issues/219)')

    with c.cd(str(pathlib.Path.home())):
        c.run('mkdir -p .config')

    with open(config_path, 'w') as config_file:
        config = {'jira_pwd': pwd}
        config_file.write(yaml.dump(config))
