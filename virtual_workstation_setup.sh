workdir=$1

if [[ ! -f ~/.ssh/id_rsa ]]; then
    echo "Please ensure your ssh keys are set up in ~/.ssh/id_rsa and ~/.ssh/id_rsa.pub; see the onboarding wiki page for more info"
    exit 1
fi

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
    # Check if we've already added server_bashrc to the user's bashrc
    grep server_bashrc ~/.bashrc
    ret=$?
    if [[ $ret = 0 ]]; then
        return
    fi

    echo -e "\nsource $HOME/server-workflow-tool/server_bashrc.sh" >> ~/.bashrc

    source ~/.bashrc
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

            python buildscripts/scons.py compiledb

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

            python buildscripts/scons.py compiledb

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

pushd $workdir
    source ~/.bashrc

    sudo mkdir -p /data/db
    sudo chown ubuntu /data/db
    ssh-keyscan github.com >> ~/.ssh/known_hosts

    setup_bash
    setup_master
    setup_44
popd