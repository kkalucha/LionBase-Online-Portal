from flask import render_template, flash, redirect, url_for, request, Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from werkzeug.exceptions import BadRequest
from config import Config
import boto3
import os

app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'png', 'txt']
client = boto3.client('s3')
uploads_dir = 'uploads'
VALID_MODULES = [1, 2, 3, 4, 5]
import models

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
    user = models.User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({'errors':'invalid username/password'})
    login_user(user)
    return jsonify({})

@app.route('/logout')
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
    user = models.User.query.filter((User.username == username) | (User.email == email)).first()
    if user is not None:
        return jsonify({'errors':'user already exists'})
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    university = request.form.get('university')
    dob = request.form.get('dob')
    major = request.form.get('major')
    program = request.form.get('program')
    user = User(username=username, email=email, firstname=firstname, lastname=lastname, university=university,
                dob=dob, major=major, program=program)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({})
    

@app.route('/homepage', methods=['GET', 'POST'])
# @login_required
def homepage():
    ann = {"title": "Program Kickoff", "description": "Join us on Zoom for our first bonding event! Meet other students in the program."}
    #progress in terms of percent
    progress = 25
    modules = {
            "prev": {"completed": True, "number": 2.2, "name": "javascript basics", "description": "APIs, databases (SQL, NoSQL, GraphQL), queries, foreign key constraints, inheritance, ACID properties", "tutorial": "tutorial", "hascomments": True, "comments": ["great job", "keep up the good work"]},
            "curr": {"completed": False, "number": 2.3, "name": "machine learning basics", "description": "APIs, databases (SQL, NoSQL, GraphQL), queries, foreign key constraints, inheritance, ACID properties", "tutorial": "tutorial", "hascomments": True, "comments": ["great job", "keep up the good work"]},
            "next": {"completed": False, "number": 2.4, "name": "product management basics", "description": "APIs, databases (SQL, NoSQL, GraphQL), queries, foreign key constraints, inheritance, ACID properties", "tutorial": "tutorial", "hascomments": True, "comments": ["great job", "keep up the good work"]}
        }

    return render_template('homepage.jinja2', ann=ann, progress=progress, prev=modules["prev"], curr=modules["curr"], next=modules["next"])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def valid_module(module_number):
	return module_number in VALID_MODULES

@app.route('/modules/<module_number>')
def module(module_number):
    module = {"name": "Analytics",
              "number" : "1",
              "locked": False,
                "submodules": [{"locked":False,"name" : "Supervised Machine Learning", "number" : "1.1", "description":"this is ML but supervised", "theory_url": "theory_url2", "case_url": "case_urlll"},
        {"locked":False, "name" : "Unupervised Machine Learning", "number" : "1.2", "description":"ML but wait there be no supervision", "theory_url":"theory_url2", "case_url": "case_urlll"},
        {"locked":True, "name" : "Optimisation", "number" : "1.3", "description": "now we optimise", "theory_url":"theory_url2", "case_url": "case_urlll"}],
                "exercises": "https://mybinder.org/v2/gist/kkalucha/f9cf740f5371c15163c2229c701891ce/master" }

    return render_template('module.jinja2', module=module)

@app.route('/submodules/theory/<submodule_number>')
def theory(submodule_number):
    return render_template('submodule.jinja2', submodule_number=submodule_number, type="theory");

@app.route('/submodules/case/<submodule_number>')
def case(submodule_number):
    return render_template('submodule.jinja2', submodule_number=submodule_number, type="case");

@app.route('/modules')
def modules():

    all_modules = [
         {"completed": "true",
                    "locked": "false",
                     "number": "1",
                      "name": "capture / maintain / process",
                      "submodules":["using an api", "databases", "datacleaning"],
                      "exercises": ["module 1 - assignment.html"],
                      "hascomments": "true",
                      "comments":["great job", "keep up the good work"]},

        {"completed": "true",
                     "locked": "false",
                     "number": "2",
                     "name": "Analytics: Supervised Learning",
                     "submodules": ["using an api", "databases", "datacleaning"],
                     "exercises": ["module 1 - assignment.html"],
                     "hascomments": "true",
                     "comments": ["great job", "keep up the good work"]},

         {"completed": "false",
                     "locked": "false",
                     "number": "3",
                     "name": "Analytics: Unsupervised Learning",
                     "submodules": ["using an api", "databases", "datacleaning"],
                     "exercises": ["module 1 - assignment.html"],
                     "hascomments": "true",
                     "comments": ["great job", "keep up the good work"]},

         {"completed": "true",
                     "locked": "false",
                     "number": "4",
                     "name": "End Products",
                     "submodules": ["using an api", "databases", "datacleaning"],
                     "exercises": ["module 1 - assignment.html"],
                     "hascomments": "true",
                     "comments": ["great job", "keep up the good work"]},

        {"completed": "true",
         "locked": "false",
         "number": "5",
         "name": "Project Management",
         "submodules": ["using an api", "databases", "datacleaning"],
         "exercises": ["module 1 - assignment.html"],
         "hascomments": "true",
         "comments": ["great job", "keep up the good work"]}
    ]
    return render_template('modules.jinja2', all_modules=all_modules)


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
    key = request.form.get("username") + "_" + request.form.get("module") + "_" + request.form.get("submodule") + "." + filename.rsplit('.', 1)[1].lower()
    client.upload_file(os.path.join(uploads_dir, filename), 'online-portal', key)
    return jsonify({})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('page-not-found.jinja2')
    
if __name__ == "__main__":
   app.run(debug = True)
