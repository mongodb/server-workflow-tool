# Per team virtual workstation configuration
## Why?
Teams sometimes (or usually) need to follow instructions to set up their virtual workstations. 
And some teams (maybe all of them) have manuals to follow. 
This tiny project tries to automate that process and take away all setup hurdle from users.

## When you add your team to `roles/teams` or edit existing team role
Please, update `roles/common` folder: add any new common task that can be shared among other teams or can be used 
by other users (as a role). This folder keeps all roles of all teams. 
If a user can't find their team, please create a new one on top of the common roles shared by all teams.

## Rules to make everything better
- Use lowercase when naming your team role, `"_"` instead of space. `"My awesome team"` might be good in general, 
but we prefer `"my_awesome_team"`
- Most of the time `roles` folder is what you want to support your team and anything outside this folder is 
not specific to teams. Unless you are a maintainer or have a duty to fix bugs (not related to specific teams) here, 
please do not edit any folder or file outside `roles` folder.
- Use Ansible commands instead of shell commands when possible. 
Most of the time they are idempotent, causing fewer problems.

## Project structure

`* name - DO NOT EDIT`
```
 roles / teams /  # add your team as a role here
       |        - team1
       |        - team2
       |        - ...
       / common / # add your new tasks as roles here to share with others
                - custom-role1
                - custom-role2
                - ...
* tasks /
        - * task1.yml
        - * task2.yml
        - * ...
vars / main.yml  # configuration. can be modified to tweak the flow.
* start.yml  # main entry point for ansible      
```

# Install Ansible
If you are new to Ansible, this video will give you a good sense of what it is: [quick start](https://www.ansible.com/resources/videos/quick-start-video).

Easiest way to install Ansible is via `pip`

```> pip install ansible```

For other options, check [this guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-ansible).

# How to add a new role
A role is a collection of tasks targeted to a specific goal. Role can have its own variables, tasks, templates, tests
and more. [Here](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html#role-directory-structure) 
is the list of directories (complete structure) inside a single role.

1. Create a folder for your role. Please, follow the [naming convention](#rules-to-make-everything-better).
2. Create `tasks` folder inside your role folder, and `main.yml` file inside this `tasks` folder.
3. You can see `hello-world` role inside `common` folder to get sense of how a simple role looks like.
4. Break your whole process into small tasks, and create separate files inside `tasks` folder for each of them.
5. Inside your `tasks/main.yml` file, orchestrate all those tasks, in short, control flow goes there.
6. Try to make your tasks independent of your role. It helps to add them to `common` folder for other teams to use later.
7. And yes, please, try to add your individual tasks as a role to `common` folder, so that other teams can use them. This is optional, but is highly appreciated.

## Add a team role
1. Follow all the steps to create a regular role, described in [How to add a new role](#how-to-add-a-new-role) section.
2. Your new role will be located inside `roles/teams` folder, since you are adding a team role.

## Add a common role
1. Follow all the steps to create a regular role, described in [How to add a new role](#how-to-add-a-new-role) section.
2. Your new role will be located inside `roles/common` folder, since it is a common role.

## Integrate third-part roles
Ansible has a [Galaxy](https://galaxy.ansible.com) service which provides collection of custom roles for different purposes.
If you want your role to use any third-party roles from Ansible Galaxy, you can do it by following these steps:
1. Add your third-party role to `requirements.yml`, by following [these rules](https://docs.ansible.com/ansible/latest/galaxy/user_guide.html#installing-multiple-roles-from-a-file). You can also check existing `requirements.yml` to get a sense of how it is done.
2. New role will be installed inside `roles/third-party` folder.
3. Include or import that role inside your task. One example of doing that can be found inside `roles/common/setup-oh-my-zsh/tasks/main.yml`, it uses `oh-my-zsh` third-party role.

## How to register my new role so that it appears in roles list?
**Answer:** you don't. This project is pretty much handles this kind of stuff automatically. You only need to create specific role(s) 
inside required folder. That's it. There is a small part of the script which automatically lists everything in those 
directories and shows to users, so, no need to do anything else. Just make sure that your role works and does it correctly.

# How to Run
You may want to give necessary permissions to `setup.sh`. Most of the time, below command does it:

```> sudo chmod +x ansible/setup.sh```

Running the `setup.sh` is enough, it installs Ansible and runs playbook. Rest is handled by Ansible and roles.

```> ansible/setup.sh```

## Local development
While doing local development and trying to see if things are working, you wouldn't want to use `setup.sh` all the time, 
since it installs Ansible each time. Instead, you can just run `start.yml`, like this:
1. If you are not inside `ansible` folder, go into it first: 

```> cd ansible```
2. Run the following command:

```> ansible-playbook --become-user $(whoami) --become start.yml```
