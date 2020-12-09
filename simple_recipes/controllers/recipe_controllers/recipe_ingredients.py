import re

import werkzeug
from werkzeug.datastructures import MultiDict
from flask import render_template, redirect, url_for, request, session, Response, abort, flash
import flask_login

from simple_recipes import app, login_manager
from simple_recipes.db import recipes as db
from simple_recipes.forms import RecipeForm
from simple_recipes.web_io import format_ingredients, parse_ingredient
import simple_recipes.controllers

@app.route('/recipes/<int:recipe_id>/edit/ingredients/', methods=['POST', 'GET'])
@flask_login.login_required
def edit_recipe_ingredients(recipe_id):
    data = db.get_recipe(recipe_id)

    if data['created_by'] != flask_login.current_user.id:
        flash("You can only edit recipes you've created.")
        abort(werkzeug.exceptions.Forbidden.code)

    measurement_strings = db.get_measurement_strings()
    
    formdata = session.get('formdata', None)
    tags = session.get('tag_choices', [])
    
    if formdata:
        form = RecipeForm(MultiDict(formdata))
        form.recipe_tags.choices = tags
        form.validate()
    else:
        form = RecipeForm()
    
    if form.validate_on_submit():        
        ingredient_text = form.recipe_ingredients.data.strip()
        #app.logger.info(ingredient_text)
        ingredients = [parse_ingredient(s) 
            for s in re.split(r'\n\s*', ingredient_text.strip())]
        db.update_recipe_ingredients(recipe_id, ingredients)
        
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
        ''' prepopulate fields '''
        if data['ingredients']:
            ingredient_text = format_ingredients(data)
            form.recipe_ingredients.process_data(ingredient_text)
        
        return render_template('recipes/recipe_edit_ingredients.html',
            form=form, data=data, measurement_strings=measurement_strings)