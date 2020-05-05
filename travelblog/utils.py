from urllib.parse import urlparse, urljoin
from threading import Thread
from flask import render_template, current_app
from flask_mail import Message
from travelblog import mail

def is_safe_url(request, target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def send_mail(user, message_type, content):
    message = Message(recipients=[user.email])
    if message_type == 'email':
        message.subject = 'Email verification'
        message.html = render_template(
            'auth/_email_confirmation_mail.html', user=user, link=content)
    elif message_type == 'pass':
        message.subject = 'Password reset'
        message.html = render_template(
            'auth/_password_reset_mail.html', user=user, link=content)
    else:
        message.subject = 'News feed'

    Thread(target=async_mail, args=(current_app._get_current_object(), message)).start()

def async_mail(app, message):
    with app.app_context():
        mail.send(message)