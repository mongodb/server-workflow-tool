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
    if [[ -d mongo ]]; then
        echo "'mongo' dir exists; skipping setup"
        return
    fi

    echo "Setting up the mongo repo..."
    git clone git@github.com:mongodb/mongo.git
    pushd "$workdir/mongo"
        mkdir -p src/mongo/db/modules
        git clone git@github.com:10gen/mongo-enterprise-modules.git src/mongo/db/modules/enterprise

        /opt/mongodbtoolchain/v3/bin/python3 -m venv python3-venv

        # virtualenv doesn't like nounset
        set +o nounset
        source python3-venv/bin/activate
        set -o nounset

            python -m pip install "pip==21.0.1"

            python -m pip install -r etc/pip/dev-requirements.txt
            python -m pip install keyring

            python buildscripts/scons.py --variables-files=etc/scons/mongodbtoolchain_v3_clang.vars compiledb

            buildninjaic

        set +o nounset
        deactivate
        set -o nounset

    popd
    echo "Finished setting up the mongo repo..."
}

setup_50() {
    if [[ -d mongo-v50 ]]; then
        echo "'mongo-v50' dir exists; skipping setup"
        return
    fi

    echo "Setting up the 5.0 branch..."
    pushd "$workdir/mongo"
        git worktree add "$workdir/mongo-v50" v5.0
    popd

    pushd "$workdir/mongo-v50"
        mkdir -p src/mongo/db/modules
        git clone git@github.com:10gen/mongo-enterprise-modules.git -b v5.0 src/mongo/db/modules/enterprise

        /opt/mongodbtoolchain/v3/bin/python3 -m venv python3-venv

        # virtualenv doesn't like nounset
        set +o nounset
        source python3-venv/bin/activate
        set -o nounset

            # The bundled pip version is very old (10.0.1), upgrade to the newest version that still
            # uses the original resolver. See SERVER-53250 for more info.
            python -m pip install --upgrade "pip<20.3"

            python -m pip install -r etc/pip/dev-requirements.txt
            python -m pip install keyring

            python buildscripts/scons.py --variables-files=etc/scons/mongodbtoolchain_stable_clang.vars compiledb

            buildninjaic

        set +o nounset
        deactivate
        set -o nounset
    popd
    echo "Finished setting up the 5.0 branch"
}

setup_44() {
    if [[ -d mongo-v44 ]]; then
        echo "'mongo-v44' dir exists; skipping setup"
        return
    fi

    echo "Setting up the 4.4 branch..."
    pushd "$workdir/mongo"
        git worktree add "$workdir/mongo-v44" v4.4
    popd

    pushd "$workdir/mongo-v44"
        mkdir -p src/mongo/db/modules
        git clone git@github.com:10gen/mongo-enterprise-modules.git -b v4.4 src/mongo/db/modules/enterprise

        /opt/mongodbtoolchain/v3/bin/python3 -m venv python3-venv

        # virtualenv doesn't like nounset
        set +o nounset
        source python3-venv/bin/activate
        set -o nounset

            # The bundled pip version is very old (10.0.1), upgrade to the newest version that still
            # uses the original resolver. See SERVER-53250 for more info.
            python -m pip install --upgrade "pip<20.3"

            python -m pip install -r etc/pip/dev-requirements.txt
            python -m pip install keyring

            python buildscripts/scons.py --variables-files=etc/scons/mongodbtoolchain_v3_clang.vars compiledb

            buildninjaic

        set +o nounset
        deactivate
        set -o nounset
    popd
    echo "Finished setting up the 4.4 branch"
}

setup_cr() {
    pushd "$workdir"
        if [[ -d 'kernel-tools' ]]; then
            echo "'kernel-tools' dir exists; skipping setup"
            return
        fi
        git clone git@github.com:10gen/kernel-tools.git
    popd
}

setup_jira_auth() {
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
        /opt/mongodbtoolchain/v3/bin/python3 -m venv iteng-jira-oauth/venv

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
    pushd "$workdir"
        if [[ -d 'Boost-Pretty-Printer' ]]; then
            echo "'Boost-Pretty-Printer' dir exists; skipping setup"
        else
            git clone git@github.com:ruediger/Boost-Pretty-Printer.git
        fi

        # the original version of this script just appended this line, so we
        # have to grep for it manually
        if ! silent_grep "source $HOME/mongodb-mongo-master/server-workflow-tool/gdbinit" ~/.gdbinit; then
            idem_file_append ~/.gdbinit "Server Workflow Tool gdbinit" "source $HOME/mongodb-mongo-master/server-workflow-tool/gdbinit"
        fi
    popd
}

setup_undodb() {
    local evg_username=$(evg_user)
    if [ -z "$evg_username" ]; then
        echo "UndoDB: can't figure out what your SSO username is. Set the 'UNDO_user' environment variable to your Okta username in your shell's rc file before using UndoDB"
        echo "ex: export UNDO_user='john.doe'"
        return
    fi

    local marker="UndoDB License Config"
    local block=$(cat <<BLOCK
export UNDO_user='$evg_username'
BLOCK
    )
    idem_file_append ~/.bashrc "$marker" "$block"
    idem_file_append ~/.zshrc "$marker" "$block" 1

    local marker2="UndoDB Aliases"
    local block2=$(cat <<BLOCK
alias udb='/opt/undodb5/bin/udb --undodb-gdb-exe /opt/mongodbtoolchain/gdb/bin/gdb'
#alias gdb='/opt/undodb5/bin/udb --undodb-gdb-exe /opt/mongodbtoolchain/gdb/bin/gdb'
alias gdb='/opt/mongodbtoolchain/gdb/bin/gdb'
BLOCK
    )
    idem_file_append ~/.bashrc "$marker2" "$block2"
    idem_file_append ~/.zshrc "$marker2" "$block2" 1
}

pushd "$workdir"
    set +o nounset
    source ~/.bashrc
    set -o nounset

    sudo mkdir -p /data/db
    sudo chown ubuntu /data/db
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>&1

    setup_bash
    setup_master
    setup_50
    setup_cr
    setup_jira_auth
    setup_gdb
    setup_undodb

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
