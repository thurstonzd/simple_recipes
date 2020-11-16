from fractions import Fraction
import re

import werkzeug
from werkzeug.utils import secure_filename
from werkzeug.datastructures import MultiDict
from pint import UnitRegistry
from flask import render_template, redirect, url_for, request, session, Response, abort, flash
import flask_login

from simple_recipes import app, login_manager
from simple_recipes.db import recipes as db
from simple_recipes.db.tags import get_tags
from simple_recipes.unit_convert import convert_to_other_system
from simple_recipes.forms import RecipeForm, DeletionForm, RecipeConversionForm, RecipeSearchForm
from simple_recipes import ureg
from simple_recipes.web_io import format_instructions, format_ingredients, parse_instructions, parse_ingredient
import simple_recipes.controllers

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
    
    data = db.get_recipe(recipe_id, to_system, multiplier)
    if data:
        return render_template('recipes/recipe_base.html', data=data, multiplier=multiplier)
    else:
        abort(werkzeug.exceptions.NotFound.code)

@app.route('/recipes/<int:recipe_id>/convert/')
def convert_recipe(recipe_id):
    form = RecipeConversionForm()
    form.unit_system.data = "US"
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
        if data['recipe_desc']: 
            form.recipe_desc.process_data(data['recipe_desc'])
        if data['servings']:
            form.servings.data = data['servings']
        if data['total_time_minutes']:
            form.total_time_minutes.data = data['total_time_minutes']
            
        return render_template('recipes/recipe_edit_basic.html', 
                form=form, data=data)
            
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
        instructions = parse_instructions(form.recipe_instructions.data)
        db.update_recipe_instructions(recipe_id, instructions)
        
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
        if data['instructions']:
            instruction_text = format_instructions(data)
            form.recipe_instructions.process_data(instruction_text)

        return render_template('recipes/recipe_edit_instructions.html',
            form=form, data=data)
        
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
            
@app.route('/images/<int:image_id>/<file_name>')
def get_image(image_id, file_name):
    img = db.get_recipe_image(image_id)
    img_data = img['image_bytes']
    chunk_size = 255
    
    def generate():
        for chunk_start in range(0, len(img_data), chunk_size):
            yield img_data[chunk_start:chunk_start + chunk_size]
    
    # return Response(img['image_bytes'], mimetype=img['file_type'])
    return Response(generate(), mimetype=img['file_type'])
    
@app.route('/recipes/<int:recipe_id>/edit/images/', methods=['GET', 'POST'])
@flask_login.login_required
def edit_recipe_images(recipe_id):
    data = db.get_recipe(recipe_id)

    if data['created_by'] != flask_login.current_user.id:
        flash("You can only edit recipes you've created")
        abort(werkzeug.exceptions.Forbidden.code)

    form = RecipeForm()
    
    link_template = '''<img src="{}" alt="{}" />'''
    if data['images']:
        form.image_deletions.choices = [
            (img['image_id'], link_template.format(
                url_for('get_image', 
                    image_id=img['image_id'], 
                    file_name=img['image_file_name']),
                img['image_desc']))
            for img in data['images']]
    
    if form.validate_on_submit():
        images_to_delete = form.image_deletions.data
        if images_to_delete: db.delete_recipe_images(images_to_delete)
        
        files = request.files.getlist(form.image_uploads.name)
        file_descriptions = form.image_descriptions.data.split('\n')
        
        if len(files) != len(file_descriptions):
            flash('Some files were missing descriptions')
            return redirect(request.url)
        elif files:
            file_list = []
            for i, f in enumerate(files):
                if f.filename:
                    d = {}
                    d['image_file_name'] = secure_filename(f.filename)
                    d['file_type'] = f.mimetype
                    d['image_desc'] = file_descriptions[i]
                    d['image_bytes'] = f.read()
                    file_list.append(d)
            
            db.add_recipe_images(recipe_id, file_list)
            
        return redirect(url_for('get_recipe', recipe_id=recipe_id))
                
    else:
        return render_template('recipes/recipe_edit_images.html', 
            form=form, data=data)