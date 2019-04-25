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
import pathlib
import tempfile
import unittest
from unittest import mock

from serverworkflowtool.config import Config, _ConfigImpl


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_config_path = Config().CONFIG_FILE

    def tearDown(self) -> None:
        Config.CONFIG_FILE = self.original_config_path

    def mock_setup_jira_credentials(self):
        self.jira_user = 'new_jira_user'
        self.jira_pwd = 'new_jira_pwd'

    @mock.patch.object(_ConfigImpl, '_setup_jira_credentials', mock_setup_jira_credentials)
    def test_pickle(self):
        with tempfile.NamedTemporaryFile('wb') as temp_file:
            _ConfigImpl.CONFIG_FILE = pathlib.Path(temp_file.name)

            old_config = Config()
            old_config.git_branches = ['server1', 'server2']
            old_config.jira_user = 'old_jira_user'
            old_config.jira_pwd = 'old_jira_pwd'
            old_config.dump()

            # Remove the singleton.
            _ConfigImpl.instance = None

            new_config = Config()
            self.assertListEqual(new_config.git_branches, old_config.git_branches)
            self.assertEqual(new_config.jira_user, 'new_jira_user')
            self.assertEqual(new_config.jira_pwd, 'new_jira_pwd')
