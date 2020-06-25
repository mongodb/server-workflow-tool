import sys
import os.path as path
import urllib.parse as urlparse
import importlib
import json
import os
import subprocess
import psutil
from argparse import ArgumentParser


def set_password(args):
    os.chdir(args.generator_path)
    sys.path.append(args.generator_path)
    tokengen = importlib.import_module('jira-token-gen')

    server_split = urlparse.urlparse(tokengen.access_token_url)
    server = urlparse.urlunparse((server_split.scheme, server_split.netloc, "", "", "", ""))
                                    
    password = {'access_token': tokengen.access_token['oauth_token'], 'access_token_secret': tokengen.access_token['oauth_token_secret']}
    user = os.getenv('JIRA_USERNAME')

    if not "gnome-keyring-daemon" in (p.name() for p in psutil.process_iter()):
        subprocess.run(["gnome-keyring-daemon", "--unlock"], input="password", text=True)
    import keyring
    keyring.set_password(server, user, json.dumps(password))
    print("Password set in keyring for server: {}, user: {}".format(server, user))


def create_cr(args):
    if not "gnome-keyring-daemon" in (p.name() for p in psutil.process_iter()):
        subprocess.run(["gnome-keyring-daemon", "--unlock"], input="password", text=True)

    sys.path.append(os.path.expanduser(os.path.join("~", "kernel-tools", "codereview")))
    upload = importlib.import_module('upload')
    upload.RealMain(["--check-clang-format", "--check-eslint", "--jira_user={}".format(os.getenv('JIRA_USERNAME'))])


if __name__ == '__main__':
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title="subcommands")
    pw_command = subparsers.add_parser("set-password", help="get a JIRA oauth token and store in the keyring")
    pw_command.set_defaults(func=set_password)
    pw_command.add_argument("generator_path", metavar="generator-path", help="path to the iteng-jira-repo")

    subparsers.add_parser("create-cr", help="open a CR").set_defaults(func=create_cr)
    args = parser.parse_args()
    args.func(args)
