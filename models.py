from datetime import datetime
from app import db, login, MAX_MODULES, MAX_SUBMODULES
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    university = db.Column(db.String(100))
    dob = db.Column(db.Date)
    major = db.Column(db.String(100))
    program = db.Column(db.String(50))
    completed = db.Column(db.ARRAY(db.Boolean(), dimensions=1))
    locked = db.Column(db.ARRAY(db.Boolean(), dimensions=1))
    locked_sub = db.Column(db.ARRAY(db.Boolean(), dimensions=2))
    hascomments = db.Column(db.ARRAY(db.Boolean(), dimensions=1))
    current_element = db.Column(db.ARRAY(db.Integer, dimensions=2))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.completed = [False] * MAX_MODULES
        self.locked = [False] * MAX_MODULES
        self.locked_sub = [ ([False] + [True] * (MAX_SUBMODULES - 1)) ] * MAX_MODULES
        self.hascomments = [False] * MAX_MODULES
        self.current_element = [[0] * MAX_SUBMODULES] * MAX_MODULES

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    comment = db.Column(db.String())
    module = db.Column(db.Integer)

    def __repr__(self):
        return self.comment

class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    number = db.Column(db.String())
    description = db.Column(db.String())
    exercise = db.Column(db.String())

    def serialize(self):
        return {'name':self.name, 'number':self.number, 'description':self.description, 'exercise':self.exercise}

class Submodule(db.Model):
    __tablename__ = 'submodules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    number = db.Column(db.String())
    description = db.Column(db.String())
    belongs_to = db.Column(db.String())
    maxelements = db.Column(db.String())

    def serialize(self):
        return {'name':self.name, 'number':self.number, 'description':self.description, 'maxelements':self.maxelements}


class Survey(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    module = db.Column(db.Integer)
    submodule = db.Column(db.Integer)
    responses = db.Column(db.ARRAY(db.String(), dimensions=1))

    def __repr__(self):
        return self.username + "_" + self.module + " " + self.submodule

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    module = db.Column(db.Integer)
    key = db.Column(db.String())
    graded = db.Column(db.Boolean())
    grader = db.Column(db.String())

    def __repr__(self):
        return {'username':self.username, 'modulenumber':str(self.module + 1), 'filename':self.key, 'graded':self.graded}

    def __init__(self, **kwargs):
        super(Submission, self).__init__(**kwargs)
        self.graded = False

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String())
    title = db.Column(db.String())
    description = db.Column(db.String())

    def __repr__(self):
        {'date':self.date, 'title':self.title, 'description':self.description}
