import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    '''Returns-->database object'''
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


# The click decorator registers this function to run from the commandline with flask
# as an option eg. 'flask init-db'
@click.command('init-db')
@with_appcontext
def init_db_command():
    '''Clear the existing data and create new tables from the commandline'''
    init_db()
    click.echo('Initialized the database')


def init_app(app):
    '''Register db functions to the app'''
    # Register the close_db() function as a teardown function for the app
    # This makes close_db() run whenever the app is finished returning a response
    app.teardown_appcontext(close_db)
    # add a new command that can be called with the flask command
    # ie. >flask init-db (in this case)
    app.cli.add_command(init_db_command)
