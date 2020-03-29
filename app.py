from flask import render_template, flash, redirect, url_for, request, Flask, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from werkzeug.exceptions import BadRequest
from config import Config
import boto3
import os
import copy

app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'png', 'txt', 'py', 'ipynb']
client = boto3.client('s3')
uploads_dir = 'uploads'
NUM_MODULES = 5
MAX_SUBMODULES = 5
NUM_SUBMODULES = [5, 3, 5, 2, 1]

modules = [{"name" : "Analytics", "number" : "1", "description" : "this is the description", 
            "exercise": "https://mybinder.org/v2/gist/kkalucha/f9cf740f5371c15163c2229c701891ce/master",
            "submodules": [{"name" : "Supervised Machine Learning", "number" : "1", "description" : "this is ML but supervised"},
                           {"name" : "Supervised Machine Learning", "number" : "2", "description" : "this is the second ML"},
                           {"name" : "supervised machine learning", "number" : "3", "description" : "this is third one"},
                           {"name" : "supervised machine learning", "number" : "4", "description" : "this is fourth one"},
                           {"name" : "supervised machine learning", "number" : "5", "description" : "this is fifth one"}]},
            {"name" : "Analytics", "number" : "2", "description" : "this is the description", 
            "exercise": "https://mybinder.org/v2/gist/kkalucha/f9cf740f5371c15163c2229c701891ce/master",
            "submodules": [{"name" : "Supervised Machine Learning", "number" : "1", "description" : "this is ML but supervised"},
                           {"name" : "Supervised Machine Learning", "number" : "2", "description" : "this is the second ML"},
                           {"name" : "supervised machine learning", "number" : "3", "description" : "this is third one"}]},
            {"name" : "Analytics", "number" : "3", "description" : "this is the description", 
            "exercise": "https://mybinder.org/v2/gist/kkalucha/f9cf740f5371c15163c2229c701891ce/master",
            "submodules": [{"name" : "Supervised Machine Learning", "number" : "1", "description" : "this is ML but supervised"},
                           {"name" : "Supervised Machine Learning", "number" : "2", "description" : "this is the second ML"},
                           {"name" : "supervised machine learning", "number" : "3", "description" : "this is third one"},
                           {"name" : "supervised machine learning", "number" : "4", "description" : "this is fourth one"},
                           {"name" : "supervised machine learning", "number" : "5", "description" : "this is fifth one"}]},
            {"name" : "Analytics", "number" : "4", "description" : "this is the description", 
            "exercise": "https://mybinder.org/v2/gist/kkalucha/f9cf740f5371c15163c2229c701891ce/master",
            "submodules": [{"name" : "Supervised Machine Learning", "number" : "1", "description" : "this is ML but supervised"},
                           {"name" : "Supervised Machine Learning", "number" : "2", "description" : "this is the second ML"}]},
            {"name" : "Analytics", "number" : "5", "description" : "this is the description", 
            "exercise": "https://mybinder.org/v2/gist/kkalucha/f9cf740f5371c15163c2229c701891ce/master",
            "submodules": [{"name" : "Supervised Machine Learning", "number" : "1", "description" : "this is ML but supervised"}]}]

from models import User
from models import Comment

def get_user_module(module_number):
    module_dict = copy.deepcopy(modules[module_number])
    module_dict['locked'] = current_user.locked[module_number]
    module_dict['hascomments'] = current_user.hascomments[module_number]
    if module_dict['hascomments']:
        module_dict['comments'] = Comment.query.filter_by(username=current_user.username, module=module_number)
    for i in range(NUM_SUBMODULES[module_number]):
        module_dict['submodules'][i]['locked'] = current_user.locked_sub[module_number][i]
    return module_dict

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('homepage'))
        return render_template('login.jinja2')
    
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({'errors':'invalid username/password'})
    login_user(user)
    return jsonify({})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('homepage'))
        return render_template('signup.jinja2')
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    user = User.query.filter((User.username == username) | (User.email == email)).first()
    if user is not None:
        return jsonify({'errors':'user already exists'})
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    university = request.form.get('university')
    dob = request.form.get('dob')
    major = request.form.get('major')
    program = request.form.get('program')
    locked = [([False] + [True] * (MAX_SUBMODULES - 1))] + [ ([True] * MAX_SUBMODULES) for i in range(NUM_MODULES) ]
    user = User(username=username, email=email, firstname=firstname, lastname=lastname, university=university,\
                dob=dob, major=major, program=program, completed=[False] * NUM_MODULES,\
                locked=([False] + [True] * (NUM_MODULES - 1)), hascomments=[False] * NUM_MODULES,\
                locked_sub=locked, current_module=0)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({})
    
@app.route('/homepage', methods=['GET', 'POST'])
@login_required
def homepage():
    ann = {"title": "Program Kickoff", "description": "Join us on Zoom for our first bonding event! Meet other students in the program."}
    module_dict = get_user_module(current_user.current_module)
    cur = 0
    for i in range(NUM_SUBMODULES[current_user.current_module]):
        if module_dict['submodules'][i]['locked']:
            cur = i
            break
    progress = int(100 * (sum(NUM_SUBMODULES[0:current_user.current_module], cur)/sum(NUM_SUBMODULES)))
    prev = None
    if current_user.current_module > 0:
        prev = get_user_module(current_user.current_module - 1)
    nex = None
    if current_user.current_module < NUM_MODULES - 1:
        nex = get_user_module(current_user.current_module + 1)
    return render_template('homepage.jinja2', ann=ann, progress=progress, prev=prev, curr=module_dict, next=nex)

@app.route('/modules')
@login_required
def modules_route():
    return render_template('modules.jinja2', all_modules=[get_user_module(i) for i in range(NUM_MODULES)])

@app.route('/modules/<int:module_number>')
@login_required
def module(module_number):
    if module_number < 1 or module_number > NUM_MODULES or current_user.locked[module_number - 1]:
        abort(404)
    return render_template('module.jinja2', module=get_user_module(module_number - 1))

@app.route('/modules/<int:module_number>/<int:submodule_number>/<kind>')
@login_required
def submodule(module_number, submodule_number, kind):
    if module_number < 1 or module_number > NUM_MODULES or submodule_number < 1 or submodule_number > NUM_SUBMODULES[module_number - 1]\
    or current_user.locked_sub[module_number - 1][submodule_number - 1]:
        abort(404)
    return render_template('submodule.jinja2', module_number=module_number, submodule_number=submodule_number, kind=kind)


@app.route('/notebook/<notebook_name>')
@login_required
def notebook(notebook_name):
    return render_template("notebooks/" + notebook_name)

@app.route('/submit', methods=['POST'])
@login_required
def submit_file():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"errors":"no file attached"})
    if not allowed_file(file.filename):
        return jsonify({"errors":"invalid file type"})
    filename = secure_filename(file.filename)
    file.save(os.path.join(uploads_dir, filename))
    key = current_user.username + "_" + request.form.get("module") + "." + filename.rsplit('.', 1)[1].lower()
    client.upload_file(os.path.join(uploads_dir, filename), 'online-portal', key)
    return jsonify({})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('page-not-found.jinja2')
    
if __name__ == "__main__":
   app.run(debug = True)
