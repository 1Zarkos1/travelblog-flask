import os
from datetime import datetime

from flask import (render_template, redirect, request, url_for, flash, abort,
                   json, escape, current_app, session)
from flask_login import current_user, login_required

from travelblog.main import bp
from travelblog import db
from travelblog.models import (User, Country, Article, Comment, Message,
                               user_followers, country_tag, country_follower)
from travelblog.main.forms import (EditProfileForm, ArticleForm, CommentForm,
                                   MessageForm)


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.info.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    if request.method == 'POST':
        session['feed'] = not session.get('feed', False)
        return redirect(url_for('main.index'))
    if session.get('feed', False) == False or current_user.is_anonymous:
        articles = Article.query.order_by(
            Article.date_posted.desc()).paginate(page=page, per_page=2)
    else:
        users_art = db.session.query(Article.id).filter(
            Article.user_id.in_(db.session.query(user_followers.c.followed_id)
            .filter(user_followers.c.follower_id == current_user.id)))
        count_art = (db.session.query(country_tag.c.article_id)
                     .filter(country_tag.c.country_id.in_(db.session.query(
                         country_follower.c.country_id).filter(
                         country_follower.c.user_id == current_user.id)
                     )).distinct())
        articles = Article.query.filter(
            Article.id.in_(users_art) | Article.id.in_(count_art)).paginate(
            page=page, per_page=3)
    return render_template('index.html', articles=articles)


@bp.route('/create_article/', methods=['GET', 'POST'])
@login_required
def create_article():
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article(article_author=current_user,
                          country_tags=form.country_tag.data, 
                          title=form.title.data,
                          article_type=form.article_type.data,
                          body=form.hidden_body.raw_data[1])
        db.session.add(article)
        db.session.commit()
        flash('Your article was added successfully!', category='info')
        return redirect(url_for('main.index'))
    return render_template('create_article.html', form=form)


@bp.route('/edit_article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.filter_by(id=id).first_or_404()
    if current_user != article.article_author:
        abort(403)
    form = ArticleForm(article_type=article.article_type, title=article.title,
                       country_tag=article.country_tags, hidden_body=article.body)
    if form.validate_on_submit():
        country = Country.query.filter(
            Country.name.in_(form.country_tag.data)).all()
        article.country_tags = country
        article.title = form.title.data
        article.article_type = form.article_type.data
        article.body = form.hidden_body.raw_data[1]
        article.last_updated = datetime.utcnow()
        db.session.commit()
        flash('Your article was updated!', category='info')
        return redirect(url_for('main.article_view', id=id))
    return render_template('edit_article.html', form=form, id=id)


@bp.route('/article/<int:id>/', methods=['GET', 'POST'])
def article_view(id):
    article = Article.query.filter_by(id=id).first_or_404()
    form = CommentForm()
    if form.validate_on_submit():
        comment_id = form.id.raw_data[1]
        if comment_id:
            comment = Comment.query.get_or_404(int(comment_id))
            comment.body = form.hidden_body.raw_data[1]
            comment.last_updated = datetime.utcnow()
        else:
            comment = Comment(article=article, comment_author=current_user,
                              body=form.hidden_body.raw_data[1])
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
    print(current_app.jinja_env.lstrip_blocks)
    print(current_app.jinja_env.trim_blocks)
    country_list = Country.query.all()
    return render_template('country_list.html', countries=country_list)


@bp.route('/country/<int:id>/')
def country_view(id):
    page = request.args.get('page', 1, type=int)
    country = Country.query.get(id)
    articles = country.articles.paginate(page=page, per_page=2)
    return render_template('country.html', country=country, articles=articles)


@bp.route('/gear/')
def gear():
    return render_template('base.html')


@bp.route('/about_me/')
@login_required
def about_me():
    return render_template('base.html')


@bp.route('/user/<username>/')
def user(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    articles = Article.query.filter_by(
        article_author=user).paginate(page=page, per_page=2)
    return render_template('profile.html', user=user, articles=articles)


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
        user_info.origin_country = form.origin_country.data.name
        user_info.about = form.about.data
        db.session.commit()
        return redirect(url_for('main.user', username=current_user.username))
    return render_template('edit_profile.html', form=form)


@bp.route('/likes_control/<int:id>/<action>/')
@login_required
def likes_control(id, action):
    article = Article.query.get(id)
    main_list, sub_list = ((article.likes, article.dislikes) if action == 'like'
                           else (article.dislikes, article.likes))
    if current_user in sub_list:
        sub_list.remove(current_user)
    if current_user in main_list:
        main_list.remove(current_user)
    else:
        main_list.append(current_user)
    db.session.commit()
    return json.dumps(len(article.likes)-len(article.dislikes)), 200


@bp.route('/send_message/<int:id>', methods=['GET', 'POST'])
@login_required
def send_message(id):
    user = User.query.get(id)
    if (not current_user.is_authenticated or current_user.id == id
            or user == None):
        flash("You can't send message to this user!")
        return redirect(url_for('main.user', username=user.username))
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(title=form.title.data, body=form.body.data,
                          sender=current_user, recipient=user)
        db.session.add(message)
        db.session.commit()
        flash('Your message was sent')
        return redirect(url_for('main.user', username=user.username))
    return render_template('send_message.html', form=form, user=user)


@bp.route('/private_messages/')
@login_required
def messages():
    received = current_user.received_messages.filter(
        (Message.deleted == None) | (Message.deleted == False)).all()
    sent = current_user.sent_messages.filter(
        (Message.deleted == None) | (Message.deleted == True)).all()
    return render_template('private_messages.html', sent=sent,
                           received=received, now=datetime.utcnow())


@bp.route('/private_messages/<int:id>/')
@login_required
def message(id):
    message = Message.query.get_or_404(id)
    if current_user not in (message.recipient, message.sender):
        abort(403)
    if current_user == message.recipient and message.seen == False:
        message.seen = True
        db.session.commit()
    return render_template('message.html', message=message)


@bp.route('/private_messages/delete/<int:id>/')
@login_required
def delete_message(id):
    message = Message.query.get_or_404(id)
    if current_user not in (message.recipient, message.sender):
        abort(403)
    if current_user == message.sender:
        if message.deleted == None:
            message.deleted = False
        elif message.deleted == True:
            db.session.delete(message)
    else:
        if message.deleted == None:
            message.deleted = True
        elif message.deleted == False:
            db.session.delete(message)
    db.session.commit()
    return redirect(url_for('main.messages'))


@bp.route('/comment/delete/<int:id>/')
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    if current_user != comment.comment_author:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('main.article_view', id=comment.article_id))


@bp.route('/follow_country/<int:id>/')
@login_required
def follow_country(id):
    country = Country.query.get(id)
    if current_user in country.followers:
        country.followers.remove(current_user)
    else:
        country.followers.append(current_user)
    db.session.commit()
    return redirect(url_for('main.country_view', id=id))


@bp.route('/user/<username>/follow/')
@login_required
def follow_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user in user.followers:
        user.followers.remove(current_user)
    else:
        user.followers.append(current_user)
    db.session.commit()
    return redirect(url_for('main.user', username=username))


@bp.route('/check_new_messages/')
@login_required
def check_new_messages():
    new_messages = current_user.received_messages.filter(
        (Message.deleted == None) | (Message.deleted == False),
        Message.seen == False).count()
    return json.dumps(new_messages)


@bp.route('/search_query/')
def search_query():
    query = request.args.get('query', '')
    subject = request.args.get('subject', '')
    if query:
        articles = Article.query.filter(
            Article.title.contains(query)).limit(3).all()
        users = User.query.filter(User.username.contains(query)).limit(3).all()
        countries = Country.query.filter(
            Country.name.contains(query)).limit(3).all()

        return render_template('_search_query.html', articles=articles,
                               countries=countries, users=users)
    return ''