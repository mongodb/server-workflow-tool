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
import io
import re
import urllib.parse
import webbrowser

from invoke import task

import serverworkflowtool.utils.git as git
import serverworkflowtool.helpers as helpers

from serverworkflowtool import config
from serverworkflowtool.utils import jira, InvalidConfigError, log
from serverworkflowtool.utils.log import get_logger, actionable, req_input


@task(aliases=['a', 'start', 'switch'], positional=['ticket_number'], optional=['base_branch', 'project'])
def anew(ctx, ticket_number, project='server', base_branch='master'):
    """
    Step 0: Start a ticket or continue working on an existing ticket.

    A git branch is created for every Jira ticket and there is a one-to-one correspondence. If you need to
    work on two pieces of the same Jira ticket concurrently and have them reviewed separately, consider
    filing another ticket and linking it with the original ticket. This way, more information can be captured in
    Jira for future reference.

    :param ticket_number: Digits of the Jira ticket.
    :param project: Jira project. Default: server.
    :param base_branch: The base branch of this ticket. Default: master
    """
    helpers.check_mongo_repo_root()

    try:
        ticket_number = int(ticket_number)
    except ValueError:
        get_logger().critical('Ticket number must be an integer, got "%"', ticket_number)
        raise InvalidConfigError()

    branch_name = f'{project}-{ticket_number}'

    # This is an in-progress ticket.
    if branch_name in config.Config().in_progress_tickets:
        git.checkout_branch(ctx, branch_name)

    # Starting a new ticket.
    else:
        git.refresh_repos(ctx, base_branch)
        git.new_branch(ctx, branch_name)

        issue = jira.transition_ticket(
            f'{branch_name.upper()}',
            from_status='Open',
            transition_name='Start Progress'
        )

        conf = config.TicketConfig()
        conf.base_branch = base_branch
        if issue:
            conf.ticket_summary = issue.summary
        else:
            conf.ticket_summary = branch_name.upper()

        config.Config().in_progress_tickets[branch_name] = conf


@task(aliases=['c'])
def commit(ctx):
    """
    Step 2: Format code and commit changes to existing files; please manually `git add` new files
    """
    helpers.check_mongo_repo_root()
    raw_commit_msg = input('Please enter your commit message (without ticket number): ')

    # Format code before committing.
    helpers.format_code(ctx)

    commit_info = config.CommitInfo()

    def do_commit(repo):
        has_changes = ctx.run('git diff HEAD').stdout.strip()
        if has_changes:
            branch = git.cur_branch_name(ctx)
            ctx.run('git add -u', echo=True, hide=False)
            ctx.run(f'git commit -m "{branch.upper()} {raw_commit_msg}"', echo=True, hide=False)
            commit_hash = ctx.run('git rev-parse --verify HEAD').stdout.strip()
            if repo == 'community':
                commit_info.community = commit_hash
            elif repo == 'enterprise':
                commit_info.enterprise = commit_hash
            else:
                raise ValueError('Unknown repo type %s', repo)
        else:
            get_logger().info('No changes found in repo: %s', repo)

    try:
        do_commit('community')
        with ctx.cd(git.ent_repo_rel_path):
            do_commit('enterprise')
    finally:
        if not commit_info.is_empty():
            ticket_conf = helpers.get_ticket_conf(ctx)
            ticket_conf.commits.append(commit_info)


@task(aliases='p', optional=['finalize'])
def patch(ctx, finalize='yes'):
    """
    Step 3: Run a patch build in Evergreen CI.

    :param finalize: pass in any falsy value to avoid kicking off the patch build immediately.
    """
    helpers.check_mongo_repo_root()

    ticket_conf = helpers.get_ticket_conf(ctx)

    if not ticket_conf.commits:
        get_logger().warning('Did not find any commits on this branch. Please make sure you run `commit` '
                             'before `patch`')

    # Use the commit message from the latest commit as the patch build description.
    commit_msg = ctx.run('git log -1 --pretty=%B').stdout.strip()
    cmd = f'evergreen patch --alias required --description "{commit_msg}" --yes'
    if finalize == 'yes':
        # Any other value specified through the commandline is considered falsy.
        cmd += ' --finalize'
    res = ctx.run(cmd, hide=False, echo=True)

    # Sketchy regex parsing of the output of "evergreen patch"
    evg_url = re.search("Build : (.*)", res.stdout, re.MULTILINE).group(1)
    patch_id = evg_url.split('/')[-1]

    with ctx.cd(git.ent_repo_rel_path):
        ctx.run(f'evergreen patch-set-module --id {patch_id} --module enterprise --yes', hide=False, echo=True)

    ticket_conf = helpers.get_ticket_conf(ctx)
    ticket_conf.patch_ids.append(patch_id)

    if finalize != 'yes':
        # Point the user to the patch build URL if finalize is false.
        webbrowser.open(evg_url)
    else:
        get_logger().info('Patch build starting...')
        get_logger().url(f'Patch web page URL: {evg_url}')


@task(aliases='r')
def review(ctx):
    """
    Step 4: Open a new code review (CR) or put up a new patch to an existing code review.
    """
    helpers.check_mongo_repo_root()

    ticket_conf = helpers.get_ticket_conf(ctx)

    if not ticket_conf.commits:
        get_logger().warning('Did not find any commits on this branch. Please make sure you run `commit` '
                             'before `review`')

    with ctx.prefix(helpers.virtualenv):
        def upload(existing_cr):
            has_changes = ctx.run(f'git diff {ticket_conf.base_branch}').stdout.strip()
            if not has_changes:
                cwd = ctx.run('pwd').stdout.strip()
                get_logger().info(f'There are no changes in {cwd}, skipping code review')
                return

            cmd = f'python {str(config.UPLOAD_PY)} --rev {ticket_conf.base_branch}...'  # Yes three dots.
            cmd += ' --nojira -y --git_similarity 90 --check-clang-format --check-eslint'

            if existing_cr is not None:
                # Continue an existing CR.
                cmd += f' -i {existing_cr}'
            else:
                # Start a new CR.
                commit_msg = ctx.run('git log -1 --pretty=%B').stdout.strip()
                cr_title = input(f'Please enter the title for this code review (without the ticket number). '
                                 f'Default: {commit_msg}')
                if not cr_title:
                    cr_title = commit_msg
                else:
                    # Add the ticket number to the description.
                    cr_title = f'{git.cur_branch_name(ctx).upper()} {commit_msg}'

                cmd += f' -t "{cr_title}"'

            get_logger().info('Opening browser to authenticate with OAuth2... ')
            # Simulate some newline inputs to get the browser to open.
            sim_stdin = io.StringIO(initial_value='\n\n')
            res = ctx.run(cmd, in_stream=sim_stdin)

            if existing_cr is None:
                cr_url = re.search('Issue created. URL: (.*)', res.stdout.strip()).group(1)
                cr_issue_number = cr_url.split('/')[-1]
                get_logger().info(f'Code review created: {cr_url}')

                ticket_number = git.cur_branch_name(ctx).upper()
                jira.transition_ticket(ticket_number, 'In Progress', 'Start Code Review')

                jira.add_comment(
                    ticket_number,
                    f'Code Review: {cr_url}',
                    visibility={'type': 'role', 'value': 'Developers'}
                )

                return cr_issue_number
            else:
                get_logger().info(f'Code review updated')
                return existing_cr

        ticket_conf.cr_info.community = upload(ticket_conf.cr_info.community)
        with ctx.cd(git.ent_repo_rel_path):
            ticket_conf.cr_info.enterprise = upload(ticket_conf.cr_info.enterprise)

        note = actionable('Note:')
        get_logger().info('')
        get_logger().info(f'{note} Step 3 (patch build) and Step 4 (code review) may need to be repeated to address')
        get_logger().info('      CR feedback or to validate new changes. Please consult with your mentor on the exact')
        get_logger().info('      workflow for your team.')
        get_logger().info('')
        req_input('Press any key to open the code review app...')
        webbrowser.open('https://mongodbcr.appspot.com')


@task(aliases=['z'])
def zzz(ctx):
    """
    Step 6: Cleanup. Remove local branches and close Jira ticket
    :param ctx:
    :return:
    """
    helpers.check_mongo_repo_root()
    ticket_conf = helpers.get_ticket_conf(ctx)
    feature_branch = git.cur_branch_name(ctx)
    base_branch = ticket_conf.base_branch

    actionable(f'Congrats on completing {feature_branch.upper()}! '
               f'Press any key to remove local branches and close the Jira ticket')

    config.Config().in_progress_tickets.pop(feature_branch)

    ctx.run(f'git checkout {base_branch}')
    ctx.run(f'git branch --delete {feature_branch}')

    jira.transition_ticket(
        feature_branch.upper(),
        'In Code review',
        'Close Issue'
    )


@task(aliases=['s', 'push'])
def ship(ctx):
    """
    Step 5: Provide instructions on pushing your changes to master.

    Also add the URL of the latest patch build to the Jira ticket.
    """
    helpers.check_mongo_repo_root()
    ticket_conf = helpers.get_ticket_conf(ctx)
    cur_branch = git.cur_branch_name(ctx)

    if ticket_conf.patch_ids:
        jira.add_comment(
            cur_branch.upper(),
            f'Patch Build: {urllib.parse.urljoin(config.EVG_PATCH_URL_BASE, ticket_conf.patch_ids[-1])}',
            visibility={'type': 'role', 'value': 'Developers'}
        )
    else:
        get_logger().warning('No patch builds were created for this ticket, not adding patch build URL to Jira')

    # This will implicitly check for uncommitted changes on the feature branch
    git.refresh_repos(ctx, ticket_conf.base_branch)

    lines = [
        actionable('Please run the following commands to push your changes to the upstream MongoDB repository:'),
        '',
        f'    git rebase --interactive {ticket_conf.base_branch}',
        f'    git checkout {ticket_conf.base_branch}',
        f'    git merge --ff-only {cur_branch}',
        f'    git push origin {ticket_conf.base_branch} --dry-run',
        f'    git push origin {ticket_conf.base_branch}',
        '',
        'As part of `git rebase --interactive`, you should squash your local commits into one commit. Please refer to',
        'this guide for an intro to interactive rebase: https://git-scm.com/docs/git-rebase#_interactive_mode',
        '',
        'If you encounter errors during any of the above steps, please ask your mentor for advice.',
        '',
        'Finally, when you\'ve pushed your changes, you can run `workflow zzz'
    ]
    log.log_multiline(get_logger().info, lines)


@task
def code(ctx):
    """
    Step 1: 💻 Write code. (Informational only, there's no need to run `workflow code`)️
    """
    print('https://github.com/mongodb/mongo/blob/master/src/mongo/idl/unittest.idl')
