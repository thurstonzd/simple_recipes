import werkzeug
from werkzeug.datastructures import MultiDict
from flask import render_template, redirect, url_for, request, session, Response, abort, flash
import flask_login

from simple_recipes import app, login_manager
from simple_recipes.db import recipes as db
from simple_recipes.db.tags import get_tags
from simple_recipes.forms import RecipeForm
import simple_recipes.controllers

@app.route('/recipes/<int:recipe_id>/edit/tags/', methods=['POST', 'GET'])
@flask_login.login_required
def edit_recipe_tags(recipe_id):
    data = db.get_recipe(recipe_id)

    if data['created_by'] != flask_login.current_user.id:
        flash("You can only edit recipes you've created")
        abort(werkzeug.exceptions.Forbidden.code)
    
    formdata = session.get('formdata', None)
    tags = session.get('tag_choices', [])
    
    if formdata:
        form = RecipeForm(data=MultiDict(formdata))
        form.recipe_tags.choices = tags
        form.validate()
    else:
        form = RecipeForm()
    
    if not tags:
        tags = get_tags()
    
    form.recipe_tags.choices = [
        (t['tag_id'], t['tag_name']) for t in get_tags()]
    
    if form.validate_on_submit():
        db.update_recipe_tags(recipe_id, form.recipe_tags.data)
        
        pages = session.get('pages', None)
        if pages:
            page = pages.pop(0)
            session['pages'] = pages
            return redirect(url_for(page, 
                recipe_id=recipe_id), code=307)
        else:
            return redirect(url_for('get_recipe', recipe_id=recipe_id))
    else:
        if 'formdata' in session: session.pop('formdata')
        if 'pages' in session: session.pop('pages')
        # prepopulate fields
        if data['tags']:
            form.recipe_tags.data = [tag['tag_id'] for tag in data['tags']]
            
        return render_template('recipes/recipe_edit_tags.html', 
            form=form, data=data)