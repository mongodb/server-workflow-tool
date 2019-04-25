# Copyright 2019 MongoDB Inc.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="server_workflow_tool",
    version="1.0.1",
    description="MongoDB Server Team Workflow Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mongodb/server-workflow-tool",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: Apache Software License",
    ],
    install_requires=[
        'jira == 2.0.0',
        'keyring == 19.0.1',
        'invoke == 1.2.0',
        'pyyaml == 5.1'
    ],
    entry_points={
        'console_scripts': ['workflow = serverworkflowtool.__main__:run'],
    }
)
