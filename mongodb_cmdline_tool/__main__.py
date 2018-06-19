#! /usr/bin/env python3

from invoke import Program, Collection

from mongodb_cmdline_tool import setupenv
from mongodb_cmdline_tool import tasks


def main():
    config = {
        'run': {
            'echo': True
        },
        'NINJA_STATUS': '[%f/%t (%p) %es]'  # make the ninja output even nicer
    }

    ns = Collection.from_module(tasks, config=config)
    ns.add_collection(Collection.from_module(setupenv, name='setup-dev-env', config=config))

    p = Program(
        binary='m(mongodb command line tool)',
        name='MongoDB Command Line Tool',
        namespace=ns,
        version='1.0.0-alpha2')

    p.run()
