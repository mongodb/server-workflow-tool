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
import pathlib
import pickle

import jira
import keyring
import keyring.errors
import invoke.exceptions

from serverworkflowtool.utils.log import get_logger, actionable

# These configs may need to be updated periodically.
CLANG_FORMAT_URL = 'https://s3.amazonaws.com/boxes.10gen.com/build/clang%2Bllvm-3.8.0-x86_64-apple-darwin.tar.xz'
ESLINT_URL = 'https://s3.amazonaws.com/boxes.10gen.com/build/eslint-2.3.0-darwin.tar.gz'

# Constants
HOME = pathlib.Path.home()
USER = getpass.getuser()
OPT = pathlib.Path('/opt')

# Parent directory of all git repositories.
REPO_ROOT = HOME / 'mongodb'

CONFIG_DIR = HOME / '.config' / 'server-workflow-tool'
CONFIG_FILE = CONFIG_DIR / 'config.pickle'

EVG_CONFIG_FILE = HOME / '.evergreen.yml'
SSH_KEY_FILE = HOME / '.ssh' / 'id_rsa'

EVG_PATCH_URL_BASE = 'https://evergreen.mongodb.com/version'
JIRA_URL = 'https://jira.mongodb.org'
GITHUB_SSH_HELP_URL = ('https://help.github.com/articles/'
                       'generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/#platform-mac')

UPLOAD_PY = REPO_ROOT / 'kernel-tools' / 'codereview' / 'upload.py'


class DownloadConfig:
    """
    Config for any downloadable items.
    """

    def __init__(self, remote, relative_local=None, absolute_local=None):
        self.remote = remote

        # Only need at most one of the following.
        self.relative_local = relative_local
        self.absolute_local = absolute_local


# Paths are relative to root dir of all repos.
REQUIRED_REPOS = [
    DownloadConfig('git@github.com:mongodb/mongo.git', relative_local='mongo'),
    DownloadConfig('git@github.com:10gen/mongo-enterprise-modules',
                   relative_local='mongo/src/mongo/db/modules/enterprise'),
    DownloadConfig('git@github.com:RedBeard0531/mongo_module_ninja.git',
                   relative_local='mongo/src/mongo/db/modules/ninja'),
    DownloadConfig('git@github.com:10gen/kernel-tools.git', relative_local='kernel-tools'),
    DownloadConfig('git@github.com:10gen/employees.git', relative_local='scratch')
]


class CommitInfo(object):
    def __init__(self):
        """
        Define dummy instance attributes here to pacify static code analyzers. The __init__
        function is not called by pickle . Real values for attributes should be set in the
        __setstate__ method instead.
        """
        self.community = None
        self.enterprise = None

        self.__setstate__({})

    def __setstate__(self, state):
        self.community = None
        self.enterprise = None

        # Restore instance attributes.
        self.__dict__.update(state)

    def is_empty(self):
        return (self.community is None) and (self.enterprise is None)


class TicketConfig(object):
    def __init__(self):
        """
        Define dummy instance attributes here to pacify static code analyzers. The __init__
        function is not called by pickle . Real values for attributes should be set in the
        __setstate__ method instead.
        """
        self.base_branch = None
        self.ticket_summary = None
        self.cr_info = None
        self.patch_ids = None
        self.commits = None

        self.__setstate__({})

    def __setstate__(self, state):
        self.base_branch = None
        self.ticket_summary = None
        self.cr_info = CommitInfo()
        self.patch_ids = []
        self.commits = []

        # Restore instance attributes.
        self.__dict__.update(state)


class _ConfigImpl(object):
    instance = None

    def __init__(self):
        """
        Define dummy instance attributes here to pacify static code analyzers. The __init__
        function is not called by pickle . Real values for attributes should be set in the
        __setstate__ method instead.
        """
        self.in_progress_tickets = None

        self._username = None

        self._jira = None
        self._jira_pwd = None
        self._sudo_pwd = None

        self._version = None

        # Call __setstate__ to ensure atttributes are initialized correctly if _ConfigImpl is
        # created directly (i.e. not through pickle).
        self.__setstate__({})

    def __setstate__(self, state):
        # Create instance variables here instead of in __init__
        # because pickle will not add ones from __init__ to __dict__
        self.in_progress_tickets = {}

        self._username = None

        self._jira = None
        self._jira_pwd = None
        self._sudo_pwd = None

        # Default to version 1, this will be overridden by the value in the config file.
        self._version = 1

        # Restore instance attributes.
        self.__dict__.update(state)

    def __getstate__(self):
        d = self.__dict__.copy()

        # Remove sensitive and unnecessary info.
        d['_jira_pwd'] = None
        d['_jira'] = None
        d['_sudo_pwd'] = None

        return d

    def reset_jira_credentials(self):
        """
        Reset Jira credentials; for when the user accidentally entered the wrong information.
        :return:
        """
        if self.username is not None:
            self._username = None
            self._jira_pwd = None
            try:
                keyring.delete_password(JIRA_URL, self.username)
            except keyring.errors.PasswordDeleteError as e:
                get_logger().error(str(e))
        else:
            get_logger().warning('Attempting to delete Jira password without a username')

    def get_sudo_pwd(self, ctx):
        if not self._sudo_pwd:
            while True:
                sudo_pwd = getpass.getpass(prompt=actionable('Please enter your sudo password: '))

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
                jira_pwd = getpass.getpass(prompt=actionable('Please enter your Jira password: '))
            keyring.set_password(JIRA_URL, self.username, jira_pwd)
            self._jira_pwd = jira_pwd
        return self._jira_pwd

    @property
    def username(self):
        if not self._username:
            self._username = input(
                actionable('Please enter your Jira username (firstname.lastname): '))
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
                        'If that still doesn\'t work, seek help in #new-server-eng-help')
                    get_logger().debug(e)
                    self.reset_jira_credentials()

        return self._jira

    def dump(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

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
