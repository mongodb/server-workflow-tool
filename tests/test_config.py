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

import logging
import os.path
import pathlib
import tempfile
import unittest
from unittest import mock

import serverworkflowtool.config as config
from serverworkflowtool.utils import get_logger


class ConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_logger(logging.INFO)

    def setUp(self) -> None:
        self.original_config_path = config.CONFIG_FILE

    def tearDown(self) -> None:
        config.CONFIG_FILE = self.original_config_path

    def test_pickle(self):
        with tempfile.TemporaryDirectory('wb') as temp_dir:
            temp_file = os.path.join(temp_dir, 'config.pickle')
            config.CONFIG_FILE = pathlib.Path(temp_file)

            old_config = config.Config()

            old_config.git_branches = ['server1', 'server2']
            old_config._username = 'dummy_user'
            old_config._jira_pwd = 'old_jira_pwd'
            old_config._sudo_pwd = 'old_sudo_pwd'
            old_config.dump()

            # Remove the singleton.
            config._ConfigImpl.instance = None

            new_config = config.Config()
            self.assertListEqual(new_config.git_branches, old_config.git_branches)
            self.assertEqual(new_config.username, old_config.username)

            # Passwords should not be persisted.
            self.assertEqual(new_config._jira_pwd, None)
            self.assertEqual(new_config._sudo_pwd, None)

            # Large objects should not be persisted.
            self.assertEqual(new_config._jira, None)
