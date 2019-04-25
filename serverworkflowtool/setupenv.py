#  Copyright 2019 MongoDB Inc.
#
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.
import webbrowser

from invoke import task

from serverworkflowtool import config
from serverworkflowtool.templates import evergreen_yaml_template
from serverworkflowtool.utils import get_logger, instruction


def evergreen_yaml(conf):
    # initialize Jira to get the jira user name for Evergreen.
    jira = conf.jira

    if config.EVG_CONFIG_FILE.exists():
        get_logger().info(
            'Found existing ~/.evergreen.yml, skipping adding Evergreen configuration')
        get_logger().info(
            'Please make sure your Evergreen config file contains your API credentials and'
            ' a default project configuration of mongodb-mongo-master.')

    else:
        input('\n'
              'Opening browser to configure Evergreen credentials. Please paste the content\n'
              'of hexadecimal string for the key "api_key" in the top left box.\n'
              '\n'
              'E.g. You will see a text box that resembles the following:\n'
              '\n'
              'user: "jane.doe"\n'
              'api_key: "1234567890abcdef123456"\n'
              'api_server_host: "https://evergreen.mongodb.com/api"\n'
              'ui_server_host: "https://evergreen.mongodb.com"\n'
              '\n'
              'Please copy and paste the string "1234567890abcdef123456" (without quotes). You '
              'may be redirected to a login page first if you\'re not logged in in your '
              'operating system\'s default browser'
              '\n' +
              instruction('Press any key to continue...'))
        settings_url = 'https://evergreen.mongodb.com/settings'
        get_logger().info('Opening {}'.format(settings_url))
        webbrowser.open(settings_url)

        while True:
            api_key = input(
                instruction('Please paste the hexadecimal api_key here (without quotes): '))
            try:
                int(api_key, 16)
                break
            except ValueError as e:
                get_logger().error(e)

        evg_config = evergreen_yaml_template.format(conf.username, api_key)

        with open(config.EVG_CONFIG_FILE, 'w') as fh:
            fh.write(evg_config)


def ssh_keys(ctx):
    if config.SSH_KEY_FILE.is_file():
        get_logger().info(
            'Found existing key ~/.ssh/id_rsa, skipping setting up ssh keys. Please ensure'
            'your keys are added to your GitHub account')
        return

    res = input(instruction('Opening browser for instructions to setting up ssh keys in GitHub, '
                            'press any key to continue, enter "skip" to skip: '))
    if res != 'skip':
        webbrowser.open(config.GITHUB_SSH_HELP_URL)
        input(
            'Once you\'ve generated SSH keys and added them to GitHub, press any key to continue')
    else:
        get_logger().info('Skipping adding SSH Keys to GitHub')

    while not (config.SSH_KEY_FILE.is_file()):
        get_logger().error(
            str(config.SSH_KEY_FILE) + ' is not a file, please double check you have completed '
                                       'GitHub\'s guide on setting up SSH keys')


def clone_repos(ctx):


@task
def macos(ctx):
    conf = config.Config()

    # evergreen_yaml(conf)
    # ssh_keys(ctx)

