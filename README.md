# MongoDB Server Team Command-line Tool

Command line tool to help MongoDB server engineers set up dev environment and automate everyday workflow.

## Installation:
```
git clone https://github.com/mongodb/server-workflow-tool.git ~/.config/
cd ~/.config/server-workflow-tool
pip3 install .
```

## Usage:
```
Usage: m(mongodb command line tool) <subcommand> [--subcommand-opts] ...

Subcommands:

  commit (c)                             Step 4: Wrapper around git commit to automatically add changes and fill in the ticket number
  finish (f)                             Step 7: Finalize your changes. Merge them with the base branch and optionally push upstream.
  lint (l)                               Step 3: lint and format your code: Wrapper around clang_format and eslint.
  new (n)                                Step 1: Create or switch to the branch for a ticket.
  open-jira (j)                          Open the Jira link for the ticket you're currently working on.
  patch (p)                              Step 6: Run patch build in Evergreen.
  review (r)                             Step 5: Put your code up for code review.
  scons (s)                              Step 2: [experimental] Check your code compiles, wrapper around "python buildscripts/scons.py".
  self-update (u)                        Update this tool.
  setup-dev-env._check-homebrew-exists
  setup-dev-env._checkout-repo
  setup-dev-env._create-db-dir
  setup-dev-env._create-ssh-keys
  setup-dev-env._install-binary
  setup-dev-env._install-editor
  setup-dev-env._install-git-hook
  setup-dev-env._set-env-vars
  setup-dev-env._set-evergreen-config
  setup-dev-env.get-passwords
  setup-dev-env.macos                    Set up MongoDB core server development environment on MacOS. Please run this task with "-w"
  setup-dev-env.macos-extra              Set up optional MongoDB development utilities on MacOS
```
