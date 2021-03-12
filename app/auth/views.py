from . import auth
from flask_login import login_user,logout_user,login_required,current_user
from .forms import LoginForm,RegisterForm,MailForm
from app.models import User,Role
from flask import request,url_for,redirect,render_template,flash,current_app
from app import db
from app.send_email import send_email

@auth.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username_or_email.data).first()
        if user is None:
            user = User.query.filter_by(email=form.username_or_email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user,form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('身份验证未通过')
    return render_template('auth/login.html',form=form)

@login_required
@auth.route('/logout')
def logout():
    logout_user()
    flash('您已成功退出')
    return redirect(url_for('main.index'))

@auth.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_auth_token(form.email.data,form.username.data)
        send_email(form.email.data,'邮箱绑定验证','confirm',token=token,user=user)
        flash('请前往邮箱进行安全验证')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html',form=form)

@auth.route('/confirm/<token>')
def verify_account(token):
    user = User.verify_auth_token(token)
    if current_user.is_authenticated and current_user.confirmed:
        return redirect(url_for('main.index'))
    if user:
        login_user(user)
        user.confirmed = True
        if user.email is not None and user.avatar_hash is None:
            user.avatar_hash = current_app.config['BASE_PHOTO_PATH']
        db.session.add(user)
        db.session.commit()
        flash('你已通过邮箱安全验证')
        return render_template('auth/verify_access.html',user=user)
    else:
        flash('验证未通过')
    return redirect(url_for('main.index'))

@auth.before_app_request
@auth.route('/unconfirm')
def before_request():
    if 'Python' in request.headers.get('User-Agent'):
        return render_template('404.html')
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.blueprint != 'auth' and request.endpoint != 'static':
            return render_template('unconfirmed.html')

@login_required
@auth.route('/send_email',methods=['GET','POST'])
def resend():
    form = MailForm()
    if form.validate_on_submit():
        token = current_user.generate_auth_token(form.email.data, current_user.username)
        send_email(form.email.data, '邮箱绑定验证', 'confirm', token=token,
                   user=current_user._get_current_object())
        flash('邮件已发送至您的邮箱')
        return redirect('main.index')
    return render_template('auth/resend.html',form=form)



