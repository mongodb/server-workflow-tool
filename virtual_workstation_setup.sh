workdir=$1

# TODO: Support forwarded SSH keys
# if [[ ! -f ~/.ssh/id_rsa ]]; then
#     echo "Please ensure your ssh keys are set up in ~/.ssh/id_rsa and ~/.ssh/id_rsa.pub; see the onboarding wiki page for more info"
#     exit 1
# fi

if [[ -z $(git config --get user.name) ]]; then
    echo "Please ensure your git credentials are set up; see the onboarding wiki page for more info"
    exit 1
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

setup_bash() {
    # Check if we've already added server_bashrc to the user's bash_profile
    grep server_bashrc ~/.bash_profile
    ret=$?
    if [[ $ret = 0 ]]; then
        return
    fi
    
    echo -e "\nsource $HOME/mongodb-mongo-master/server-workflow-tool/server_bashrc.sh" >> ~/.bash_profile
    source ~/.bash_profile
}

setup_master() {
    if [[ -d mongo ]]; then
        return
    fi

    echo "Setting up the mongo repo..."
    git clone git@github.com:mongodb/mongo.git
    pushd $workdir/mongo
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
        return
    fi

    echo "Setting up the 4.4 branch..."
    pushd $workdir/mongo
        git worktree add $workdir/mongo-v44 v4.4
    popd

    pushd $workdir/mongo-v44
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
    pushd $workdir
        git clone git@github.com:10gen/kernel-tools.git
    popd
}

setup_jira_auth() {
    # Get the user's JIRA username
    read -p "JIRA username: " jira_username
    echo "export JIRA_USERNAME=$jira_username" >> ~/.bash_profile
    export JIRA_USERNAME=$jira_username

    # Set up the Jira OAuth Token Generator repo
    pushd $HOME/mongodb-mongo-master
        git clone git@github.com:10gen/iteng-jira-oauth.git
        mkdir venv
        /opt/mongodbtoolchain/v3/bin/python3 -m venv venv

        # Get credentials and store them in the system keyring
        source venv/bin/activate
            python -m pip install --upgrade pip
            python -m pip install -r iteng-jira-oauth/requirements.txt
            python -m pip install ./server-workflow-tool
            dbus-run-session -- python server-workflow-tool/jira_credentials.py set-password $PWD/iteng-jira-oauth
        deactivate
    popd
}

setup_gdb() {
    pushd $workdir
        git clone git@github.com:ruediger/Boost-Pretty-Printer.git
        echo "source $HOME/mongodb-mongo-master/server-workflow-tool/gdbinit" >> ~/.gdbinit
    popd
}

pushd $workdir
    source ~/.bashrc

    sudo mkdir -p /data/db
    sudo chown ubuntu /data/db
    ssh-keyscan github.com >> ~/.ssh/known_hosts

    setup_bash
    setup_master
    setup_44
    setup_cr
    setup_jira_auth
    setup_gdb
popd
