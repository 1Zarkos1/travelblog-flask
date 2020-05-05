import os
from datetime import datetime

from flask import render_template, redirect, request, url_for, flash, abort
from flask_login import current_user, login_required

from travelblog.main import bp
from travelblog import db
from travelblog.models import User, Country, Article, Comment
from travelblog.main.forms import EditProfileForm, ArticleForm, CommentForm


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.info.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index/')
def index():
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template('index.html', articles=articles)


@bp.route('/create_article/', methods=['GET', 'POST'])
@login_required
def create_article():
    form = ArticleForm()
    if form.validate_on_submit():
        country = Country.query.filter(
            Country.name.in_(form.country_tag.data)).all()
        article = Article(article_author=current_user,
                          country_tags=country, title=form.title.data,
                          article_type=form.article_type.data,
                          body=form.body.data)
        db.session.add(article)
        db.session.commit()
        flash('Your article was added successfully!', category='info')
        return redirect(url_for('main.index'))
    return render_template('create_article.html', form=form)


@bp.route('/article/<int:id>/', methods=['GET', 'POST'])
def article_view(id):
    article = Article.query.filter_by(id=id).first_or_404()
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(article=article, comment_author=current_user,
                          body=form.comment.data)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('main.article_view', id=id))
    return render_template('article.html', form=form, article=article)


@bp.route('/news/')
def news():
    return render_template('base.html')


@bp.route('/guides/')
def guides():
    return render_template('base.html')


@bp.route('/galleries/')
def galleries():
    refs = []
    for imgref in os.listdir('travelblog/static/img'):
        if imgref.endswith('.jpeg'):
            print(imgref)
            refs.append(imgref)
    return render_template('gallerie.html', refs=refs)


@bp.route('/galleries/<ref>/')
def image(ref):
    return render_template('gallerie.html', refs=[f'{ref}'])


@bp.route('/countries/')
def countries():
    country_list = Country.query.all()
    return render_template('country_list.html', countries=country_list)


@bp.route('/country/<country_id>')
def country_view(country_id):
    country = Country.query.get(country_id)
    return render_template('country.html', country=country)


@bp.route('/gear/')
def gear():
    return render_template('base.html')


@bp.route('/about_me/')
@login_required
def about_me():
    return render_template('base.html')


@bp.route('/user/<username>/')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)


@bp.route('/edit_profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_info = current_user.info
    form = EditProfileForm(
        birthdate=user_info.birthdate, gender=user_info.gender,
        job=user_info.job, origin_country=user_info.origin_country,
        about=user_info.about)
    if form.validate_on_submit():
        avatar_file = form.avatar.data
        if avatar_file.filename:
            filename, file_extension = os.path.splitext(avatar_file.filename)
            img_name = f'{current_user.username.lower()}{file_extension}'
            avatar_file.save(f'travelblog/static/img/avatars/{img_name}')
            user_info.avatar = img_name
        user_info.birthdate = form.birthdate.data
        user_info.gender = form.gender.data
        user_info.job = form.job.data
        user_info.origin_country = form.origin_country.data
        user_info.about = form.about.data
        db.session.commit()
        return redirect(url_for('main.user', username=current_user.username))
    return render_template('edit_profile.html', form=form)
