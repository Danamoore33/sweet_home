from faker import Faker
from .models import User,Post,Sex
from random import choice,randint
from app import db
from sqlalchemy.exc import IntegrityError
from flask import current_app

def users(count=100):
    fake = Faker(locale="zh_CN")
    for i in range(count):
        u = User(user=fake.name(),username=fake.user_name(),email=fake.email(),
                 confirmed=True,password='fake',about_me=fake.text(),location=fake.city(),
                 sex=choice([Sex.query.filter_by(name='男').first(),Sex.query.filter_by(name='女').first()]),
                 register_time=fake.past_date(),avatar_hash=current_app.config['BASE_PHOTO_PATH'])
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

def posts(count=100):
    fake = Faker(locale='zh_CN')
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0,user_count-1)).first()
        p = Post(body=fake.text(),timestamp=fake.past_date(),author=u)
        db.session.add(p)
    db.session.commit()

