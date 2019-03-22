'''
File containing the blog blueprint for the flaskr app
The blog blueprint will have views to see, create, and edit blog posts
'''
from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    '''Homepage for the website'''
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    '''View for creating new posts'''
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post(title, body, author_id)'
                'VALUES (?,?,?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(_id, check_author=True):
    '''Fetch a single post. Used in the views: update, delete, and show_post'''
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (_id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(_id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    '''View for modifying an existing post'''

    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                'WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    '''callback function for deleting a post. This function does not have its own view
    as it is accessed via the update view'''
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>', methods=('GET', 'POST'))
def show_post(id):
    '''Display a single post on a separate page from the index
    If the request method is a POST then a comment was posted'''

    # Grab the individual post
    post = get_post(id, check_author=False)
    # Grab all the comments for this post
    comments = get_db().execute(
        'SELECT id, comment_text, poster, created'
        '  FROM comments'
        '  WHERE post_id = ?',
        (id,)
    ).fetchall()

    if request.method == 'POST':
        if g.user is None:
            return redirect(url_for('auth.login'))
        comment_text = request.form['comment']
        error = None

        if not comment_text:
            error = 'Cannot post empty comment'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO comments'
                '  (post_id, comment_text, poster)'
                '  VALUES(?,?,?)',
                (id, comment_text, g.user['username'])
            )
            db.commit()
            return redirect(url_for('blog.show_post', id=id))

    return render_template('blog/content.html', post=post, comments=comments)


@bp.route('/<int:post_id>/<int:id>/delete_comment', methods=('POST',))
def delete_comment(id, post_id):
    '''Function to allow a user to delete a comment from a blog post
        This function does not have its own view it is accessed and visible
        only to users on the comments they have made on a post
    '''
    db = get_db()
    db.execute('DELETE FROM comments WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.show_post', id=post_id))


@login_required
@bp.route('/<int:post_id>/<int:id>/edit_comment', methods=('POST', 'GET'))
def edit_comment(post_id, id):
    '''View that allows users to edit comments they make to posts'''
    db = get_db()
    comment = db.execute(
        'SELECT comment_text FROM comments where id = ?',
        (id,)).fetchone()

    if request.method == 'POST':
        comment_text = request.form['comment_text']
        db.execute(
            'UPDATE comments set comment_text = ?'
            '   WHERE id = ?',
            (comment_text, id)
        )
        db.commit()
        return redirect(url_for('blog.show_post', id=post_id))

    return render_template('blog/edit_comment.html', comment=comment)
