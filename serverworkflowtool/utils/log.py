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


def actionable(msg):
    """
    Make instructions to actionable items green so they stand out from generic logging.
    """
    return f'\033[92m{msg}\033[0m'


def log_func(func, human_name):
    grey = lambda msg: f'\033[90m{msg}\033[0m'
    get_logger().info(grey('    ----- Starting Task: %s -----'), human_name)
    retval = func()
    get_logger().info(grey('    ----- Finished Task: %s -----'), human_name)
    get_logger().info('')
    get_logger().info('')

    return retval


def log_multiline(log_func, lines):
    for line in lines:
        log_func(line)


def req_input(msg):
    return input(actionable(msg))
