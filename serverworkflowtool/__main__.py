# Copyright 2019 MongoDB Inc.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import logging
import sys

import pkg_resources

from invoke import Program, Collection

from serverworkflowtool import setupenv
from deprecated import tasks
from serverworkflowtool.config import Config
from serverworkflowtool.utils import get_logger


def run():
    invoke_config = {
        'run': {
            'hide': True  # Don't print stdout or stderr.
        },
        'NINJA_STATUS': '[%f/%t (%p) %es] '  # make the ninja output even nicer
    }

    ns = Collection.from_module(tasks, config=invoke_config)
    ns.add_collection(Collection.from_module(setupenv, name='setup', config=invoke_config))

    proj_info = pkg_resources.require("server_workflow_tool")[0]

    p = Program(
        binary='workflow',
        name=proj_info.project_name,
        namespace=ns,
        version=proj_info.version)

    p.parse_core(sys.argv[1:])

    if p.args.debug.value:
        get_logger(level=logging.DEBUG)
    else:
        get_logger(level=logging.INFO)

    c = Config()
    p.run()
    c.dump()


if __name__ == '__main__':
    run()
