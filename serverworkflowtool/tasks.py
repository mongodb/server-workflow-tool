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
from invoke import task

from serverworkflowtool.utils import get_logger


@task(positional=['ticket_number'], optional=['branch', 'project'])
def new(ctx, ticket_number, project='server'):
    """
    Step 1: Create or switch to the branch for a ticket.

    :param ticket_number: Digits of the Jira ticket.
    :param project: Jira project. Default: server.
    """
    try:
        ticket_number = int(ticket_number)
    except ValueError:
        get_logger().critical('Ticket number must be an integer, got "%"', ticket_number)
        return 1
