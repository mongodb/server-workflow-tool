# Operations in this file should be idempotent-ish. At the very least, make
# sure your code doesn't do duplicate work/clobber existing files on rerun
set -o errexit
workdir=$1

# TODO: Support forwarded SSH keys (check if SSH_AUTH_SOCK is not empty?)
# if [[ ! -f ~/.ssh/id_rsa ]]; then
#     echo "Please ensure your ssh keys are set up in ~/.ssh/id_rsa and ~/.ssh/id_rsa.pub; see the onboarding wiki page for more info"
#     exit 1
# fi

if [[ -z $(git config --get user.name) ]]; then
    echo "Please ensure your git credentials are set up; see the onboarding wiki page for more info"
    exit 1
fi

test_github_keys=$(ssh -T git@github.com | grep -q "You've successfully authenticated, but GitHub does not provide shell access")
if ! $test_github_keys; then
    echo "Please ensure your GitHub SSH keys have been set up; see the onboarding wiki page for more info"
    if [[ -f ~/.ssh/id_rsa.pub ]]; then
        echo "Your SSH Public Key:"
        cat ~/.ssh/id_rsa.pub
        exit 1
    fi
fi

if [[ -z "$1" ]]; then
  workdir=$HOME
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

# arg1: file
# arg2: a unique marker text for the block being appended
# arg3: block to inject
# arg4: if non empty, do not append if the file does not exist
idem_file_append() {
    if [[ -z $1 ]]; then
        return 1
    fi
    if [[ ! -f $1 && -n $4 ]]; then
        return
    fi
    if [[ -z $2 ]]; then
        return 2
    fi
    if [[ -z $3 ]]; then
        return 3
    fi
    local start_marker="# BEGIN $2"
    local end_marker="# END $2"
    if ! grep "^$start_marker" "$1"; then
        echo -e "\n$start_marker" >> "$1"
        echo -e "$3" >> "$1"
        echo -e "$end_marker" >> "$1"
    fi
}

setup_bash() {
    # Check if we've already added server_bashrc to the user's bash_profile
    grep server_bashrc ~/.bash_profile
    ret=$?
    if [[ $ret != 0 ]]; then
        echo -e "\nsource $HOME/mongodb-mongo-master/server-workflow-tool/server_bashrc.sh" >> ~/.bash_profile
    fi

    # Bash profile should source .bashrc
    local block=<<-BLOCK
    if [[ -f ~/.bashrc ]]; then
        source ~/.bashrc
    fi
BLOCK

    idem_file_append ~/.bash_profile "Source .bashrc" "$block"

    source ~/.bash_profile
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
        source python3-venv/bin/activate

            # The bundled pip version is very old (10.0.1), upgrade to (20.0+).
            python -m pip install --upgrade pip

            python -m pip install -r etc/pip/dev-requirements.txt

            python buildscripts/scons.py --variables-files=etc/scons/mongodbtoolchain_v3_clang.vars compiledb

            buildninjaic
        deactivate

    popd
    echo "Finished setting up the mongo repo..."
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
        source python3-venv/bin/activate

            # The bundled pip version is very old (10.0.1), upgrade to (20.0+).
            python -m pip install --upgrade pip

            python -m pip install -r etc/pip/dev-requirements.txt

            python buildscripts/scons.py --variables-files=etc/scons/mongodbtoolchain_v3_clang.vars compiledb

            buildninjaic
        deactivate
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

setup_gdb() {
    pushd "$workdir"
        if [[ -d 'Boost-Pretty-Printer' ]]; then
            echo "'Boost-Pretty-Printer' dir exists; skipping setup"
            return
        fi
        git clone git@github.com:ruediger/Boost-Pretty-Printer.git
        echo "source $HOME/mongodb-mongo-master/server-workflow-tool/gdbinit" >> ~/.gdbinit
    popd
}

setup_undodb() {
    local evg_username
    evg_username=$(evg_user)
    if [ -z "$evg_username" ]; then
        echo "UndoDB: can't figure out what your SSO username is. Set the 'UNDO_user' environment variable to your Okta username in your shell's rc file before using UndoDB"
        echo "ex: export UNDO_user='john.doe'"
        return 1
    fi

    local marker="UndoDB License Config"
    local block=<<-BLOCK
    export UNDO_user='$evg_username'
    alias udb='/opt/undodb-5/bin/udb --undodb-gdb-exe /opt/mongodbtoolchain/gdb/bin/gdb'
BLOCK
    idem_file_append ~/.bashrc "$marker" "$block"
    idem_file_append ~/.zshrc "$marker" "$block" 1
}

pushd "$workdir"
    source ~/.bashrc

    sudo mkdir -p /data/db
    sudo chown ubuntu /data/db
    ssh-keyscan github.com >> ~/.ssh/known_hosts

    setup_bash
    setup_master
    setup_44
    setup_cr
    setup_gdb
    setup_undodb
popd
