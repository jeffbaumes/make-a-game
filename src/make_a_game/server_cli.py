"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mmake_a_game` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``make_a_game.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``make_a_game.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import click
from .server import startServer


@click.command()
@click.option('--world', default='default')
@click.option('--seed', default=1)
@click.option('--port', default=1234)
def main(world, seed, port):
    startServer(world, seed, port)
