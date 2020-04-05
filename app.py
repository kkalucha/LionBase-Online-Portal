from flask import render_template, flash, redirect, url_for, request, Flask, jsonify, abort, session, send_file
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

ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'png', 'txt', 'py', 'ipynb', 'html']
STUDENT_EMAILS = ['wr2314@columbia.edu',\
'ic2502@columbia.edu',\
'ws2578@columbia.edu',\
'g.su@columbia.edu',\
'atg2152@barnard.edu',\
'tc2963@columbia.edu',\
'edl2123@columbia.edu',\
'yk2822@columbia.edu',\
'xw2600@columbia.edu',\
'kaw2216@columbia.edu',\
'gn2271@barnard.edu',\
'zim2103@columbia.edu',\
'jap2293@columbia.edu',\
'vc2534@columbia.edu',\
'gd2528@columbia.edu',\
'sg3789@columbia.edu',\
'alt2177@columbia.edu',\
'yl4095@columbia.edu',\
'at3456@columbia.edu',\
'kaan.avci@columbia.edu',\
'yw3473@columbia.edu',\
'mac2492@columbia.edu',\
'cbo2108@columbia.edu',\
'jordan.phillips@columbia.edu',\
'kak2240@columbia.edu',\
'fbb2117@columbia.edu']
TA_EMAILS = ['logan.troy@columbia.edu',\
'ketan.jog@lionbase.nyc',\
'kevin.le@lionbase.nyc',\
'kevin.chen@lionbase.nyc',\
'certificate@lionbase.nyc']

client = boto3.client('s3')
uploads_dir = 'uploads'
MAX_MODULES = 50
NUM_MODULES = 2
MAX_SUBMODULES = 20
NUM_SUBMODULES = [3, 5]
sender_address = os.environ.get('SENDER_ADDRESS')
sender_password = os.environ.get('SENDER_PASSWORD')
receiver_address = os.environ.get('RECEIVER_ADDRESS')
mail_port = 465

modules = [{"name" : "Capture, Maintain, Process", "number" : "1", "description" : "Welcome! Module 1 dives into the foundations of the data science life cycle. As you progress, you’ll increase your flexibility and understanding to maximize returns at each phase of the process. Let’s get started!",
            "exercise": "https://mybinder.org/v2/gh/LionBaseNYC/portal-exercise-01/master",
            "submodules": [{"name" : "Using an API", "number" : "1", "description" : "Explore the world of Application Programming Interfaces— an interface that allows your application to interact with external services using simple commands. Harness their power to save time and efficiency.", "maxelements":"2"},
                           {"name" : "Databases", "number" : "2", "description" : "Databases are organized collections of structured information. Here, you’ll learn how databases can help you access, manage, and update information.", "maxelements":"2"},
                           {"name" : "Data Quality", "number" : "3", "description" : "Data quality may very well be the single most important component of a data pipeline; without a level of confidence and reliability in your data, analysis generated from the data is near useless.","maxelements":"2"}]},
            {"name" : "Analytics - Supervised", "number" : "2", "description" : "Welcome to the second module! Dive into supervised analytics, where both input and preferred output are part of the training data. Learn how previously known classifications can be used to train models to correctly label unknown data points.",
            "exercise": "https://mybinder.org/v2/gh/LionBaseNYC/portal-exercise-02/master",
            "submodules": [{"name" : "Linear Regression", "number" : "1", "description" : "Linear regression is the oldest, simple and widely used supervised machine learning algorithm for predictive analysis. Discover how linear regression is used for finding linear relationships between target and one or more predictors.", "maxelements":"3"},
                           {"name" : "Model Selection and Assessment", "number" : "2", "description" : "In model selection, we estimate the performance of various competing models with the hopes of choosing the best one. Explore how this model can then be assessed by estimating the prediction error on new data.", "maxelements":"4"},
                           {"name" : "Basic Classification", "number" : "3", "description" : "Dive into classification— the process of predicting the class of given data points. You’ll be introduced to logistic regression, linear discriminant analysis, and the k-Nearest Neighbors theory.", "maxelements":"4"},
                           {"name" : "Decision Trees + Random Forest", "number" : "4", "description" : "It’s time to branch out! Learn how to build classification or regression models— in the form of a tree structure.", "maxelements":"2"},
                           {"name" : "Naive Bayes + SVMs", "number" : "5", "description" : "Explore classifiers further, and discover how Support-Vector Machine and Naive Bayes theories can be used to distinctly classify data points.", "maxelements":"3"}]},
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
        module_dict['submodules'][i]['currentelement'] = current_user.current_element[module_number][i] + 1
    return module_dict

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_module(module_number):
    return not (module_number < 0 or module_number > NUM_MODULES - 1 or current_user.locked[module_number])

def get_current_module():
    i = 0
    while not current_user.locked[i] and i < NUM_MODULES:
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
    if (not email in STUDENT_EMAILS) and (not email in TA_EMAILS):
        return jsonify({'errors':'sorry, you are not allowed to use this service'})
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
    ann = Announcement.query.all()[-1]
    current_module = get_current_module()
    module_dict = get_user_module(current_module)
    cur = 0
    for i in range(NUM_SUBMODULES[current_module]):
        if module_dict['submodules'][i]['locked'] or i == NUM_SUBMODULES[current_module] - 1:
            cur = i
            break
    progress = int(100 * (sum(NUM_SUBMODULES[0:current_module], cur)/(sum(NUM_SUBMODULES)-1)))
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
    current_user.hascomments[module_number - 1] = False
    flag_modified(current_user, 'hascomments')
    return render_template('module.jinja2', module=get_user_module(module_number - 1))

@app.route('/modules/<int:module_number>/<int:submodule_number>/<int:element>')
@login_required
def submodule(module_number, submodule_number, element):
    if not allowed_submodule(module_number - 1, submodule_number - 1) or element > int(modules[module_number - 1]['submodules'][submodule_number - 1]['maxelements']):
        abort(404)
    current_user.current_element[module_number - 1][submodule_number - 1] = element - 1
    flag_modified(current_user, 'current_element')
    db.session.commit()
    return render_template('submodule.jinja2', module_number=module_number, submodule_number=submodule_number, currentelement=int(element),\
        maxelements=int(modules[module_number - 1]['submodules'][submodule_number - 1]['maxelements']))

@app.route('/modules/<int:module_number>/<int:submodule_number>/<int:element>/notebook')
@login_required
def notebook(module_number, submodule_number, element):
    if not allowed_submodule(module_number - 1, submodule_number - 1):
        abort(404)
    name = str(module_number) + "_" + str(submodule_number) + "_" + str(element) + ".html"
    client.download_file('portal-notebooks', name, 'templates/notebooks/' + name)
    return render_template("notebooks/" + name)

@app.route('/complete/<int:module_number>/<int:submodule_number>', methods=['GET','POST'])
@login_required
def complete(module_number, submodule_number):
    if not allowed_submodule(module_number - 1, submodule_number - 1):
        abort(404)
    if request.method == 'GET':
        return render_template('survey.jinja2')
    q1 = request.form.get('q1')
    q2 = request.form.get('q2')
    q3 = request.form.get('q3')
    q4 = request.form.get('q4')
    q5 = request.form.get('q5')
    if not q1 or not q2 or not q3 or not q4 or not q5:
        return render_template('survey.jinja2', fail=True)
    survey = Survey(username=current_user.username, module=module_number - 1, submodule=submodule_number - 1,\
        responses=[q1] + [q2] + [q3] + [q4] + [q5])
    db.session.add(survey)
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
    return render_template('submitted.jinja2')

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
        return render_template('supportsubmitted.jinja2')

@app.route('/create_announcement', methods=['GET', 'POST'])
@login_required
def create_announcement():
    if current_user.email not in TA_EMAILS:
        abort(404)
    if request.method == 'GET':
        return render_template('create_announcement.jinja2')
    if request.method == 'POST':
        date = request.form.get('date')
        title = request.form.get('title')
        description = request.form.get('description')
        announcement = Annoncement(date=date, title=title, description = description)
        db.session.add(announcement)
        db.session.commit()
        return render_template('announcementsubmitted.jinja2')

@app.route('/announcements')
@login_required
def announcements():
    ann = Announcement.query.all()[::-1]
    return render_template('announcements.jinja2', ann=ann)

@app.route('/submissions')
@login_required
def submissions():
    if current_user.email not in TA_EMAILS:
        abort(404)
    surveys = Survey.query.all()[::-1]
    return render_template('responses.jinja2', surveys = surveys)

#ok so this is kinda confusin but /submissions renders responses.jinja2
#and /responses renders submissions.jinja 2. aren't we quirky aha ha

@app.route('/responses')
@login_required
def responses():
    if current_user.email not in TA_EMAILS:
        abort(404)
    return render_template('submissions.jinja2', all_submissions=Submission.query.all())

@app.route('/download/<filename>')
@login_required
def download(filename):
    if current_user.email not in TA_EMAILS:
        abort(404)
    output = 'downloads/' + filename
    client.download_file('online-portal', filename, output)
    return send_file(output, as_attachment=True)

@app.route('/complete', methods=['GET', 'POST'])
@login_required
def grading():
    if current_user.email not in TA_EMAILS:
        abort(404)
    if request.method == 'GET':
        return render_template('commentme.jinja2')
    username = request.form.get('username')
    grader = request.form.get('TA')
    module = int(request.form.get('module'))
    comment = request.form.get('comments')
    verdict = request.form.get('verdict')
    submission = Submission.query.filter_by(username=username).filter_by(module=module-1).first()
    if submission is None:
        return render_template('commentme.jinja2')
    submission.graded = True
    comment = Comment(username=username, comment=comment, module=(module-1))
    db.session.add(comment)
    student = User.query.filter_by(username=username).first()
    student.hascomments[module - 1] = True
    if verdict == 'yes':
        student.locked[module] = False
        student.locked_sub[module][0] = False
        flag_modified(student, 'locked')
        flag_modified(student, 'locked_sub')
    flag_modified(student, 'hascomments')
    db.session.commit()
    return render_template('commentme.jinja2')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('page-not-found.jinja2')

if __name__ == "__main__":
   app.run(debug = True)
