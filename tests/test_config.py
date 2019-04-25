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

import tempfile
import unittest

from serverworkflowtool.config import Config


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_config_path = Config.config_file

    def tearDown(self) -> None:
        Config.config_file = self.original_config_path

    def test_pickle(self):
        with tempfile.NamedTemporaryFile('wb') as temp_file:
            Config.config_file = temp_file.name

            old_config = Config()
            old_config.branches = ['server1', 'server2']

            old_config.dump()

            new_config = old_config.load()
            self.assertListEqual(new_config.branches, old_config.branches)
