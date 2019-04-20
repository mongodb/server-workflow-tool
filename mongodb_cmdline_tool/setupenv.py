import getpass
import os
import pathlib
import re
import tempfile
import webbrowser

import yaml
from invoke import task
from invoke.exceptions import Exit, UnexpectedExit

from mongodb_cmdline_tool.utils import print_bold, format_bold, get_jira_pwd, save_jira_pwd

# Global Constants.
kHome = pathlib.Path.home()
kOptDir = pathlib.Path('/opt')
kDownloadsCache = pathlib.Path(tempfile.mkdtemp())
kPackageDir = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
kConfigDir = kHome / '.config'
kTemplatesDir = kConfigDir / 'server-workflow-tool' / 'mongodb_cmdline_tool' / 'templates'

# Exit code.
kCommandNotFound = 127
kSuccess = 0

# Environment variables.
env_editor = None

# Toolchain constants.
kToolchainURL = ('https://s3.amazonaws.com/mciuploads/toolchain-builder/osx/'
                 '23e02cf782ce2069598f5b8a3029cd13daf6db1c/toolchain_builder_'
                 'osx_23e02cf782ce2069598f5b8a3029cd13daf6db1c_18_06_05_16_54_20.tar.gz')

# Evergreen constants
kEvgToolURL = 'https://evergreen.mongodb.com/clients/darwin_amd64/evergreen'
kEvgConfigPath = pathlib.Path.home() / '.evergreen.yml'

# GitHub constants
kGitHubAddSSHHelpURL = ('https://help.github.com/articles/'
                        'generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/#platform-mac')
kRepositories = [
    {'source_loc': 'git@github.com:mongodb/mongo.git',
     'target_loc': 'mongo'},
    {'source_loc': 'git@github.com/10gen/mongo-enterprise-modules',
     'target_loc': 'mongo/src/mongo/db/modules/'},
    {'source_loc': 'git@github.com:10gen/kernel-tools.git',
     'target_loc': 'kernel-tools'}
]
# Runtime configuration
jira_username = None
jira_password = None
sudo_password = None


@task
def get_passwords(c):
    global jira_password
    global sudo_password

    if not get_jira_pwd():
        jira_password = getpass.getpass(prompt='jira.mongodb.org password: ')
        save_jira_pwd(jira_password)

    jira_password = get_jira_pwd()
    sudo_password = getpass.getpass(prompt='Your sudo password: ')


@task
def macos(c):
    """
    Set up MongoDB core server development environment on MacOS. Please run this task with "-w"

    set $EDITOR
    clang-format, eslint, pylinter
    git credentials: https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account/
    git checkout optionally enterprise module repos,
    ssh keys
    evergreen credentials (requires manual copy and paste from browser
        https://evergreen.mongodb.com/settings),
        also turn on email/Slack alerts for patch builds
    evergreen default build variants and tasks, tasks vary by team

    """
    get_passwords(c)

    print_bold('Checking sudo password is correct')
    c.sudo('ls', warn=False, hide='both', password=sudo_password)

    print_bold('Setting Evergreen Configuration')
    _set_evergreen_config(c)

    print_bold('Creating SSH keys')
    _create_ssh_keys(c)

    print_bold(f'Checking out your git repositories')
    for repo in kRepositories:
        _checkout_repo(c, repo['source_loc'], repo['target_loc'])

    print_bold('Installing git hooks for the mongo repo')
    _install_git_hook(c)

    print_bold(f'Creating /data/db')
    _create_db_dir(c)

    print_bold('Checking HomeBrew is installed')
    # res = c.run('brew --version', hide='both')
    # _check_homebrew_exists(c)

    print_bold('Installing Text Editor')
    _install_editor(c)

    print_bold('Setting Evergreen Configuration')
    _set_evergreen_config(c)

    with c.cd(f'{kHome / "mongo"}'):
        c.run('pip3 install -r buildscripts/requirements.txt')  # Ignore permission errors.
        c.run('python2 -m pip install -r buildscripts/requirements.txt')  # Ignore permission errors.
        c.run('python2 -m pip install regex', warn=False)

    print_bold('Installing MongoDB Toolchain')
    _install_binary(c, kToolchainURL, f'toolchain.tar.gz', 'mongodbtoolchain', kOptDir, untar=True)

    print_bold('Installing Evergreen Command Line Tool')
    _install_binary(c, kEvgToolURL, 'evergreen', 'evergreen', pathlib.Path.home() / 'bin',
                    untar=False)

    # Work around 'evergreen' not executable by default.
    c.run(f'chmod +x {pathlib.Path.home() / "bin" / "evergreen"}')

    print_bold('Setting configurations and environment variables.')
    _set_env_vars(c)


@task
def _set_env_vars(c):
    with open(str(kHome / '.bashrc'), 'a') as f:
        lines = [
            f'export PATH=/opt/mongodbtoolchain/v2/bin:$HOME/bin:$PATH'
        ]

        if env_editor:
            lines.append(f'export EDITOR={env_editor}')

        f.write('\n'.join(lines))

    with open(str(kTemplatesDir / 'default-evergreen-config.yml')) as f:
        conf = f.read()

    with open(str(kHome / '.evergreen.yml'), 'a') as f:
        f.write(conf)


@task
def _install_git_hook(c):
    mongo_hooks = kHome / ".githooks" / "mongo"

    c.run(f'mkdir -p {mongo_hooks}', warn=False)
    c.run(f'cp -r {kHome / "kernel-tools" / "githooks"/ "*"} {mongo_hooks}')

    with c.cd(f'{mongo_hooks}'):
        c.run('rm pre-push/check-uncommitted')
        c.run('rm pre-push/check-code-freeze-any-branch')
        c.run('rm pre-push/check-compile')
        c.run('rm README.md')

    with c.cd(f'{kHome / "mongo"}'):
        c.run('source buildscripts/install-hooks -f', warn=False, hide=None)


@task
def _create_db_dir(c):
    c.sudo('mkdir -p /data/db', warn=False, hide='both', password=sudo_password)
    c.sudo(f'chown {getpass.getuser()} /data/db', warn=False, password=sudo_password)


@task
def _checkout_repo(c, source_loc, target_loc):
    parent_dir = kHome
    with c.cd(str(parent_dir)):
        if os.path.exists(parent_dir / target_loc):
            print(f'Found existing directory {parent_dir / target_loc}, skipping cloning {source_loc}')
        else:
            c.run(f'git clone {source_loc} {target_loc}', warn=False)


@task
def _create_ssh_keys(c):
    if os.path.isfile(pathlib.Path.home() / '.ssh' / 'id_rsa'):
        print('Found existing id_rsa, skipping creating ssh keys')
        return

    res = input(format_bold('Opening browser for instructions to setting up ssh keys in GitHub, '
                            'press any key to continue, enter "skip" to skip: '))
    if res != 'skip':
        webbrowser.open(kGitHubAddSSHHelpURL)
        input(format_bold(
            'Once you\'ve generated SSH keys and added them to GitHub, press any key to continue'))
    else:
        print('Skipping adding SSH Keys to GitHub')


@task
def _set_evergreen_config(c):
    global jira_username

    if os.path.isfile(kEvgConfigPath):
        print('Found existing ~/.evergreen.yml, skipping adding Evergreen configuration')
        print('Please make sure your Evergreen config file contains your API credentials and'
              ' a default project configuration of mongodb-mongo-master.')
    else:
        input('Opening browser to configure Evergreen Authentication credentials, press any key to'
              'continue')
        webbrowser.open('https://evergreen.mongodb.com/settings')

        input('Once you have created ~/.evergreen.yml, added your credentials to it and entered '
              'your user and notification settings on the web UI, press any key to continue')

    with open(pathlib.Path.home() / '.evergreen.yml') as evg_file:
        evg_config = yaml.load(evg_file)
        jira_username = evg_config['user']


@task
def _install_editor(c):
    global env_editor

    # Install editors.
    while True:
        default_editor = 'nano'
        editor = input('Which text editor do you use? '
                       '(e.g. vim/emacs/neovim/sublime-text/visual-studio-code. Default: nano): ')
        if not editor:
            editor = default_editor

        # Hide stdout and stderr by default because editor may be a cask.
        res = c.run(f'brew install {editor}', hide='both')
        if res.return_code is not kSuccess:
            res_cask = c.run(f'brew cask reinstall {editor}', hide='both')
            if res_cask.return_code is not kSuccess:
                print(res)
                print(res_cask)
                print((f'\'{editor}\' not found; please find the '
                       f'name of the HomeBrew formula for {editor}'))
                continue
            stdout = res_cask.stdout
            match = re.search(r'Linking Binary \'(\w+)\'', stdout)
            if match:
                env_editor = match.group(1)
            else:
                print((f'WARNING: {editor} does not have a command line invocation, '
                       f'using \'{default_editor}\' as $EDITOR'))
                env_editor = 'nano'

        else:
            env_editor = editor
        print(f'Installed {editor}')
        break


@task
def _install_binary(c, url, download_name, binary_name, parent_dir, untar=False):
    with c.cd(str(kDownloadsCache)):
        # Don't warn, error out immediately.
        c.run(f'curl -fsSL {url} -o {download_name}', warn=False)
        if untar:
            c.run(f'tar -xvf {download_name}', hide='both', warn=False)

    c.sudo(f'mkdir -p {parent_dir}', warn=False, password=sudo_password)
    c.sudo(f'rm -rf {parent_dir / binary_name}', warn=False, password=sudo_password)
    c.sudo(f'mv -f {kDownloadsCache / binary_name} {parent_dir / binary_name}', warn=False,
           password=sudo_password)
    c.sudo(f'chown -R {getpass.getuser()} {parent_dir / binary_name}', warn=False,
           password=sudo_password)
    print(f'Installed {binary_name} to {parent_dir}')


@task
def _check_homebrew_exists(res):
    if res.return_code == kCommandNotFound:
        raise Exit('`brew` executable not found. Please install HomeBrew: https://brew.sh')
    elif res.return_code != kSuccess:
        raise UnexpectedExit(res)


@task
def macos_extra(c):
    """
    Set up optional MongoDB development utilities on MacOS

    :param c:
    :return:
    """
    print_bold('Installing ninja')
    c.run('brew install ninja')

    modules_dir = str(kHome / 'mongo' / 'src' / 'mongo' / 'db' / 'modules')
    c.run(f'mkdir -p {modules_dir}')

    with c.cd(modules_dir):
        # Ignore errors since ninja may already exist.
        c.run('git clone https://github.com/RedBeard0531/mongo_module_ninja ninja', warn=True)
    with c.cd(str(kHome / 'mongo')):
        ninja_cmd = 'python2 buildscripts/scons.py CC=clang CXX=clang++ '
        ninja_cmd += 'CCFLAGS=-Wa,--compress-debug-sections '
        ninja_cmd += 'MONGO_VERSION=\'0.0.0\' MONGO_GIT_HASH=\'unknown\' '
        ninja_cmd += 'VARIANT_DIR=ninja --modules=ninja build.ninja'
        c.run(ninja_cmd)

    print_bold('Installing CLion')

    # Ignore errors since CLion already exists.
    c.run('brew cask install clion', warn=True)
    with c.cd(str(kTemplatesDir)):
        c.run('cp mongo-cmakelists.txt ~/mongo/CMakeLists.txt')
