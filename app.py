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
app.permanent_session_lifetime = datetime.timedelta(minutes=120)
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
'fbb2117@columbia.edu',\
'jam2454@columbia.edu',\
'kchhsieh@ucdavis.edu',\
'anyas@princeton.edu',\
'hc20@princeton.edu',\
'zeba.huque@yahoo.com',\
'yh3137@columbia.edu',\
'lin.jiang@columbia.edu',\
'esu@berkeley.edu',\
'led84@cornell.edu',\
'ncd2123@columbia.edu',\
'mdl2175@columbia.edu']
TA_EMAILS = ['logan.troy@columbia.edu',\
'ketan.jog@lionbase.nyc',\
'kevin.le@lionbase.nyc',\
'kevin.chen@lionbase.nyc',\
'certificate@lionbase.nyc']

client = boto3.client('s3')
uploads_dir = 'uploads'
MAX_MODULES = 50
#NUM_MODULES = 3
MAX_SUBMODULES = 20
sender_address = os.environ.get('SENDER_ADDRESS')
sender_password = os.environ.get('SENDER_PASSWORD')
receiver_address = os.environ.get('RECEIVER_ADDRESS')
mail_port = 465

from models import User, Comment, Submission, Survey, Announcement, Module, Submodule

def get_all_modules():
    modules = []
    modules_from_database = list(map(lambda x: x.serialize(), Module.query.all()))

    #go through each module dictionary, add the list of all submodule dictionaries
    #then, append that freshly cooked up module dict to the list of hardcoded modules.
    #when the hardcoded modules are eventually purged, replace them with an empty list
    for mods in modules_from_database:
        mods['submodules'] = list(map(lambda x: x.serialize(), Submodule.query.filter_by(belongs_to=mods['number'])))
        modules.append(mods)
    return modules


def num_modules():
    return len(get_all_modules())

def num_submodules():
    NUM_SUBMODULES = []
    for mods in get_all_modules():
        num_submods = len(mods['submodules'])
        NUM_SUBMODULES.append(num_submods)
    return NUM_SUBMODULES

def get_user_module(module_number):
    module_dict = copy.deepcopy(get_all_modules()[module_number])
    module_dict['locked'] = current_user.locked[module_number]
    module_dict['hascomments'] = current_user.hascomments[module_number]
    module_dict['comments'] = Comment.query.filter_by(username=current_user.username, module=module_number).all()
    if module_dict['comments'] is not None:
        module_dict['comments'] = ' '.join(map(str, module_dict['comments']))
    for i in range(num_submodules()[module_number]):
        module_dict['submodules'][i]['locked'] = current_user.locked_sub[module_number][i]
        module_dict['submodules'][i]['currentelement'] = current_user.current_element[module_number][i] + 1
    return module_dict

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_module(module_number):
    return not (module_number < 0 or module_number > num_modules() - 1 or current_user.locked[module_number])

def get_current_module():
    i = 0
    while not current_user.locked[i] and i < num_modules():
        i += 1
    return i - 1

def allowed_submodule(module_number, submodule_number):
    return not (module_number < 0 or module_number > num_modules() - 1 or submodule_number < 0 or submodule_number > num_submodules()[module_number] - 1\
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
    for i in range(num_submodules()[current_module] + 1):
        if i == num_submodules()[current_module] or module_dict['submodules'][i]['locked']:
            cur = i
            break
    progress = int(100 * (sum(num_submodules()[0:current_module], cur)/(sum(num_submodules()))))
    prev = None
    if current_module > 0:
        prev = get_user_module(current_module - 1)
    nex = None
    if current_module < num_modules() - 1:
        nex = get_user_module(current_module + 1)
    days_left=get_days_left()
    return render_template('homepage.jinja2', ann=ann, progress=progress, prev=prev, curr=module_dict, next=nex, name=current_user.firstname, days_left=days_left)

@app.route('/modules')
@login_required
def modules_route():
    return render_template('modules.jinja2', all_modules=[get_user_module(i) for i in range(num_modules())])

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
    if not allowed_submodule(module_number - 1, submodule_number - 1) or element > int(get_all_modules()[module_number - 1]['submodules'][submodule_number - 1]['maxelements']):
        abort(404)
    current_user.current_element[module_number - 1][submodule_number - 1] = element - 1
    flag_modified(current_user, 'current_element')
    db.session.commit()
    return render_template('submodule.jinja2', module_number=module_number, submodule_number=submodule_number, currentelement=int(element),\
        maxelements=int(get_all_modules()[module_number - 1]['submodules'][submodule_number - 1]['maxelements']))

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
    if submodule_number < num_submodules()[module_number - 1]:
        current_user.locked_sub[module_number - 1][submodule_number] = False
        flag_modified(current_user, 'locked_sub')
    db.session.commit()
    return redirect('/modules/' + str(module_number))

@app.route('/newmodule', methods=['GET', 'POST'])
@login_required
def newmodule():
    if current_user.email not in TA_EMAILS:
        abort(404)
    if request.method == 'GET':
        return render_template('newmodule.jinja2')
    if request.method == 'POST':
        name = request.form.get('name')
        number = request.form.get('number')
        description = request.form.get('description')
        exercise = request.form.get('exercise')
        module = Module(name = name, number = number, description = description, exercise = exercise)
        db.session.add(module)
        db.session.commit()
        return render_template('newmodulesubmitted.jinja2')

@app.route('/newsubmodule', methods=['GET', 'POST'])
@login_required
def newsubmodule():
    if current_user.email not in TA_EMAILS:
        abort(404)
    if request.method == 'GET':
        return render_template('newsubmodule.jinja2')
    if request.method == 'POST':
        name = request.form.get('name')
        number = request.form.get('number')
        description = request.form.get('description')
        belongs_to = request.form.get('belongs_to')
        maxelements = request.form.get('maxelements')
        submodule = Submodule(name = name, number = number, description = description, belongs_to = belongs_to, maxelements = maxelements)
        db.session.add(submodule)
        db.session.commit()
        return render_template('newmodulesubmitted.jinja2')

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
        announcement = Announcement(date=date, title=title, description = description)
        db.session.add(announcement)
        db.session.commit()
        return render_template('announcementsubmitted.jinja2')

@app.route('/announcements')
@login_required
def announcements():
    ann = Announcement.query.all()[::-1]
    return render_template('announcements.jinja2', ann=ann)

@app.route('/surveyresponses')
@login_required
def surveyresponses():
    if current_user.email not in TA_EMAILS:
        abort(404)
    surveys = Survey.query.all()[::-1]
    return render_template('responses.jinja2', surveys = surveys)

@app.route('/submissions')
@login_required
def submission():
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

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.email not in TA_EMAILS:
        abort(404)
    return render_template('dashboard.jinja2')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('page-not-found.jinja2')

if __name__ == "__main__":
   app.run(debug = True)
