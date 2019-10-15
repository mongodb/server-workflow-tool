# MongoDB Server Team Workflow Tool

Command line tool to help MongoDB server engineers set up dev environments (not for daily workflow).

## Installation
```
# Install homebrew.
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# Install Python.
brew update
brew install python3 python2
brew upgrade

# Install and update pip.
python3 -m pip install --upgrade pip setuptools

# Install the server workflow tool.
python3 -m pip install git+https://github.com/mongodb/server-workflow-tool.git

# Run the workflow tool to set up your dev environment.
workflow setup.macos
```

## Usage:
```
$ workflow --help

Usage: workflow <subcommand> [--subcommand-opts] ...

Subcommands:

  helpers.upgrade                     Upgrade the workflow tool to the latest version
  setup.macos                         Set up macOS for MongoDB server development.
```
