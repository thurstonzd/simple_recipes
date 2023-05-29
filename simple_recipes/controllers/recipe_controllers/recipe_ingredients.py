import re

import werkzeug
from werkzeug.datastructures import MultiDict
from flask import render_template, redirect, url_for, request, session, Response, abort, flash
import flask_login

from simple_recipes import app, login_manager
from simple_recipes.db import recipes as db
from simple_recipes.forms import RecipeForm
import simple_recipes.controllers

@app.route('/recipes/<int:recipe_id>/edit/ingredients/', methods=['POST', 'GET'])
@flask_login.login_required
def edit_recipe_ingredients(recipe_id):
    data = db.get_recipe(recipe_id)

    ...