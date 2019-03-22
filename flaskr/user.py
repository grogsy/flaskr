'''
File containing the user profile blueprint for the flaskr app
The user blueprint will have views to profile pages and the information on them
'''

import os

from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort

from flaskr.db import get_db
from flaskr.auth import login_required

bp = Blueprint('user', __name__, url_prefix='/user')

VALID_EXTENSIONS = set('jpg jpeg png'.split())
IMG_DESTINATION = os.sep+'static'+os.sep+'img'


@bp.route('/<string:user>', methods=('GET',))
def view_user(user):
    '''View for individual user pages'''
    db = get_db()
    username = db.execute(
        'SELECT id FROM user WHERE username = ?',
        (user,)
    ).fetchone()

    profile_info = db.execute(
        'SELECT username, photo, join_date, bio'
        ' FROM profile'
        ' WHERE username = ?',
        (user,)
    ).fetchone()

    return render_template('user/profile.html', user=username, profile=profile_info)


@bp.route('/<string:user>/update', methods=('GET', 'POST'))
@login_required
def update_profile(user):
    '''View for modifying information on the user page'''
    db = get_db()

    this_user = db.execute('SELECT id from user WHERE username = ?',
            (user,)
    ).fetchone()

    if this_user['id'] != g.user['id']:
        abort(403)

    profile_info = db.execute(
        'SELECT username, bio, photo FROM profile WHERE username = ?',
        (user,)
    ).fetchone()

    old_photo = profile_info['photo']

    if request.method == 'POST':
        bio = request.form['bio']
        if 'file' not in request.files:
            filename = old_photo
        else:
            photo = request.files['file']
            filename = photo.filename
            if filename == '' or not allowed_file(filename):
                abort(422)
            filename = secure_filename(filename)

            # source:
            #   best answer of https://stackoverflow.com/questions/30836690/flask-odd-behavior-w-folder-creation-file-uploading
            # Very dirty filepath management hacking
            path = os.path.dirname(os.path.abspath(__file__)) + IMG_DESTINATION
            if not os.path.exists(path):
                os.makedirs(path)
            current_app.config["UPLOAD_FOLDER"] = path
            # End dirty filepath management hacking
            # I believe I can define this outside of the function call

            photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

        db.execute(
            'UPDATE profile set bio = ?, photo = ? WHERE username = ?',
            (bio, filename, user)
        )
        db.commit()
        return redirect(url_for('user.view_user', user=user))

    return render_template('user/update_profile.html', profile=profile_info)


def allowed_file(filename):
    '''Validate if the file has a proper extension'''
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in VALID_EXTENSIONS
