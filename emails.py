from threading import Thread
from app import app
from flask_mail import Message
from app import mail
import os


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_mail(subject, recipient, html_body):
    msg = Message(subject, sender=os.environ['MAIL_ACCOUNT'], recipients=[recipient])
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()
