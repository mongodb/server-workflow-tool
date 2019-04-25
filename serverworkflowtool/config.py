#  Copyright 2019 MongoDB Inc.
#
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.
import getpass
import os
import pathlib
import pickle

import jira
import keyring
import invoke.exceptions

# Constants
from serverworkflowtool.utils import get_logger, instruction

HOME = pathlib.Path.home()
OPT = pathlib.Path('/opt')
CONFIG_FILE = HOME / '.config' / 'server-workflow-tool' / 'config.pickle'

EVG_CONFIG_FILE = HOME / '.evergreen.yml'
SSH_KEY_FILE = HOME / '.ssh' / 'id_rsa'

JIRA_URL = 'https://jira.mongodb.org'
GITHUB_SSH_HELP_URL = ('https://help.github.com/articles/'
                       'generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/#platform-mac')


class RepoConfig:
    def __init__(self, remote, local):
        self.remote = remote
        self.local = local


REQUIRED_REPOS = [
    RepoConfig('git@github.com:mongodb/mongo.git', 'mongo'),
    RepoConfig('git@github.com:10gen/mongo-enterprise-modules', 'mongo/src/mongo/db/modules/'),
    RepoConfig('git@github.com:10gen/kernel-tools.git', 'kernel-tools')
]


class _ConfigImpl(object):
    instance = None

    def __init__(self):
        """
        Please make sure you copy all instance attributes defined in __init__ to __setstate__.
        """
        self.git_branches = []

        self._username = None

        self._jira = None
        self._jira_pwd = None
        self._sudo_pwd = None

    def __getstate__(self):
        d = self.__dict__.copy()

        # Remove sensitive and unnecessary info.
        d['_jira_pwd'] = None
        d['_jira'] = None
        d['_sudo_pwd'] = None

        return d

    def __setstate__(self, state):
        # Create instance variables here instead of in __init__
        # because pickle will not add ones from __init__ to __dict__
        self.git_branches = []

        self._username = None

        self._jira = None
        self._jira_pwd = None
        self._sudo_pwd = None

        # Restore instance attributes.
        self.__dict__.update(state)

    def reset_jira_credentials(self):
        """
        Reset Jira credentials; for when the user accidentally entered the wrong information.
        :return:
        """
        if self.username is not None:
            self._username = None
            self._jira_pwd = None
            keyring.delete_password(JIRA_URL, self.username)
        else:
            get_logger().warning('Attempting to delete Jira password without a username')

    def get_sudo_pwd(self, ctx):
        if not self._sudo_pwd:
            while True:
                sudo_pwd = getpass.getpass(prompt='Please enter your sudo password: ')

                try:
                    # Check if this password works
                    ctx.sudo('ls', warn=False, hide='both', password=sudo_pwd)
                except invoke.exceptions.AuthFailure as e:
                    get_logger().error(str(e))
                    continue

                self._sudo_pwd = sudo_pwd
                break

        return self._sudo_pwd

    @property
    def jira_pwd(self):
        if not self._jira_pwd:
            jira_pwd = keyring.get_password(JIRA_URL, self.username)
            if not jira_pwd:
                jira_pwd = getpass.getpass(prompt=instruction('Please enter your Jira password: '))
            keyring.set_password(JIRA_URL, self.username, jira_pwd)
            self._jira_pwd = jira_pwd
        return self._jira_pwd

    @property
    def username(self):
        if not self._username:
            self._username = input(
                instruction('Please enter your Jira username (firstname.lastname): '))
        return self._username

    @property
    def jira(self):
        """
        lazily get a jira client.
        """
        if not self._jira:
            while True:
                try:
                    _jira = jira.JIRA(
                        options={'server': JIRA_URL},
                        basic_auth=(self.username, self.jira_pwd),
                        validate=True,
                        logging=False,
                        max_retries=3,
                        timeout=5,  # I think the unit is seconds.
                    )
                    if _jira:
                        self._jira = _jira
                        break
                except jira.exceptions.JIRAError as e:
                    get_logger().warning(
                        'Failed to login to Jira. Please re-enter your username and password. '
                        'If the failure persists, please login to Jira manually in a browser. '
                        'If that still doesn\'t work, seek help in #asdf')
                    get_logger().debug(e)
                    self.reset_jira_credentials()
                    # TODO: slack channel.

        return self._jira

    def dump(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(str(CONFIG_FILE), 'wb') as fh:
            pickle.dump(
                self,
                fh,
                protocol=pickle.HIGHEST_PROTOCOL,  # Use protocol version 4.
                fix_imports=False  # Don't support Python 2.
            )

    @staticmethod
    def load():
        if CONFIG_FILE.exists():
            with open(str(CONFIG_FILE), 'rb') as fh:
                try:
                    return pickle.load(fh, fix_imports=False)
                except (EOFError, KeyError, TypeError, AttributeError) as e:
                    get_logger().error('%s: %s', type(e), str(e))

        get_logger().warning('Could not read config file at %s, using empty config '
                             'as fallback', str(CONFIG_FILE))
        return _ConfigImpl()


# Singleton _Config object
def Config():
    if _ConfigImpl.instance is None:
        _ConfigImpl.instance = _ConfigImpl.load()

    return _ConfigImpl.instance
