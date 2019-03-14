import os
import pathlib
import re
import sys
import webbrowser

import jira
import yaml
from invoke import task

from mongodb_cmdline_tool.utils import get_jira_pwd, print_bold

jira_username = None
jira_password = None
jira_cli = None

kHome = pathlib.Path.home()

kPackageDir = kHome / '.config' / 'server-workflow-tool'
kScriptDir = kPackageDir / 'scripts'

def get_jira():
    global jira_cli
    if not jira_cli:
        try:
            jira_cli = jira.JIRA(
                options={'server': 'https://jira.mongodb.org'},
                basic_auth=(jira_username, jira_password),
                validate=True,
                logging=False
            )
        except jira.exceptions.JIRAError as e:
            if e.status_code == '403' or e.status_code == 403:
                print('CAPTCHA required, please log out and log back into Jira')
                return None

    print_bold('Updating ticket in Jira. Please wait...')
    return jira_cli


def init(c):
    global jira_username
    global jira_password

    if jira_username:
        return

    # Use the Evergreen username for Jira as well.
    with open(pathlib.Path.home() / '.evergreen.yml') as evg_file:
        evg_config = yaml.load(evg_file)
        jira_username = evg_config['user']
    jira_password = get_jira_pwd()


def _strip_proj(ticket_number):
    match = re.search(r'[0-9]+', ticket_number)
    if not match:
        print(f'[ERROR] {ticket_number} is not a valid ticket number')
        sys.exit(1)
    return match.group(0)


def _get_ticket_numbers(c):
    """Get the ticket numbers from the commit and the branch."""
    branch = c.run('git rev-parse --abbrev-ref HEAD', hide=True).stdout
    ticket_number = _strip_proj(branch)
    commit_msg = c.run('git log --oneline -1 --pretty=%s', hide=True).stdout
    commit_ticket_number = _strip_proj(commit_msg)
    return commit_ticket_number, ticket_number


def _load_cache(c):
    try:
        with open(str(kPackageDir / 'cache'), 'r') as cache_file:
            cache = yaml.load(cache_file)
            return cache or {}
    except IOError:
        # File doesn't exist.
        return {}


def _store_cache(c, cache_dict):
    with open(str(kPackageDir / 'cache'), 'w') as cache_file:
        yaml.dump(cache_dict, cache_file)


def _git_refresh(c, branch):
    old_branch = c.run('git rev-parse --abbrev-ref HEAD', hide=True).stdout
    c.run(f'git checkout {branch}', hide=True)
    c.run(f'git fetch origin {branch}')
    c.run(f'git rebase origin/{branch}', hide=True)
    c.run(f'git checkout {old_branch}', hide=True)


def _post_update_steps(c):
    """
    Additional steps to run after a git update.
    """
    pass


@task(aliases='n', positional=['ticket_number'], optional=['branch', 'project'])
def new(c, ticket_number, branch='master', project='server'):
    """
    Step 1: Create or switch to the branch for a ticket.

    :param ticket_number: Digits of the Jira ticket.
    :param branch: Base branch for this ticket. Default: master.
    :param project: Jira project. Default: server.
    """
    init(c)
    ticket_number = _strip_proj(ticket_number)

    project = project.lower()

    res = c.run(f'git rev-parse --verify {project}{ticket_number}', warn=True, hide=True)
    if res.return_code == 0:
        c.run(f'git checkout {project}{ticket_number}', hide='both')
    else:
        print_bold(f'Updating {branch} to latest and creating new branch: server{ticket_number}')
        c.run(f'git checkout {branch}')
        _git_refresh(c, branch)
        c.run(f'git checkout -B {project}{ticket_number}', hide='both')

        jirac = get_jira()
        if jirac:
            issue = jirac.issue(f'{project.upper()}-{ticket_number}')
            if issue.fields.status.id == '1':  # '1' = Open
                print_bold(f'Transitioning {project.upper()}-{ticket_number} '
                           f'in Jira to "In Progress"')
                jirac.transition_issue(issue, '4')  # '4' = Start Progress
            else:
                print_bold(f'{project.upper()}-{ticket_number} in Jira is not '
                           f'in "Open" status, not updating Jira')

    cache = _load_cache(c)
    if ticket_number not in cache:
        cache[ticket_number] = {}

    cache[ticket_number]['project'] = project
    _store_cache(c, cache)


@task(aliases='m', optional=['pull'])
def checkout_master(c, pull=False):
    """
    Checkout the master branch. Wrapper around "git checkout master"

    :param pull: fetch and rebase onto latest master on remote.
    """
    with c.cd(str(kHome / 'mongo')):
        c.run('git fetch origin master')
        c.run('git rebase origin/master')


@task(aliases='s')
def scons(c):
    """
    Step 2: [experimental] Check your code compiles, wrapper around "python buildscripts/scons.py".
    """
    init(c)
    num_cpus = os.cpu_count()
    c.run(f'ninja core -j{num_cpus}', pty=True)


@task(aliases='l', optional=['eslint'])
def lint(c, eslint=False):
    """
    Step 3: lint and format your code: Wrapper around clang_format and eslint.

    :param eslint: Run ESLint for JS files. Default: False.
    """
    init(c)
    with c.cd(str(kHome / 'mongo')):
        if eslint:
            c.run('python2 buildscripts/eslint.py fix')
        c.run('python2 buildscripts/clang_format.py format')


@task(aliases='c')
def commit(c):
    """
    Step 4: Wrapper around git commit to automatically add changes and fill in the ticket number
    in the commit message.
    """
    init(c)

    commit_num, branch_num = _get_ticket_numbers(c)

    cache = _load_cache(c)

    project = cache.get(branch_num, {}).get('project', 'server')

    c.run('git add -u')

    if project == 'server':
        c.run('git add src/')
        c.run('git add jstests/')

    if commit_num == branch_num:
        c.run('git commit --amend --no-edit --reset-author')
    else:
        raw_commit_msg = input('Please enter the commit message (without ticket number): ')
        c.run(f'git commit -m "{project.upper()}-{branch_num} {raw_commit_msg}"')

    print_bold('Committed local changes')


@task(aliases='r', optional=['new_cr', 'browser'])
def review(c, new_cr=False, browser=True):
    """
    Step 5: Put your code up for code review.

    :param new_cr: whether to create a new code review. Use it if you have multiple CRs for the
                   same ticket. (Default: False)
    :param browser: Set it to False if you're running this script in a ssh terminal.
    """
    init(c)
    commit_num, branch_num = _get_ticket_numbers(c)
    if commit_num != branch_num:
        print('[ERROR] Please commit your local changes before submitting them for review.')
        sys.exit(1)

    cache = _load_cache(c)
    if commit_num not in cache:
        cache[commit_num] = {}

    issue_number = cache[commit_num].get('cr', None)
    project = cache[commit_num].get('project', 'server')

    commit_msg = c.run('git log --oneline -1 --pretty=%s', hide=True).stdout.strip()

    cmd = f'python2 {kScriptDir / "upload.py"} --rev HEAD~1 --nojira -y '

    if project == 'server':
        cmd += '--git_similarity 90 --check-clang-format --check-eslint'

    if issue_number and not new_cr:
        cmd += f' -i {issue_number}'
    else:
        # New issue, add title.
        cmd += f' -t "{commit_msg}"'

    if not browser:
        cmd += ' --no_oauth2_webbrowser'

    print('Authenticating with OAuth2... If your browser did not open, press enter')
    res = c.run(cmd, hide='stdout')

    match = re.search('Issue created. URL: (.*)', res.stdout)
    if not match:
        print_bold(f'Please manually add a link of your codereview to: '
                   f'https://jira.mongodb.org/browse/{project.upper()}-{commit_num}')
        sys.exit(1)

    url = match.group(1)
    issue_number = url.split('/')[-1]

    if not issue_number:
        print('[ERROR] Something went wrong, no CR issue number was found in code review URL')
        sys.exit(1)

    jirac = get_jira()
    if jirac:
        ticket = get_jira().issue(f'{project.upper()}-{commit_num}')

        # Transition Ticket
        if ticket.fields.status.id == '3':  # '3' = In Progress.
            print_bold(
                f'Transitioning {project.upper()}-{branch_num} in Jira to "Start Code Review"')
            jirac.transition_issue(ticket, '761')  # '4' = Start Code Review

            # Add comment.
            get_jira().add_comment(
                ticket,
                f'CR: {url}',
                visibility={'type': 'role', 'value': 'Developers'}
            )
        else:
            print_bold(f'SERVER-{branch_num} in Jira is not in '
                        f'"In Progress" status, not updating Jira')

    cache[commit_num]['cr'] = issue_number

    _store_cache(c, cache)

    url = f'https://mongodbcr.appspot.com/{issue_number}'
    print_bold(f'Opening code review page: {url}')
    webbrowser.open(url)


@task(aliases='p', optional=['branch', 'finalize'])
def patch(c, branch='master', finalize=False):
    """
    Step 6: Run patch build in Evergreen.


    :param finalize: whether to finalize the patch build and have it run immediately.
                     (Default: False)
    :param branch: the base branch for the patch build. (Default: False)
    """
    init(c)
    temp_branch = 'patch-build-branch'
    feature_branch = c.run('git rev-parse --abbrev-ref HEAD', hide=True).stdout
    commit_msg = c.run('git log --oneline -1 --pretty=%s', hide=True).stdout.strip()

    commit_num, branch_num = _get_ticket_numbers(c)
    if commit_num != branch_num:
        print('[ERROR] Please commit your local changes before putting up a patch build.')
        sys.exit(1)

    try:
        _git_refresh(c, branch)

        c.run(f'git checkout -B {temp_branch}')
        res = c.run(f'git rebase {branch}', warn=True)
        if res.return_code != 0:
            print(f'[WARNING] {feature_branch} did not rebase cleanly. Please manually run '
                  f'"git rebase {branch}" and retry the patch build again')
            c.run('git rebase --abort')
            sys.exit(1)
        else:
            cmd = f'evergreen patch -y -d "{commit_msg}"'
            if finalize:
                cmd += ' -f'
            c.run(cmd)

            webbrowser.open('https://evergreen.mongodb.com/patches/mine')

            # TODO: store the link for future use.
    finally:
        c.run(f'git checkout {feature_branch}')


@task(aliases='f', optional=['push', 'branch'])
def finish(c, push=False, branch='master'):
    """
    Step 7: Finalize your changes. Merge them with the base branch and optionally push upstream.

    :param push: git push your changes (Default: False)
    :param branch: the base branch for your changes. (Default: master)
    """
    init(c)

    commit_num, branch_num = _get_ticket_numbers(c)
    if commit_num != branch_num:
        print('[ERROR] Please commit your local changes before finalizing.')
        sys.exit(1)

    feature_branch = c.run('git rev-parse --abbrev-ref HEAD', hide=True).stdout

    _git_refresh(c, branch)

    res = c.run(f'git rebase {branch}', warn=True)
    if res.return_code != 0:
        print(f'[ERROR] Did not rebase cleanly onto {branch}, '
              f'please manually run: git rebase {branch}')
        c.run(f'git checkout {feature_branch}')
        sys.exit(1)
    c.run(f'git checkout {branch}')
    c.run(f'git merge {feature_branch}')

    push_cmd = 'git push'
    if not push:
        push_cmd += ' -n'

    res = c.run(push_cmd, warn=True)
    if res.return_code != 0:
        print('[ERROR] git push failed!')
        c.run(f'git checkout {feature_branch}')
        sys.exit(1)

    cache = _load_cache(c)
    project = cache.get(branch_num, {}).get('project', 'server')

    if push:
        if branch_num in cache:
            del cache[branch_num]
            _store_cache(c, cache)

        c.run(f'git branch -d {feature_branch}')

        jirac = get_jira()
        if jirac:
            ticket = get_jira().issue(f'{project}-{branch_num}')

            # Transition Ticket
            if ticket.fields.status.id == '10018':  # '10018' = In Code Review.
                print_bold(f'Transitioning {project}-{branch_num} in Jira to "Closed"')
                jirac.transition_issue(ticket, '981')  # '981' = Close Issue
            else:
                print_bold(f'{project}-{branch_num} in Jira is not in '
                           f'"In Code Review" status, not updating Jira')
        else:
            print_bold(f'Please manually add a link of your code review to: '
                       f'https://jira.mongodb.org/browse/{project}-{commit_num}')

    print_bold(
        'Please remember to close this issue and add a comment of your patch build link '
        'if you haven\'t already. The comment should have "Developer" visibility')
    print_bold(f'https://jira.mongodb.com/browse/{project}-{branch_num}')

    self_update(c)


@task(aliases='u')
def self_update(c):
    """
    Update this tool.
    """
    print_bold('Updating MongoDB Server Commandline Tool...')
    with c.cd(str(kPackageDir)):
        c.run('git fetch', warn=False, hide='both')
        c.run('git rebase', warn=False, hide='both')

        # Ignore failures if we can't install or upgrade with pip3.
        c.run('pip3 install --upgrade .', warn=True, hide=True)
        _post_update_steps(c)


@task(aliases='j', optional=['ticket'])
def open_jira(c, ticket=None):
    """
    Open the Jira link for the ticket you're currently working on.

    :param ticket: ticket number without project name (Default: your current git branch)
    """
    commit_num, branch_num = _get_ticket_numbers(c)

    cache = _load_cache(c)

    project = cache.get(branch_num, {}).get('project', 'server')

    print_bold(f'opening Jira for ticket {project.upper()}-{branch_num}')

    if not ticket:
        ticket = branch_num

    webbrowser.open(f'https://jira.mongodb.org/browse/{project.upper()}-{ticket}')
