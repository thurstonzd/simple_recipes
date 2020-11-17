from flask import Flask
import werkzeug

from flask_wtf.csrf import CSRFProtect
from flaskext.markdown import Markdown
import flask_login

from pint import UnitRegistry

app = Flask(__name__)
app.config['SECRET_KEY'] = b'\x98R\xcd}\xe5\xa9\xe3\x110?\x82\x11\xf2\xa7\x17\x9c'

if app.config['ENV'] == 'development':
    app.config['DATABASE_URL'] = 'host=localhost port=5433 dbname=recipes user=postgres password=admin'

csrf = CSRFProtect(app)
Markdown(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

ureg = UnitRegistry()

from simple_recipes.controllers.tag_controllers import *
from simple_recipes.controllers.recipe_controllers import *
from simple_recipes.controllers.user_controllers import *
    
@app.route('/')
def index():
    return render_template('_base.html')

@app.errorhandler(werkzeug.exceptions.NotFound)
def handle_not_found(e):
    return render_template('errors/not_found.html'), \
        werkzeug.exceptions.NotFound.code

@app.errorhandler(werkzeug.exceptions.Forbidden)
def handle_forbidden(e):
    return render_template('errors/forbidden.html'), \
        werkzeug.exceptions.Forbidden.code