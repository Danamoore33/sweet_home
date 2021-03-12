from app.models import User,Role,Sex
import unittest
from app import create_app,db

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_User(self):
        user = User(username='test',password='test',email='test@qq.com',confirmed=True)
        user2 = User(username='test2',password='test',email='test2@qq.com',confirmed=True)
        db.session.add_all([user,user2])
        db.session.commit()
        role = Role.query.filter_by(name='User').first()
        sex = Sex.query.filter_by(name='未知').first()
        self.assertTrue(user.password_hash != user2.password_hash)
        self.assertTrue(user.role == role)
        self.assertTrue(user.sex == sex)

