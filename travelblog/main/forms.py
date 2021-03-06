from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields.html5 import DateField
from wtforms.fields import (StringField, SubmitField, TextAreaField,
                            SelectMultipleField, SelectField, FileField,
                            HiddenField)
from wtforms.ext.sqlalchemy.fields import (QuerySelectMultipleField,
                                           QuerySelectField)
from wtforms.validators import DataRequired, ValidationError, Length

from travelblog.models import User, Country


class EditProfileForm(FlaskForm):
    avatar = FileField(
        'Choose avatar', validators=[FileAllowed(['jpg', 'jpeg', 'png'],
                                                 'Only images are allowed!')])
    birthdate = DateField('Birthdate')
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female')])
    job = StringField('Your job')
    origin_country = QuerySelectField(
        label='Origin Country', get_label='name', query_factory=lambda: Country.query)
    about = TextAreaField('About You')
    submit = SubmitField('Submit')


class ArticleForm(FlaskForm):
    article_type = SelectField('Type', choices=[(
        'Guide', 'Guide'), ('Blog', 'Blog'), ('News', 'News')])
    title = StringField(
        'Title', validators=[DataRequired('Article must have a title!')])
    # country_tag = SelectMultipleField(
    #     'Country tags', choices=[(country.name, country.name)
    #                              for country in Country.get_country_list()])
    country_tag = QuerySelectMultipleField(
        label='Country tags', get_label='name',
        query_factory=lambda: Country.query)
    # body = TextAreaField(
    #     'Post body', validators=[DataRequired('Article must have some text!')])
    hidden_body = HiddenField()
    submit = SubmitField()


class CommentForm(FlaskForm):
    id = HiddenField()
    # comment = TextAreaField('Your comment')
    hidden_body = HiddenField()
    submit = SubmitField('Comment')


class MessageForm(FlaskForm):
    title = StringField(
        'Title', validators=[DataRequired('Message must have a title')])
    body = TextAreaField(
        'Message', validators=[DataRequired('Write something to message')])
    submit = SubmitField('Send')
