import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mongodb_cmdline_tool",
    version="20180702-1",
    author="Robert Guo",
    author_email="rob@mongodb.com",
    description="MongoDB Server Team Command Line Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/10gen/kernel-tools/cmdlinetool",
    packages=setuptools.find_packages(),
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3 :: Only",
        "License "" Other/Proprietary License",
        "Operating System :: MacOS :: MacOS X",
    ),
    install_requires=[
        'jira >= 1.0',
        'keyring >= 12',
        'invoke >= 1.0',
        'pyyaml >= 3.0'
    ],
    entry_points={
        'console_scripts': ['m = mongodb_cmdline_tool.__main__:main'],
    }
)