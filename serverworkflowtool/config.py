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

import os
import pathlib
import pickle


class Config(object):

    # Constants
    HOME = pathlib.Path.home()
    OPT = pathlib.Path('/opt')
    CONFIG_FILE = HOME / '.config' / 'server-workflow-tool' / 'config.pickle'

    def __init__(self):
        self.branches = []
        self.jira_user = None
        self.jira_pwd = None

    def __getstate__(self):
        # Remove sensitive info.
        d = self.__dict__.copy()

        del d['jira_pwd']
        return d

    def __setstate__(self, state):
        # Restore instance attributes.
        self.__dict__.update(state)

        self.jira_pwd = None

    def dump(self):
        try:
            os.mkdir(os.path.dirname(self.CONFIG_FILE))
        except FileExistsError:
            # Directory exists.
            pass

        with open(self.CONFIG_FILE, 'wb') as fh:
            pickle.dump(
                self,
                fh,
                protocol=pickle.HIGHEST_PROTOCOL,  # Use protocol version 4.
                fix_imports=False  # Don't support Python 2.
            )

    @staticmethod
    def load():
        with open(Config.CONFIG_FILE, 'rb') as fh:
            return pickle.load(fh)
