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

evergreen_yaml_template = \
    '''
user: "{}"
api_key: "{}"
api_server_host: "https://evergreen.mongodb.com/api"
ui_server_host: "https://evergreen.mongodb.com"

projects:
- name: mongodb-mongo-master
  default: true
  alias: required
  tasks:
  - all
    '''

shell_profile_template = \
    '''
export PATH="$HOME/bin:$PATH"
alias m=workflow  # Give the workflow tool a shorter name.
    '''
