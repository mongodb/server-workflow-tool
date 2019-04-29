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

import jira.exceptions

from serverworkflowtool import config
from serverworkflowtool.utils.log import get_logger

_server_status_map = {
    'Open': '1',
    'In Progress': '3',
    'In Code Review': '7',  # TODO: verify if 7 is correct.
    'Closed': '1000'  # TODO: figure out what this number is.
}

_server_transition_map = {
    'Start Progress': '4',
    'Start Code Review': '761',
    'Close Issue': '981'
}

# Map of statuses after transitions.
_server_transition_to_map = {
    'Start Progress': 'In Progress',
    'Start Code Review': 'In Code Review',
    'Close Issue': 'Closed'
}


def transition_ticket(ticket, from_status, transition_name):
    from_id = _server_status_map[from_status]
    transition_id = _server_transition_map[transition_name]
    to_status = _server_transition_to_map[transition_name]

    try:
        jirac = config.Config().jira
        issue = jirac.issue(ticket)

        if issue.fields.status.id == from_id:
            get_logger().info(f'Transitioning {ticket} in Jira from "{from_status}"" to {to_status}"')
            jirac.transition_issue(issue, transition_id)
        else:
            get_logger().info(f'{ticket} is not "{from_status}", skipping transition to "{to_status}"')

        return issue
    except jira.exceptions.JIRAError as e:
        get_logger().error('Failed to do transition "%s" for ticket %s due to Jira error: %s',
                           transition_name, ticket, e.text)


def add_comment(ticket, comment, **kwargs):
    try:
        jirac = config.Config().jira
        jirac.add_comment(ticket, comment, **kwargs)
    except jira.exceptions.JIRAError as e:
        get_logger().error('Failed to add comment "%s" to ticket %s due to Jira error: %s', comment, ticket, e.text)
