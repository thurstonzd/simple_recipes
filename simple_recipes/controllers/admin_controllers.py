from flask import render_template, redirect, url_for, flash

import flask_login

import scrypt

from simple_recipes import app, login_manager
from simple_recipes.db.users import *
from simple_recipes.forms import UserForm