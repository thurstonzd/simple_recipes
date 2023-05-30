import werkzeug
from flask import render_template, redirect, url_for, request, session, Response, abort, flash
import flask_login

from simple_recipes import app, login_manager

from simple_recipes.db import get_measurement_units, get_unit_strings
from simple_recipes.db.recipes import get_recipe
from simple_recipes.db.tags import get_tags

from simple_recipes.unit_conversion import parse_quantity_string, convert_quantity, convert_recipe_text

from simple_recipes.forms import RecipeForm, RecipeConversionForm, RecipeSearchForm, DeletionForm
import simple_recipes.controllers
from simple_recipes.controllers.recipe_controllers.recipe_images import *
from simple_recipes.controllers.recipe_controllers.recipe_ingredients import *
from simple_recipes.controllers.recipe_controllers.recipe_instructions import *
from simple_recipes.controllers.recipe_controllers.recipe_tags import *

@app.route('/recipes/')
def search_recipes():
    form = RecipeSearchForm()

    search = request.args.get('what', '')
    opt = request.args.get('how', '')
    tsquery = ''
    
    if opt.upper() == 'ALL':
        tsquery = ' & '.join(search.split())
    elif opt.upper() == 'ANY':
        tsquery = ' | '.join(search.split())
    else:
        tsquery = search
        
    recipes, count = None, 0
    if tsquery:
        recipes = db.get_recipes(tsquery)
        count = len(recipes)
        form.how.data = opt
        form.what.data = search
    else: form.how.data = 'all'
        
    return render_template('recipes/recipe_search.html', 
        recipes=recipes, form=form, count=count)
        
@app.route('/recipes/<int:recipe_id>/')
@app.route('/recipes/<int:recipe_id>/<path:subpath>')
def get_recipe(recipe_id, subpath=None):
    multiplier = request.args.get('multiplier', default=1, type=float)
    to_system = request.args.get('unit_system', default=None)
    
    formdata = None
    if 'formdata' in session: formdata = session.pop('formdata')
    if 'pages' in session: session.pop('pages')
    
    data = db.get_recipe(recipe_id)
    if data:
        units = get_measurement_units()
        data['servings'] *= multiplier
        data['ingredients'] = convert_recipe_text(
            data['ingredients'], 
            multiplier=multiplier, 
            to_system=to_system,
            units=units,
            quantity_tag='span',
            Class="quantity")

        return render_template('recipes/recipe_base.html', data=data)
    else:
        abort(werkzeug.exceptions.NotFound.code)

@app.route('/recipes/<int:recipe_id>/convert/')
def convert_recipe(recipe_id):
    form = RecipeConversionForm()
    form.unit_system.data = "N/A"
    data = db.get_recipe(recipe_id)
    return render_template('recipes/recipe_convert.html', form=form, data=data)
        
@app.route('/recipes/add/', methods=['GET', 'POST'])
@flask_login.login_required
def add_recipe():
    form = RecipeForm()
    
    tags = [(t['tag_id'], t['tag_name']) for t in get_tags()]
    form.recipe_tags.choices = tags
            
    measurement_strings = db.get_measurement_strings()
    
    if form.validate_on_submit():
        recipe_id = db.update_recipe_basic(form.data)
        session['formdata'] = request.form
        session['pages'] = [
            'edit_recipe_ingredients', 
            'edit_recipe_instructions', 
            'edit_recipe_tags']
        session['tag_choices'] = tags
            
        return redirect(url_for(session['pages'].pop(0), 
            recipe_id=recipe_id), code=307)
    else:
        form.created_by.data = flask_login.current_user.id
        return render_template('recipes/recipe_add.html', 
            form=form, measurement_strings=measurement_strings)
    
@app.route('/recipes/<int:recipe_id>/edit/', methods=['GET', 'POST'])
@app.route('/recipes/<int:recipe_id>/edit/basic/', methods=['GET', 'POST'])
@flask_login.login_required
def edit_recipe_basic(recipe_id):
    data = db.get_recipe(recipe_id)

    if data['created_by'] != flask_login.current_user.id:
        flash("You can only edit recipes you've created")
        abort(werkzeug.exceptions.Forbidden.code)

    form = RecipeForm()
    
    form.recipe_name.flags.required = True
    form.servings.flags.required = True
    
    if form.validate_on_submit():
        data = form.data
        data.update({"recipe_id": recipe_id})
        db.update_recipe_basic(data)
        return redirect(url_for('get_recipe', recipe_id=recipe_id))
    else:
        # prepopulate fields
        form.created_by.data = flask_login.current_user.id
        if data['recipe_desc']: 
            form.recipe_desc.process_data(data['recipe_desc'])
        if data['servings']:
            form.servings.data = data['servings']
        if data['total_time_minutes']:
            form.total_time_minutes.data = data['total_time_minutes']
            
        return render_template('recipes/recipe_edit_basic.html', 
                form=form, data=data)

@app.route('/recipes/<int:recipe_id>/delete/', methods=['POST', 'GET'])
@flask_login.login_required
def delete_recipe(recipe_id):

    data = db.get_recipe(recipe_id)

    if data['created_by'] != flask_login.current_user.id:
        flash("You can only delete recipes you've created")
        abort(werkzeug.exceptions.Forbidden.code)

    form = DeletionForm()
    if form.validate_on_submit():
        db.delete_recipe(recipe_id)
        return redirect(url_for('search_recipes'))
    else:
        recipe = db.get_recipe(recipe_id)
        return render_template('recipes/recipe_delete.html',
            data=recipe, form=form)
            