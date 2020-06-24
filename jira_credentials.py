import sys
import os.path as path
import keyring
import urllib.parse as urlparse
import importlib
import json
import os
import subprocess

def set_password(generator_path):
    os.chdir(generator_path)
    sys.path.append(generator_path)
    tokengen = importlib.import_module('jira-token-gen')

    server_split = urlparse.urlparse(tokengen.access_token_url)
    server = urlparse.urlunparse((server_split.scheme, server_split.netloc, "", "", "", ""))
                                    
    password = {'access_token': tokengen.access_token['oauth_token'], 'access_token_secret': tokengen.access_token['oauth_token_secret']}
    print("access_token: {}, secret: {}".format(tokengen.access_token['oauth_token'], tokengen.access_token['oauth_token_secret']))

    user = os.getenv('JIRA_USERNAME')
    print("user: {}".format(user))

    keyring.set_password(server, user, json.dumps(password))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError("expected one argument")
    if not path.exists(sys.argv[1]):
        raise ValueError("path '{}' does not exist".format(sys.argv[1]))

    set_password(sys.argv[1])