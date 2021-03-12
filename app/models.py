from . import db,login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from flask import current_app,request
from flask_login import UserMixin,AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
import bleach
from markdown import markdown
import hashlib
import os

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    followed_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    timestamp = db.Column(db.DateTime(),default=datetime.utcnow)

class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True)
    user = db.Column(db.String(64))
    location = db.Column(db.String(64))
    username = db.Column(db.String(64),unique=True,index=True)
    email = db.Column(db.String(64),unique=True,index=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime(),default=datetime.now)
    about_me = db.Column(db.Text())
    register_time = db.Column(db.DateTime(),default=datetime.now)
    confirmed = db.Column(db.Boolean,default=False)
    role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))
    sex_id = db.Column(db.Integer,db.ForeignKey('sexs.id'))
    avatar_hash = db.Column(db.String(64))
    posts = db.relationship('Post',backref='author',lazy='dynamic')
    comments = db.relationship('Comment',backref='author',lazy='dynamic')
    #我的关注
    followers = db.relationship('Follow',foreign_keys=[Follow.followed_id],
                               backref=db.backref('followed',lazy='joined'),
                                lazy='dynamic',cascade='all,delete-orphan')
    #我的粉丝
    followed = db.relationship('Follow',foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower',lazy='joined'),
                               lazy='dynamic',cascade='all,delete-orphan')

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['MAIL_ADMIN']:
                self.role = Role.query.filter_by(name='Admin').first()
            elif self.role is None:
                self.role = Role.query.filter_by(name='User').first()
        if self.sex is None:
            self.sex = Sex.query.filter_by(name='未知').first()

    @property
    def followed_posts(self):
        return Post.query.join(Follow,Post.author_id == Follow.follower_id).filter(Follow.followed_id == self.id)

    def follow(self,user):
        if not self.is_following(user):
            f = Follow(followed=self,follower=user)
            db.session.add(f)

    def unfollow(self,user):
        f = self.followers.filter_by(follower_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self,user):
        if user.id is None:
            return False
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def is_followed_by(self,user):
        if user.id is None:
            return False
        return self.followed.filter_by(folloed_id=user.id).first() is not None

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    """
    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()


    def gravatar(self,size=80,r='g',d='identicon'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&r={r}&d={d}'.format(url=url,hash=hash,size=size,d=d,r=r)
    """

    @property
    def password(self):
        raise AttributeError('你没有这个权限')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    def generate_auth_token(self,email,username,exprie=3600):
        s = TJS(current_app.config['SECRET_KEY'],exprie)
        return s.dumps({'confirm': self.id,'email': email,'username':username}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = TJS(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.filter_by(username=data.get('username')).first()
        if user is None:
            return False
        if data.get('confirm') != user.id:
            return False
        user.email = data.get('email')
        db.session.add(user)
        return user

    def can(self,perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_admin(self):
        return self.can(Permission.ADMIN)

    def __repr__(self):
        return '<User {!r}>'.format(self.username)

class AnonymousUser(AnonymousUserMixin):
    def can(self,perm):
        return False

    def is_admin(self):
        return False

login_manager.anonymous_user = AnonymousUser

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),index=True,unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User',backref='role',lazy='dynamic')

    def __init__(self,**kwargs):
        super(Role,self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self,perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def reduce_permission(self,perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permission(self):
        self.permissions = 0

    def has_permission(self,perm):
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW,Permission.COMMENT,Permission.WRITE],
            'Moderator': [Permission.FOLLOW,Permission.COMMENT,Permission.WRITE,Permission.MODERATE],
            'Admin': [Permission.FOLLOW,Permission.COMMENT,Permission.WRITE,Permission.MODERATE,Permission.ADMIN]
        }
        defualt_role = 'User'

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permission()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == defualt_role)
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role {!r}>'.format(self.name)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text())
    body_html = db.Column(db.Text())
    timestamp = db.Column(db.DateTime(),default=datetime.utcnow)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    comments = db.relationship('Comment',backref='post',lazy='dynamic')

    @staticmethod
    def on_body_change(target,value,oldvalue,initial):
        allow_tags = ['p','h1','h2','h3','h4','em','i','abbr','strong','small','b',
                      'div','ul','li','ol','code']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value,output_format='html'),tags=allow_tags,strip=True
        ))

db.event.listen(Post.body,'set',Post.on_body_change)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text())
    body_html = db.Column(db.Text())
    timestamp = db.Column(db.DateTime(),default=datetime.utcnow)
    disabled = db.Column(db.Boolean,default=False)
    post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))

    @staticmethod
    def on_body_change(target,value,oldvalue,initial):
        allow_tags = ['p','h1','h2','h3','h4','em','i','abbr','strong','small','b',
                      'div','ul','li','ol','code']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value,output_html='html'),tags=allow_tags,strip=True
        ))

db.event.listen(Comment.body,'set',Comment.on_body_change)


class Sex(db.Model):
    __tablename__ = 'sexs'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(32))
    users = db.relationship('User',backref='sex',lazy='dynamic')

    @staticmethod
    def make_sex():
        sex_choice = ['男','女','未知']
        for s in sex_choice:
            if not Sex.query.filter_by(name=s).first():
                se = Sex(name=s)
                db.session.add(se)
                db.session.commit()

    def __repr__(self):
        return '<Sex {!r}>'.format(self.name)

class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16




