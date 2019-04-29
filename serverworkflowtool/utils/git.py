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

from serverworkflowtool.utils.log import get_logger

ent_repo_rel_path = 'src/mongo/db/modules/enterprise'


def refresh_repos(ctx, branch):
    original_branch = checkout_branch(ctx, branch, silent=True)

    try:
        ctx.run(f'git pull --rebase origin {branch}')
        with ctx.cd(ent_repo_rel_path):
            ctx.run(f'git pull --rebase origin {branch}')

        get_logger().info(f'Pulled latest changes from {branch} branch')
    finally:
        checkout_branch(ctx, original_branch)


def checkout_branch(ctx, branch, silent=False):
    original_branch = cur_branch_name(ctx)
    ctx.run(f'git checkout {branch}')
    with ctx.cd(ent_repo_rel_path):
        ctx.run(f'git checkout {branch}')
    if not silent:
        get_logger().info(f'Checked out existing branch {branch}')

    return original_branch


def new_branch(ctx, branch):
    ctx.run(f'git checkout -B {branch}')
    with ctx.cd(ent_repo_rel_path):
        ctx.run(f'git checkout -B {branch}')
    get_logger().info(f'Created new branch {branch}')


def cur_branch_name(ctx):
    res = ctx.run('git rev-parse --abbrev-ref HEAD')
    return res.stdout.strip()
