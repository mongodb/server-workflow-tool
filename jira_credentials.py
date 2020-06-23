import sys
import keyring
import urlparse
import json
import os
import subprocess

sys.path.append("iteng-jira-oauth")
os.chdir("iteng-jira-oauth")
import __builtin__
# Line below is due to a bug in jira-token-gen
__builtin__.input = __builtin__.raw_input
tokengen = __import__('jira-token-gen', globals(), locals(), [], -1)

server_split = urlparse.urlparse(tokengen.access_token_url)
server = urlparse.urlunparse((server_split.scheme, server_split.netloc, "", "", "", ""))
                                 
password = {'access_token': tokengen.access_token['oauth_token'], 'access_token_secret': tokengen.access_token['oauth_token_secret']}
user = os.getenv('JIRA_USERNAME')
keyring.set_password(server, user, json.dumps(password))
