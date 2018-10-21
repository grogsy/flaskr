''' File containing the authentication blueprint for the flaskr app
    The authentication blueprint will have views to register the new users and log in/out
'''
import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    '''View function for the registration page'''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES(?,?)',
                (username, generate_password_hash(password))
            )
            # Register the user's name into the profile table as well
            db.execute(
                'INSERT INTO profile(username) VALUES(?)',
                (username,)
            )
            db.commit()
            # If successful redirect to the login page
            return redirect(url_for('auth.login'))

        flash(error)

    # GET authentication page
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    '''View function for the login page'''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user where username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    '''
    Load data from the db data for the user's session
    This loaded data persists the duration of the session
    '''
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    '''Log a user out and remove their session data'''
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    '''
    A decorator called on pages that require being logged in and checks if a user is logged in
    If no user logged in, redirect to the login page, else if there is a user
    load the original view and continue normally
    '''
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
