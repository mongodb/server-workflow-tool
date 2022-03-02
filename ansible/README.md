## Per team virtual workstation configuration
### Why?
Teams sometimes (or usually) need to follow instructions to set up their virtual workstations. 
And some teams (maybe all of them) have manuals to follow. 
This tiny project tries to automate that process and take away all setup hurdle from users.

### When you add your team to `roles/teams` or edit existing team role
Please, update `roles/common` folder: add any new common task that can be shared among other teams or can be used 
by other users (as a role). This folder keeps all roles of all teams. When users can't find their team,
they'll use these common roles instead.

### Project structure

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

### Rules to make everything better
- Use lowercase when naming your team role, `"_"` instead of space. `"My awesome team"` might be good in general, 
but we prefer `"my_awesome_team"`
- Most of the time `roles` folder is what you want to support your team and anything outside this folder is 
not specific to teams. Unless you are a maintainer or have a duty to fix bugs (not related to specific teams) here, 
please do not edit any folder or file outside `roles` folder.
- Use Ansible commands instead of shell commands when possible. 
Most of the time they are idempotent, causing fewer problems.

### How to Run
Running the `setup.sh` is enough, it installs Ansible and runs playbook. Rest is handled by Ansible and roles.
