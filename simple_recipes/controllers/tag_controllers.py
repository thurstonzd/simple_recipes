from flask import render_template, redirect, url_for, flash, abort
import flask_login
import werkzeug

from simple_recipes import app, login_manager
from simple_recipes.db import tags as db
from simple_recipes.forms import TagForm, DeletionForm

@app.route('/tags/')
def get_tags():
    tags = db.get_tags()
    return render_template('tags/tag_list.html', tags=tags)
    
@app.route('/tags/<int:tag_id>/view/')
@app.route('/tags/<int:tag_id>/')
def get_tag(tag_id):
    tag = db.get_tag(tag_id)
    if tag:
        return render_template('tags/tag_details.html', tag=tag)
    else: abort(werkzeug.exceptions.NotFound.code)

@app.route('/tags/add/', methods=['POST', 'GET'])
@flask_login.login_required
def add_tag():
    form = TagForm()

    if form.validate_on_submit():
        user_name = flask_login.current_user.id
        tag_name = form.tag_name.data
        tag_desc = form.tag_desc.data
        tag_id = db.add_tag(tag_name, tag_desc=tag_desc, user_name=user_name)
        return redirect(url_for('get_tag', tag_id=tag_id))
    return render_template('tags/tag_add.html', form=form)
    
@app.route('/tags/<int:tag_id>/edit/', methods=['POST', 'GET'])
@flask_login.login_required
def edit_tag(tag_id):
    tag = db.get_tag(tag_id)
    if tag['created_by'] != flask_login.current_user.id:
        flash("You can only edit tags you've created")
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        new_name = form.tag_name.data
        new_desc = form.tag_desc.data
        db.update_tag(tag_id, new_name, new_desc)
        return redirect(url_for('get_tag', tag_id=tag_id))
    else:
        # prepopulate fields
        tag = db.get_tag(tag_id)
        
        if tag['tag_desc']: form.tag_desc.process_data(tag['tag_desc'])
        form.tag_name.data = tag['tag_name']
        
        return render_template('tags/tag_edit.html', tag=tag, form=form)
        
@app.route('/tags/<int:tag_id>/delete/', methods=['POST', 'GET'])
@flask_login.login_required
def delete_tag(tag_id):
    tag = db.get_tag(tag_id)
    if tag['created_by'] != flask_login.current_user.id:
        flash("You can only edit tags you've created")
        abort(403)

    form = DeletionForm()
    if form.validate_on_submit():
        db.delete_tag(tag_id)
        return redirect(url_for('get_tags'))
    else:
        tag = db.get_tag(tag_id)
        return render_template('tags/tag_delete.html', 
            tag=tag, form=form)