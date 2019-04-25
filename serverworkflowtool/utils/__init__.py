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
import sys


def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance


_logger = None


def get_logger(level=None):
    global _logger

    if not _logger:
        logger = logging.getLogger('workflow')
        logger.setLevel(level)
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        stdout = logging.StreamHandler(sys.stdout)
        stdout.setFormatter(formatter)
        logger.addHandler(stdout)
        _logger = logger
    return _logger


def instruction(msg):
    return f'\033[92m{msg}\033[0m'


def bold(msg):
    return f'\n\033[1m{msg}\033[0m'
