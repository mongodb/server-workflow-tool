# MongoDB Server Team Workflow Tool

Command line tool to help MongoDB server engineers set up dev environments and automate everyday workflow.

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
workflow --help

Usage: workflow <subcommand> [--subcommand-opts] ...

Subcommands:

  anew (a, start, switch)             Step 0: Start a ticket or continue working on an existing ticket.
  code                                Step 1: 💻 Write code. (Informational only, there's no need to run `workflow code`)️
  commit (c)                          Step 2: Format code and commit changes to existing files; please manually `git add` new files
  patch (p)                           Step 3: Run a patch build in Evergreen CI.
  review (r)                          Step 4: Open a new code review (CR) or put up a new patch to an existing code review.
  ship (push, s)                      Step 5: Provide instructions on pushing your changes to master.
  zzz (z)                             Step 6: Cleanup. Remove local branches and close Jira ticket
  helpers.delete-branch (helpers.d)   Delete the current branch on the community and enterprise repos.
  helpers.format-code (helpers.f)     Format modified C++ and JavaScript code.
  helpers.upgrade                     Upgrade the workflow tool to the latest version
  setup.macos                         Set up macOS for MongoDB server development.
```
