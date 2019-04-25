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
