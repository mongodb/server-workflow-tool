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

#
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.
import os.path

from invoke import task

from serverworkflowtool import config
from serverworkflowtool.utils import git as git, InvalidConfigError
from serverworkflowtool.utils.git import cur_branch_name
from serverworkflowtool.utils.log import get_logger

virtualenv = f'source {config.REPO_ROOT / "mongo" / "python3-venv" / "bin" / "activate"}'


def check_mongo_repo_root():
    if not os.path.isfile('SConstruct'):
        get_logger().critical('Please run this command from the root of the mongo repository')
        raise InvalidConfigError()


def get_ticket_conf(ctx):
    branch = cur_branch_name(ctx)
    ticket_conf = config.Config().in_progress_tickets.get(branch)
    if not ticket_conf:
        get_logger().critical('Unknown branch "%s". Please ensure the branch is created with the "start" command',
                              branch)
        raise InvalidConfigError()
    return ticket_conf


@task(aliases=['f'])
def format_code(ctx):
    """
    Format modified C++ and JavaScript code.

    Wrapper around `buildscripts/clang_format.py` and `buildscripts/eslint.py`. This command
    is invoked as part of `commit`.

    """
    check_mongo_repo_root()

    ticket_conf = get_ticket_conf(ctx)
    base_branch = ticket_conf.base_branch

    with ctx.prefix(virtualenv):
        modified_files = ctx.run(f'git diff --name-only {base_branch}')
        modified_js_files = [js_file for js_file in modified_files.stdout.strip().split('\n') if
                             js_file.endswith('.js')]

        # If there are no modified JS files, eslint will lint everything.
        if modified_js_files:
            ctx.run(f'python buildscripts/eslint.py fix {" ".join(modified_js_files)}', echo=True, hide=False)

        ctx.run(f'python buildscripts/clang_format.py format-my {base_branch}', echo=True, hide=False)


@task(aliases=['d'])
def delete_branch(ctx):
    """
    Delete the current branch on the community and enterprise repos.

    It's usually harmless to keep local branches around. But this command is available if you
    want to delete a branch for any reason.
    """
    check_mongo_repo_root()

    branch = cur_branch_name(ctx)
    ticket_conf = get_ticket_conf(ctx)

    def run():
        ctx.run(f'git checkout {ticket_conf.base_branch}')
        ctx.run(f'git branch --delete --force {branch}', echo=True, hide=False)

    run()
    with ctx.cd(git.ent_repo_rel_path):
        run()

    config.Config().in_progress_tickets.pop(branch)


@task
def upgrade(ctx):
    """
    [Experimental] Pull in the latest version of this tool. Does not work when installed through virtualenv.
    """
    ctx.run('python3 -m pip install --upgrade git+https://github.com/mongodb/server-workflow-tool.git')
