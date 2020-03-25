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

ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'png', 'txt']
client = boto3.client('s3')
uploads_dir = 'uploads'

from models import User

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
    user = User(username=username, email=email, firstname=firstname, lastname=lastname, university=university,
                dob=dob, major=major, program=program)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({})
    

@app.route('/homepage', methods=['GET', 'POST'])
@login_required
def homepage():
    return render_template('homepage.jinja2')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/exercise/<module_number>')

def exercise(module_number):
	if int(module_number) > 6:
		return jsonify({"errors" : "invalid module number"})
	#prompt = get_prompt()
	prompt = "This is placeholder text"
	return render_template('exercise.jinja2', module_number=module_number, prompt=prompt)


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
    
