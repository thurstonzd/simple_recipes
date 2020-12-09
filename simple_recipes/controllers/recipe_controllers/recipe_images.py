import io

import werkzeug
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, request, session, Response, abort, flash
import flask_login
from PIL import Image
import pyqrcode

from simple_recipes import app, login_manager
from simple_recipes.db import recipes as db
from simple_recipes.forms import RecipeForm
import simple_recipes.controllers

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

@app.route('/thumbnails/<int:image_id>/<file_name>')
def get_image_thumbnail(image_id, file_name):
    img_data = db.get_recipe_image(image_id)
    img_bytes = img_data['image_bytes']
    img_file_type = img_data['file_type']

    img = Image.open(io.BytesIO(img_bytes))
    img.thumbnail((90,90))

    img_bytes = io.BytesIO()
    img.save(img_bytes, format=img.format)
    return Response(img_bytes.getvalue(), mimetype=img_file_type)

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

@app.route('/share/recipe/<int:recipe_id>/')
def share_recipe(recipe_id):
    url = url_for('get_recipe', recipe_id=recipe_id, _external=True)
    qr = pyqrcode.create(url)
    buffer = io.BytesIO()
    qr.svg(buffer, scale=4)
    return Response(buffer.getvalue(), mimetype='image/svg+xml')