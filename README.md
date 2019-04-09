# MongoDB Server Team Command-line Tool

Command line tool to help MongoDB server engineers set up dev environment and automate everyday workflow.

## Installation
```
# These are the installation steps for a brand new macOS machine. Copy and paste each line here individually.

# Install homebrew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# Download python3 and pip3
brew install --upgrade python3
pip3 install --upgrade pip setuptools

# Clone the workflow tool and install its dependencies.
mkdir -p ~/.config
cd ~/.config
rm -rf server-workflow-tool
git clone https://github.com/mongodb/server-workflow-tool
cd server-workflow-tool
pip3 install .

# Add the workflow tool to PATH.
echo "source ~/.config/server-workflow-tool/profile" >> ~/.profile
echo "source ~/.profile" >> ~/.bashrc
echo "source ~/.profile" >> ~/.zshrc

# Run install script.
m -w setup-dev-env.macos
m -w setup-dev-env.macos-extra
```


## Re-Installation:
```
git clone https://github.com/mongodb/server-workflow-tool.git ~/.config/server-workflow-tool
cd ~/.config/server-workflow-tool
pip3 install .
echo "source ~/.config/server-workflow-tool/profile" >> ~/.profile
```



## Usage:
```
Usage: m(mongodb command line tool) <subcommand> [--subcommand-opts] ...

Subcommands:

  commit (c)                             Step 3: Wrapper around git commit to automatically add changes and fill in the ticket number
  finish (f)                             Step 6: Finalize your changes. Merge them with the base branch and optionally push upstream.
  lint (l)                               Step 2: lint and format your code: Wrapper around clang_format and eslint.
  new (n)                                Step 1: Create or switch to the branch for a ticket.
  open-jira (j)                          Open the Jira link for the ticket you're currently working on.
  patch (p)                              Step 5: Run patch build in Evergreen.
  review (r)                             Step 4: Put your code up for code review.
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
