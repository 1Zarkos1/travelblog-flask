from datetime import datetime
from threading import Thread

from flask import render_template, redirect, request, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message

from travelblog import db, mail
from travelblog.auth import bp
from travelblog.models import User, UserInfo
from travelblog.auth.forms import (RegistrationForm, LoginForm,
                                   RequestPasswordResetForm, ResetPasswordForm)
from travelblog.utils import is_safe_url, send_mail


@bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        flash('You are already logged in!', category='info')
        return redirect(url_for('main.news'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        new_user_info = UserInfo(user=new_user)
        db.session.add_all([new_user, new_user_info])
        db.session.commit()
        link = request.host_url + \
            url_for('auth.confirm_email', token=new_user.make_token())
        print(link)
        send_mail(new_user, 'email', link)
        flash('Confirmation message has been sent to your email', category='info')
        return redirect(url_for('auth.login'))
    return render_template('auth/signup.html', form=form)


@bp.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in!', category='info')
        return redirect(url_for('main.news'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if user.confirmed == False:
                flash('You need to verify your email first', category='danger')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember.data)
            next = request.args.get('next')
            if is_safe_url(request, next):
                flash('You have been succesfully logged in!', category='success')
                return redirect(next or url_for('main.index'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Incorrect username or password!', category='danger')
            redirect(url_for('auth.login'))
    return render_template('auth/login.html', form=form)


@bp.route('/request_password_reset/', methods=['GET', 'POST'])
def request_password_reset():
    if current_user.is_authenticated:
        flash('You are already autentificated!', category='info')
        return redirect(url_for('main.index'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        link = request.host_url + \
            url_for('auth.reset_password', token=user.make_token())
        send_mail(user, 'pass', link)
        flash('Reset password link was sent to your email', category='info')
        return redirect(url_for('auth.login'))
    return render_template('auth/request_password_reset.html', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.process_token(token)
    if user is None:
        flash('The supplied link is incorrect or already expired. Try to '
              'request password reset again.', category='danger')
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset', category='info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@bp.route('/confirm_email/<token>')
def confirm_email(token):
    user = User.process_token(token)
    if user is None:
        flash('The supplied link is incorrect or already expired.',
              category='danger')
    else:
        user.confirmed = True
        db.session.commit()
        flash('Your email has been verified', category='success')
    return redirect(url_for('main.index'))


@bp.route('/logout/')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('You have been logged out!', category='info')
        return redirect(url_for('main.news'))


# def send_mail(message):
#     Thread(target=mail.send, args=(message,)).start()