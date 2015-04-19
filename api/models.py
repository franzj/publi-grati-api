from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/db_publicidad'
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)


class User(db.Model):
    """ Tabla User """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    fullname = db.Column(db.String(25))
    nickname = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(120))

    publicity = db.relationship('Publicity', backref='user',
                                lazy='dynamic')

    def __init__(self, name, fullname, nickname, email, password):
        self.name = name
        self.fullname = fullname
        self.nickname = nickname
        self.hash_password(password)
        self.email = email

    def __repr__(self):
        return '<User({0})>'.format(self.nickname)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


class Publicity(db.Model):
    """ Tabla Publicity """

    id = db.Column(db.Integer, primary_key=True)
    publication = db.Column(db.String(140))
    company_name = db.Column(db.String(45))
    contact = db.Column(db.String(45))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, user, publication, company_name, contact):
        self.user = user
        self.publication = publication
        self.company_name = company_name
        self.contact = contact

    def __repr__(self):
        return '<Publicidad({0})>'.format(self.publication)
