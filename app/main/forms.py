from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField,SelectField,DateField,RadioField,DateTimeField
from wtforms.validators import DataRequired,Length
from flask_pagedown.fields import PageDownField
from app.models import Sex

class PostForm(FlaskForm):
    body = PageDownField('开始我传奇的一生',validators=[DataRequired()])
    submit = SubmitField('发布')

class EditProfileForm(FlaskForm):
    name = StringField('真实姓名',validators=[Length(0,64)])
    sex = SelectField('性别',coerce=int)
    location = StringField('地区',validators=[Length(0,64)])
    about_me = TextAreaField('个性签名')
    submit = SubmitField('提交')

    def __init__(self,*args,**kwargs):
        super(EditProfileForm,self).__init__(*args,**kwargs)
        self.sex.choices = [(s.id,s.name) for s in Sex.query.all()]

class CommentForm(FlaskForm):
    body = TextAreaField('抢沙发',validators=[DataRequired()])
    submit = SubmitField('发表')

