import werkzeug
from werkzeug.datastructures import MultiDict
from flask import render_template, redirect, url_for, request, session, Response, abort, flash
import flask_login

from simple_recipes import app, login_manager
from simple_recipes.db import recipes as db
from simple_recipes.forms import RecipeForm
import simple_recipes.controllers

@app.route('/recipes/<int:recipe_id>/edit/instructions/', methods=['POST', 'GET'])
@flask_login.login_required
def edit_recipe_instructions(recipe_id):
    data = db.get_recipe(recipe_id)

    if data['created_by'] != flask_login.current_user.id:
        flash("You can only edit recipes you've created")
        abort(werkzeug.exceptions.Forbidden.code)

    formdata = session.get('formdata', None)
    tags = session.get('tag_choices', [])
    
    if formdata:
        form = RecipeForm(MultiDict(formdata))
        form.recipe_tags.choices = tags
        form.validate()
    else:
        form = RecipeForm()
    
    if form.validate_on_submit():
        ...
    else:
        # pre-populate fields
        # move along to next part of adding new recipe if necessary
        ...