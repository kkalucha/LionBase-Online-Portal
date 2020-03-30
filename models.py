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
    dob = db.Column(db.Integer)
    major = db.Column(db.String(100))
    program = db.Column(db.String(50))
    completed = db.Column(db.ARRAY(db.Boolean(), dimensions=1))
    locked = db.Column(db.ARRAY(db.Boolean(), dimensions=1))
    locked_sub = db.Column(db.ARRAY(db.Boolean(), dimensions=2))
    hascomments = db.Column(db.ARRAY(db.Boolean(), dimensions=1))
    current_module = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.completed = [False] * MAX_MODULES
        self.locked = [False] + [True] * (MAX_MODULES - 1)
        self.locked_sub = [ ([False] + [True] * (MAX_SUBMODULES - 1)) ] + [ ([True] * MAX_SUBMODULES) for i in range(MAX_MODULES - 1) ]
        self.hascomments = [False] * MAX_MODULES
        self.current_module = 0

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

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    module = db.Column(db.Integer)
    key = db.Column(db.String())
    graded = db.Column(db.Boolean())

    def __repr__(self):
        return self.key

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.graded = False