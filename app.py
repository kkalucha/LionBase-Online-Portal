from flask import render_template, flash, redirect, url_for, request, Flask, jsonify, abort, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from werkzeug.exceptions import BadRequest
from config import Config
import boto3, os, copy, datetime, smtplib, ssl

app = Flask(__name__)

app.config.from_object(Config)
app.permanent_session_lifetime = datetime.timedelta(minutes=30)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'png', 'txt', 'py', 'ipynb']
client = boto3.client('s3')
uploads_dir = 'uploads'
MAX_MODULES = 50
NUM_MODULES = 2
MAX_SUBMODULES = 20
NUM_SUBMODULES = [3, 3, 5, 2, 1]
sender_address = os.environ.get('SENDER_ADDRESS')
sender_password = os.environ.get('SENDER_PASSWORD')
receiver_address = os.environ.get('RECEIVER_ADDRESS')
mail_port = 465

modules = [{"name" : "Analytics", "number" : "1", "description" : "this is the description",
            "exercise": "https://mybinder.org/v2/gist/kkalucha/f9cf740f5371c15163c2229c701891ce/master",
            "submodules": [{"name" : "Supervised Machine Learning", "number" : "1", "description" : "this is ML but supervised", "maxelements":"2"},
                           {"name" : "Supervised Machine Learning", "number" : "2", "description" : "this is the second ML", "maxelements":"2"},
                           {"name" : "supervised machine learning", "number" : "3", "description" : "this is third one","maxelements":"2"}]},
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

from models import User, Comment, Submission, Survey, Announcement

def get_user_module(module_number):
    module_dict = copy.deepcopy(modules[module_number])
    module_dict['locked'] = current_user.locked[module_number]
    module_dict['hascomments'] = current_user.hascomments[module_number]
    if module_dict['hascomments']:
        module_dict['comments'] = Comment.query.filter_by(username=current_user.username, module=module_number).all()
    for i in range(NUM_SUBMODULES[module_number]):
        module_dict['submodules'][i]['locked'] = current_user.locked_sub[module_number][i]
        print(current_user.current_element[2][1])
        module_dict['submodules'][i]['currentelement'] = current_user.current_element[module_number][i]
    return module_dict

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_module(module_number):
    return not (module_number < 0 or module_number > NUM_MODULES - 1 or current_user.locked[module_number])

def get_current_module():
    i = 0
    while not current_user.locked[i]:
        i += 1
    return i - 1

def allowed_submodule(module_number, submodule_number):
    return not (module_number < 0 or module_number > NUM_MODULES - 1 or submodule_number < 0 or submodule_number > NUM_SUBMODULES[module_number] - 1\
    or current_user.locked_sub[module_number][submodule_number])

def get_days_left():
    return (datetime.date(2020,5,2) - datetime.date.today()).days

@app.before_request
def before_request():
    session.modified = True

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
    session.permanent = True
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
    user = User(username=username, email=email, firstname=firstname, lastname=lastname, university=university,\
                dob=dob, major=major, program=program)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({})

@app.route('/homepage', methods=['GET', 'POST'])
@login_required
def homepage():
    ann = {"title": "Program Kickoff", "description": "Join us on Zoom for our first bonding event! Meet other students in the program."}
    current_module = get_current_module()
    module_dict = get_user_module(current_module)
    cur = 0
    for i in range(NUM_SUBMODULES[current_module]):
        if module_dict['submodules'][i]['locked']:
            cur = i
            break
    progress = int(100 * (sum(NUM_SUBMODULES[0:current_module], cur)/sum(NUM_SUBMODULES)))
    prev = None
    if current_module > 0:
        prev = get_user_module(current_module - 1)
    nex = None
    if current_module < NUM_MODULES - 1:
        nex = get_user_module(current_module + 1)
    days_left=get_days_left()
    return render_template('homepage.jinja2', ann=ann, progress=progress, prev=prev, curr=module_dict, next=nex, name=current_user.firstname, days_left=days_left)

@app.route('/modules')
@login_required
def modules_route():
    return render_template('modules.jinja2', all_modules=[get_user_module(i) for i in range(NUM_MODULES)])

@app.route('/modules/<int:module_number>')
@login_required
def module(module_number):
    if not allowed_module(module_number - 1):
        abort(404)
    return render_template('module.jinja2', module=get_user_module(module_number - 1))

@app.route('/modules/<int:module_number>/<int:submodule_number>/<int:element>')
@login_required
def submodule(module_number, submodule_number, element):
    if not allowed_submodule(module_number - 1, submodule_number - 1):
        abort(404)
    current_user.current_element[module_number - 1][submodule - 1] = element - 1
    return render_template('submodule.jinja2', module_number=module_number, submodule_number=submodule_number, element=element,\
        maxelements=modules[module_number - 1]['submodules'][submodule_number - 1]['maxelements'])

@app.route('/modules/<int:module_number>/<int:submodule_number>/<int:element>/notebook')
@login_required
def notebook(module_number, submodule_number, element):
    if not allowed_submodule(module_number - 1, submodule_number - 1):
        abort(404)
    return render_template("notebooks/" + module_number + "_" + submodule_number + "_" + element + ".html")

@app.route('/complete/<int:module_number>/<int:submodule_number>')
@login_required
def complete(module_number, submodule_number):
    if not allowed_submodule(module_number - 1, submodule_number - 1):
        abort(404)
    if submodule_number < NUM_SUBMODULES[module_number - 1]:
        current_user.locked_sub[module_number - 1][submodule_number] = False
        flag_modified(current_user, 'locked_sub')
        db.session.commit()
    return redirect('/modules/' + str(module_number))

@app.route('/submit/<int:module_number>', methods=['POST'])
@login_required
def submit_file(module_number):
    if not allowed_module(module_number - 1):
        abort(404)
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"errors":"no file attached"})
    if not allowed_file(file.filename):
        return jsonify({"errors":"invalid file type"})
    filename = secure_filename(file.filename)
    file.save(os.path.join(uploads_dir, filename))
    key = current_user.username + "_" + str(module_number) + "." + filename.rsplit('.', 1)[1].lower()
    client.upload_file(os.path.join(uploads_dir, filename), 'online-portal', key)
    uploaded = Submission(username=current_user.username, module=module_number-1, key=key)
    db.session.add(uploaded)
    db.session.commit()
    return jsonify({})

@app.route('/support', methods=['GET', 'POST'])
def query():
    if request.method == 'GET':
        return render_template('formpage.jinja2', success=False)
    if request.method == 'POST':
        experience = request.form.get('experience')
        name = request.form.get('name')
        email = request.form.get('email')
        comments = request.form.get('comments')
        message = "Subject: [Lionbase Portal] [" + experience + "]\n\n" + name + "<" + email + "> : " + comments
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", mail_port, context=context) as server:
            server.login(sender_address, sender_password)
            server.sendmail(sender_address, receiver_address, message)
        return render_template('formpage.jinja2', success=True)

@app.route('/announcements')
@login_required
def announcements():
    ann = Announcement.query.all()
    return render_template('announcements.jinja2', ann=ann)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('page-not-found.jinja2')

if __name__ == "__main__":
   app.run(debug = True)
