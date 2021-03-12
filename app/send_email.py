from threading import Thread
from flask_mail import Message
from app import mail
from flask import current_app,render_template

def mail_async(app,msg):
    with app.app_context():
        mail.send(msg)

def send_email(to,subject,template,**kwargs):
    msg = Message(current_app.config['MAIL_SUBJECT_PREFIX']+subject,
                  sender=current_app.config['MAIL_SENDER'],recipients=[to])
    msg.body = render_template('auth/mail/'+template+'.txt',**kwargs)
    msg.html= render_template('auth/mail/' + template + '.html', **kwargs)
    thr = Thread(target=mail_async,args=(current_app._get_current_object(),msg))
    thr.start()
    return thr

