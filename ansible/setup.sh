#!/usr/bin/env bash

# global variables
PYTHON=/opt/mongodbtoolchain/v3/bin/python3
GLOBAL_PYTHON=python3

# === START: function definitions
function install_ansible() {
    echo "Installing Ansible."
    $1 -m venv venv
    source venv/bin/activate
    python -m pip install ansible
}

function check_python_and_install_ansible() {
  if [ -f "$PYTHON" ]; then
      install_ansible $PYTHON;
  else

    if command -v "$GLOBAL_PYTHON" &> /dev/null; then
      install_ansible $GLOBAL_PYTHON;
    else
      echo "Python not found."
      echo "We searched for $PYTHON and $GLOBAL_PYTHON, but could not find it."
      exit 1

    fi
  fi
}

function check_ansible_installation {
    if command -v ansible --version 2>&1 /dev/null; then
      echo "Ansible successfully installed."
    else
      echo "Ansible installation failed."
      exit 1
    fi
}

# === START: flow
# install ansible
check_python_and_install_ansible;

# validate ansible installation
check_ansible_installation;

# run playbook
# --become-user and --become are needed to provide ansible with necessary permissions
ansible-playbook --become-user "$(whoami)" --become start.yml
# everything is handled by ansible.
# this script is used to map installing ansible and running the playbook.
# end
