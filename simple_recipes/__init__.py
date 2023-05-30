import io

from flask import Flask
import werkzeug

from flask_wtf.csrf import CSRFProtect
from flaskext.markdown import Markdown
import flask_login
from flask_talisman import Talisman

from pint import UnitRegistry

app = Flask(__name__)
app.config['SECRET_KEY'] = b'\x98R\xcd}\xe5\xa9\xe3\x110?\x82\x11\xf2\xa7\x17\x9c'

if app.config['ENV'] == 'development':
    app.config['DATABASE_URL'] = 'host=localhost port=5432 dbname=recipes user=postgres password=admin'

csrf = CSRFProtect(app)
Markdown(app, extensions=['tables', 'def_list'])

# plugin registrations
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
Talisman(app)

#####################################################################
# Unit registry stuff

# relaxed conversion for temperatures
# see https://pint.readthedocs.io/en/stable/user/nonmult.html
ureg = UnitRegistry(autoconvert_offset_to_baseunit = True)

# define aliases for units
ureg.define('@alias fluid_ounce = fl_oz')

Q_ = ureg.Quantity
#####################################################################

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

@app.route('/robots.txt')
def robot_txt():
    return Response(    "User-agent: *\n"
                        "Disallow: /", 
                        mimetype='text/plain')

@app.route('/images/<path:file_name>')
def lightbox_image(file_name):
    return app.send_static_file(f'lightbox/{file_name}')