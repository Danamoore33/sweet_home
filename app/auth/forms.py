from flask_wtf import FlaskForm
from wtforms import StringField,SelectField,SubmitField,BooleanField,PasswordField
from wtforms.validators import DataRequired,Email,EqualTo,Length,Regexp
from app.exceptions import ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username_or_email = StringField('用户名',validators=[DataRequired(),Length(1,64)])
    password = PasswordField('密码',validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    username = StringField('用户名',validators=[DataRequired(),Length(1,64),Regexp(
        '[\u4e00-\u9fa5-A-Za-z_丶]+',0,'用户名只允许包含汉字,大小写英文字母和下划线')])
    email = StringField('邮箱',validators=[DataRequired(),Email(),Length(1,128)])
    password = PasswordField('密码',validators=[DataRequired(),EqualTo('password1',message="请重新确认密码"),Length(3,128)])
    password1 = PasswordField('确认密码',validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在')

    def validate_email(self,field):
        user = User.query.filter_by(email=field.data).first()
        if user and user.confirmed:
            raise ValidationError('此邮箱已注册')

class MailForm(FlaskForm):
    email = StringField('邮箱地址',validators=[DataRequired(),Email(),Length(1,64)])
    submit = SubmitField('发送邮件')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('此邮箱已注册')

