from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError
from wtforms.fields.html5 import EmailField

from travelblog.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_repeat = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password',
                                               'Your passwords do not match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter(User.username.ilike(username.data)).first()
        if user is not None:
            raise ValidationError('Please choose another username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please choose another email.')


class RequestPasswordResetForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no user with this email.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password_repeat = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password',
                                               'Your passwords do not match')])
    submit = SubmitField('Reset password')