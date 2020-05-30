import json
from datetime import datetime as dt, timedelta
from hashlib import md5
from time import time

import jwt
from flask import current_app
from flask_login import UserMixin, current_user
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash

from travelblog import db, login, admin


country_visitor_relation = db.Table(
    'country_visitor',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True),
    db.Column('country_id', db.Integer, db.ForeignKey('country.id'),
              primary_key=True))


country_follower_relation = db.Table(
    'country_follower',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True),
    db.Column('country_id', db.Integer, db.ForeignKey('country.id'),
              primary_key=True))


country_articletags_relation = db.Table(
    'country_tag',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'),
              primary_key=True),
    db.Column('country_id', db.Integer, db.ForeignKey('country.id'),
              primary_key=True))


user_article_like_relation = db.Table(
    'article_likes',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'),
              primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True))


user_follower_followed_relation = db.Table(
    'user_followers',
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True),
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True))


user_article_dislike_relation = db.Table(
    'article_dislikes',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'),
              primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    active = db.Column(db.Boolean())

    info = db.relationship('UserInfo', backref='user', uselist=False,
                           cascade='all')
    comments = db.relationship('Comment', backref='comment_author')
    articles = db.relationship('Article', backref='article_author')

    followers = db.relationship(
        'User', secondary=user_follower_followed_relation,
        primaryjoin=id==user_follower_followed_relation.c.followed_id,
        secondaryjoin=id==user_follower_followed_relation.c.follower_id,
        backref='follows')

    sent_messages = db.relationship(
        'Message', foreign_keys='Message.sender_id', lazy='dynamic', 
        backref=db.backref('sender', lazy=True))

    received_messages = db.relationship(
        'Message', foreign_keys='Message.recipient_id', lazy='dynamic', 
        backref=db.backref('recipient', lazy=True))

    followed_countries = db.relationship(
        'Country', secondary=country_follower_relation, lazy=True,
        backref='followers')

    visited_countries = db.relationship(
        'Country', secondary=country_visitor_relation, lazy=True,
        backref='visitors')

    liked_articles = db.relationship(
        'Article', secondary=user_article_like_relation, lazy=True,
        backref='likes')

    disliked_articles = db.relationship(
        'Article', secondary=user_article_dislike_relation, lazy=True,
        backref='dislikes')

    role = db.relationship('Role', backref='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def make_token(self):
        payload = {'exp': dt.utcnow()+timedelta(hours=1), 'iat': dt.utcnow(),
                   'id': self.id}
        return jwt.encode(
            payload, current_app.config['SECRET_KEY'], 'HS256').decode('utf-8')

    @staticmethod
    def process_token(token):
        try:
            id = jwt.decode(
                token, current_app.config['SECRET_KEY'], 'HS256')['id']
        except:
            return None
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(id)


class UserInfo(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        primary_key=True)
    birthdate = db.Column(db.Date())
    avatar = db.Column(db.String(120), default='default.png')
    gender = db.Column(db.String(1))
    job = db.Column(db.String(60))
    origin_country = db.Column(db.String(60))
    about = db.Column(db.Text(600))
    registration_date = db.Column(db.Date(), default=dt.utcnow)
    last_seen = db.Column(db.DateTime(), default=dt.utcnow)

    def __repr__(self):
        return f'<Info about {self.user.username}>'


class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True)
    code = db.Column(db.String(2), index=True, unique=True)

    info = db.relationship('CountryInfo', backref='country', uselist=False,
                           cascade='all')

    articles = db.relationship(
        'Article', secondary=country_articletags_relation, lazy='dynamic',
        backref='country_tags', cascade='all')

    def __repr__(self):
        return f'<Country {self.name}>'

    @staticmethod
    def get_country_list():
        with current_app.app_context():
            return Country.query.all()


class CountryInfo(db.Model):
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'),
                           primary_key=True)
    capital = db.Column(db.String(20))
    population = db.Column(db.Integer)
    land_area = db.Column(db.Integer)
    currency = db.Column(db.String(40))
    currency_code = db.Column(db.String(3))
    language = db.Column(db.String(30))
    time_zone = db.Column(db.String(50))
    time_offset = db.Column(db.String(10))
    weather = db.Column(db.Text(600))
    description = db.Column(db.Text(2000))
    region = db.Column(db.String(20))
    subregion = db.Column(db.String(40))
    last_updated = db.Column(db.DateTime(), default=dt.utcnow)

    def __repr__(self):
        return f'<Info about {self.country.name}>'


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.Text(100000), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    article_type = db.Column(db.String(10))
    date_posted = db.Column(db.DateTime(), default=dt.utcnow)
    last_updated = db.Column(db.DateTime())

    comments = db.relationship(
        'Comment', backref='article', cascade='all', lazy='dynamic')

    def __repr__(self):
        return (f'<Article {self.id} title {self.title} '
                f'by user {self.article_author.username}')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.Text(2000), nullable=False)

    date_posted = db.Column(db.DateTime(), default=dt.utcnow)
    last_updated = db.Column(db.DateTime())

    def __repr__(self):
        return f'<Comment №{self.id} on post {self.article.title}>'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text(2000), nullable=False)

    date_send = db.Column(db.DateTime(), default=dt.utcnow)
    seen = db.Column(db.Boolean(), default=False)
    deleted = db.Column(db.Boolean())

    def __repr__(self):
        return f'<Message №{self.id} from {self.sender} to {self.recipient}>'


class Role(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    role_name = db.Column(db.String(30))
    date_granted = db.Column(db.DateTime(), default=dt.utcnow)

    def __repr__(self):
        return f'<User {self.user_id} is {self.role_name}>'