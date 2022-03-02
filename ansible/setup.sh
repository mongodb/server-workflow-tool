#!/usr/bin/env bash

# install Ansible
PYTHON=/opt/mongodbtoolchain/v3/bin/python3

if [ -f "$PYTHON" ]; then
    echo "Installing Ansible."
    $PYTHON -m venv venv
    source venv/bin/activate
    python -m pip install ansible
else
  echo "python3 not found inside mongodbtoolchain. We searched for $PYTHON, but could not find it."
  exit 1
fi

# run playbook
ansible-playbook start.yml
# everything is handled by ansible.
# this script is used to map installing ansible and running the playbook.
# end
