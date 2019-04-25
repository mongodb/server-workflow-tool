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
import logging
import webbrowser

from invoke import task

from serverworkflowtool import config
from serverworkflowtool.templates import evergreen_yaml_template
from serverworkflowtool.utils import get_logger


def evergreen_yaml(conf):
    # initialize Jira to get the jira user name for Evergreen.
    jira = conf.jira

    if config.EVG_CONFIG_FILE.exists():
        logging.warning('Found existing ~/.evergreen.yml, skipping adding Evergreen configuration')
        logging.warning(
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
              '\n'
              'Press any key to continue...')
        settings_url = 'https://evergreen.mongodb.com/settings'
        get_logger().info('Opening {}'.format(settings_url))
        webbrowser.open(settings_url)

        while True:
            api_key = input('Please paste the hexadecimal api_key here (without quotes): ')
            try:
                int(api_key, 16)
                break
            except ValueError as e:
                get_logger().error(e)

        evg_config = evergreen_yaml_template.format(conf.jira_user, api_key)

        with open(config.EVG_CONFIG_FILE, 'w') as fh:
            fh.write(evg_config)


@task
def macos(ctx):
    conf = config.Config()

    evergreen_yaml(conf)


