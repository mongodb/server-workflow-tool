# Operations in this file should be idempotent-ish. At the very least, make
# sure your code doesn't do duplicate work/clobber existing files on rerun
set -euo pipefail
workdir=${1:-$HOME}

if [[ -z $(git config --get user.name) ]]; then
    echo "Please ensure your git credentials are set up; see the onboarding wiki page for more info"
    exit 1
fi

silent_grep() {
    command grep -q  > /dev/null 2>&1 "$@"
}

set +e
# we assume that if the user has non default SSH key filename they know about ssh-agent
# and can set it up themselves
for filename in ~/.ssh/id_*; do
    [[ -e "$filename" && "$filename" != *".pub" ]] || continue
    # check if SSH key has passphrase
    ssh-keygen -y -P "" -f "$filename" > /dev/null 2>&1
    [ $? -eq 0 ] && continue
    # check if SSH agent is running and have any SSH keys added
    # (we assume that the key with passphrase will be added, but not checking it explicitly)
    ssh-add -l > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "SSH key with passphare found: $filename"
        echo "Please do the following steps:"
        echo " - Setup ssh-agent"
        echo " - Add SSH key with passphrase to the ssh-agent"
        echo " - Rerun the Evergreen project setup command"
        echo "It will help to avoid entering passphrase during the setup script run"
        exit 1
    fi
done
set -e

# SSH into GitHub and check for the success message. The SSH command
# returns 1, so it can't be used alone
github_test=$(ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -T git@github.com 2>&1 || true)
if ! (echo "${github_test}" | silent_grep "You've successfully authenticated, but GitHub does not provide shell access"); then
    echo "Cannot login to GitHub via SSH"
    echo "Please ensure your GitHub SSH keys have been set up; see the onboarding wiki page for more info"
    echo "Your SSH Public Keys:"
    cat ~/.ssh/id_*.pub || true
    exit 1
fi

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

evg_user() {
    local evg_username=$(grep -Po '(?<=user: ).*' "$HOME/.evergreen.yml")
    if [ -z "$evg_username" ]; then
        evg_username=$(grep -Po '(?<=user:).*' "$HOME/.evergreen.yml")
    fi

    echo "$evg_username"
}

# append a given block to a file. Surround it with the markers so
# it looks like this:
# # BEGIN Marker
# block goes here
# # END Marker
#
# Do not attempt to change the contents of a block in the future with this
# function. It doesn't support updating a block, so just make a block with a
# new marker, and yell at the user at the bottom of the script to fix it
#
# arg1: file
# arg2: a unique marker text for the block being appended
# arg3: block to inject
# arg4: if non empty, do not append if the file does not exist
idem_file_append() {
    if [[ -z "$1" ]]; then
        return 1
    fi
    if [[ ! -f "$1" && -n "${4-}" ]]; then
        return
    fi
    if [[ -z "$2" ]]; then
        return 2
    fi
    if [[ -z "$3" ]]; then
        return 3
    fi
    local start_marker="# BEGIN $2"
    local end_marker="# END $2"
    if ! silent_grep "^$start_marker" "$1"; then
        {
            echo -e "\n$start_marker";
            echo -e "$3";
            echo -e "$end_marker";
        } >> "$1"
    fi
}

# Here's a quick explanation of what's going on here for the next soul here:
# If you like visuals instead: https://shreevatsa.files.wordpress.com/2008/03/bashstartupfiles1.png
# bash_profile is generally invoked once per login shell.
# bashrc is invoked for interactive, non-login shells

# setup_bash will make bash_profile source .bashrc (see the "may include" in
# the above diagram), and the .bashrc will source the server_bashrc.sh file
# in this repo.
# This ensures that no matter which kind of interactive shell you're using, the
# server_bashrc.sh has been sourced. While we technically could just source
# server_bashrc.sh in both .bash_profile, and .bashrc, this could break if
# something gets added to it that cannot be sourced more than once in the same
# session.
setup_bash() {
    # Bash profile should source .bashrc
    echo "################################################################################"
    echo "Setting up bash..."
    local block=$(cat <<BLOCK
if [[ -f ~/.bashrc ]]; then
    source ~/.bashrc
fi
BLOCK
    )

    idem_file_append ~/.bash_profile "Source .bashrc" "$block"
    idem_file_append ~/.bashrc "Source server_bashrc.sh" "source $HOME/mongodb-mongo-master/server-workflow-tool/server_bashrc.sh"

    set +o nounset
    source ~/.bash_profile
    set -o nounset
}

setup_master() {
    echo "################################################################################"
    echo "Setting up the mongo repo..."
    if [[ -d mongo ]]; then
        echo "'mongo' dir exists; skipping setup"
        return
    fi

    git clone git@github.com:10gen/mongo.git
    pushd "$workdir/mongo"
        mkdir -p src/mongo/db/modules
        git clone git@github.com:10gen/mongo-enterprise-modules.git src/mongo/db/modules/enterprise

        /opt/mongodbtoolchain/v4/bin/python3 -m venv python3-venv

        # virtualenv doesn't like nounset
        set +o nounset
        source python3-venv/bin/activate
        set -o nounset

            python -m pip install "pip==21.0.1"

            python -m pip install -r etc/pip/dev-requirements.txt
            python -m pip install keyring

            python buildscripts/scons.py --variables-files=etc/scons/mongodbtoolchain_stable_clang.vars compiledb

            buildninjaic

        set +o nounset
        deactivate
        set -o nounset

    popd
    echo "Finished setting up the mongo repo..."
}

setup_60() {
    echo "################################################################################"
    echo "Setting up the 6.0 branch..."
    if [[ -d mongo-v60 ]]; then
        echo "'mongo-v60' dir exists; skipping setup"
        return
    fi

    pushd "$workdir/mongo"
        git worktree add "$workdir/mongo-v60" v6.0
    popd

    pushd "$workdir/mongo-v60"
        mkdir -p src/mongo/db/modules
        git clone git@github.com:10gen/mongo-enterprise-modules.git -b v6.0 src/mongo/db/modules/enterprise

        /opt/mongodbtoolchain/v3/bin/python3 -m venv python3-venv

        # virtualenv doesn't like nounset
        set +o nounset
        source python3-venv/bin/activate
        set -o nounset
            python -m pip install --upgrade "pip==21.0.1"

            python -m pip install -r etc/pip/dev-requirements.txt
            python -m pip install keyring

            python buildscripts/scons.py --variables-files=etc/scons/mongodbtoolchain_stable_clang.vars compiledb

            buildninjaic

        set +o nounset
        deactivate
        set -o nounset
    popd
    echo "Finished setting up the 6.0 branch"
}

setup_cr() {
    echo "################################################################################"
    echo "Setting up Rietveld Code Review tool..."
    pushd "$workdir"
        if [[ -d 'kernel-tools' ]]; then
            echo "'kernel-tools' dir exists; skipping setup"
            return
        fi
        git clone git@github.com:10gen/kernel-tools.git
    popd
}

setup_jira_auth() {
    echo "################################################################################"
    echo "Setting up Jira Authentication..."
    if [ -d "$HOME/mongodb-mongo-master/iteng-jira-oauth" ]; then
        echo "'mongodb-mongo-master/iteng-jira-oauth' dir exists; skipping setup"
        return
    fi

    # Get the user's JIRA username
    read -p "JIRA username (from https://jira.mongodb.org/secure/ViewProfile.jspa): " jira_username
    if ! silent_grep "export JIRA_USERNAME=" ~/.bashrc; then
        idem_file_append ~/.bashrc "CR Tool JIRA Username" "export JIRA_USERNAME=$jira_username"
    fi
    export JIRA_USERNAME=$jira_username
    echo "Wrote username \"$JIRA_USERNAME\" to ~/.bashrc"

    # Set up the Jira OAuth Token Generator repo
    pushd "$HOME/mongodb-mongo-master"
        git clone git@github.com:10gen/iteng-jira-oauth.git
        pushd iteng-jira-oauth
            # Newer versions parse commandline options, which is incompatible with how jira_credentials.py
            # uses this repo.
            git checkout c837b044ca562c45fbd119a07cf477650545731e
        popd
        mkdir iteng-jira-oauth/venv
        /opt/mongodbtoolchain/v4/bin/python3 -m venv iteng-jira-oauth/venv

        # Get credentials and store them in the system keyring
        set +o nounset
        source iteng-jira-oauth/venv/bin/activate
        set -o nounset
            python -m pip install --upgrade pip
            python -m pip install -r iteng-jira-oauth/requirements.txt
            python -m pip install keyring psutil
            dbus-run-session -- python server-workflow-tool/jira_credentials.py set-password "$PWD/iteng-jira-oauth"
        set +o nounset
        deactivate
        set -o nounset
    popd
}

setup_gdb() {
    echo "################################################################################"
    echo "Setting up GDB..."
    pushd "$workdir"
        if [[ -d 'Boost-Pretty-Printer' ]]; then
            echo "'Boost-Pretty-Printer' dir exists; skipping setup"
        else
            git clone git@github.com:mongodb-forks/Boost-Pretty-Printer.git
        fi

        # the original version of this script just appended this line, so we
        # have to grep for it manually
        if ! silent_grep "source $HOME/mongodb-mongo-master/server-workflow-tool/gdbinit" ~/.gdbinit; then
            idem_file_append ~/.gdbinit "Server Workflow Tool gdbinit" "source $HOME/mongodb-mongo-master/server-workflow-tool/gdbinit"
        fi
    popd
}

setup_pipx() {
    echo "################################################################################"
    echo "Installing 'pipx' command..."
    if command -v pipx &> /dev/null; then
        echo "'pipx' command exists; skipping setup"
    else
        export PATH="$PATH:$HOME/.local/bin"
        local venv_name="tmp-pipx-venv"
        /opt/mongodbtoolchain/v4/bin/python3 -m venv $venv_name

        # virtualenv doesn't like nounset
        set +o nounset
        source $venv_name/bin/activate
        set -o nounset

            python -m pip install --upgrade "pip<20.3"
            python -m pip install pipx

            pipx install pipx --python /opt/mongodbtoolchain/v4/bin/python3 --force

        set +o nounset
        deactivate
        set -o nounset

        rm -rf $venv_name

        local marker="pipx config"
        local block=$(cat <<BLOCK
# pipx will install binaries to "~/.local/bin"
export PATH="$PATH:$HOME/.local/bin"
BLOCK
        )
        idem_file_append ~/.bashrc "$marker" "$block"
        idem_file_append ~/.zshrc "$marker" "$block" 1
    fi
}

setup_evg_module_manager() {
    echo "################################################################################"
    echo "Installing 'evg-module-manager' command..."
    export PATH="$PATH:$HOME/.local/bin"
    if command -v evg-module-manager &> /dev/null; then
        echo "'evg-module-manager' command exists; skipping setup"
    else
        pipx install evg-module-manager
    fi
}

setup_db_contrib_tool() {
    echo "################################################################################"
    echo "Installing 'db-contrib-tool' command..."
    export PATH="$PATH:$HOME/.local/bin"
    if command -v db-contrib-tool &> /dev/null; then
        echo "'db-contrib-tool' command exists; skipping setup"
    else
        pipx install db-contrib-tool
    fi
}

pushd "$workdir"
    set +o nounset
    source ~/.bashrc
    set -o nounset

    sudo mkdir -p /data/db
    sudo chown ubuntu /data/db
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>&1

    setup_bash
    setup_jira_auth
    setup_master
    setup_60
    setup_cr
    setup_gdb

    setup_pipx
    setup_evg_module_manager  # This step requires `setup_pipx` to have been run.
    setup_db_contrib_tool  # This step requires `setup_pipx` to have been run.

    nag_user=1
    if silent_grep server_bashrc ~/.bash_profile; then
        echo "Please remove the line from your ~/.bash_profile that sources mongodb-mongo-master/server-workflow-tool/server_bashrc.sh"
        nag_user=0
    fi
    if silent_grep "JIRA_USERNAME" ~/.bash_profile; then
        echo "Please remove the line from your ~/.bash_profile that exports JIRA_USERNAME"
        nag_user=0
    fi

    if [ $nag_user -eq 0 ]; then
        echo "^^^^^^^^^^^^^^^ READ ABOVE ^^^^^^^^^^^^^^^"
    fi
popd
