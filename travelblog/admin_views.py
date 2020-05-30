from os import path
from datetime import datetime

from flask import current_app
from flask_login import current_user
from wtforms.validators import Required
from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.contrib.fileadmin import FileAdmin
from travelblog.models import (User, UserInfo, Country, CountryInfo, Article,
                               Comment, Message, Role)
from travelblog import admin, db


class MyAdminView(AdminIndexView):

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role


class OwnerView(ModelView):

    def on_model_delete(self, model):
        print(f'{model} deleted by {current_user} on {datetime.now()}')

    form_choices = {
        'role_name': [
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('editor', 'Editor'),
            ('moderator', 'Moderator')
        ],

        'article_type': [
            ('Blogpost', 'Blogpost'),
            ('News', 'News'),
            ('Guide', 'Guide'),
        ],

        'gender': [
            ('M', 'Male'),
            ('F', 'Female'),
        ]
    }

    column_exclude_list = ['password_hash', ]

    form_excluded_columns = ['deleted', 'role', 'password_hash']

    def is_accessible(self):
        return (current_user.role.role_name == 'owner'
                if current_user.is_authenticated else False)


class AdminView(OwnerView):

    def is_accessible(self):
        return (super().is_accessible()
                or (current_user.role.role_name == 'admin'
                    if current_user.is_authenticated else False))


class EditorView(AdminView):

    def is_accessible(self):
        return (super().is_accessible()
                or (current_user.role.role_name == 'editor'
                    if current_user.is_authenticated else False))


class ModeratorView(AdminView):

    def is_accessible(self):
        return (super().is_accessible()
                or (current_user.role.role_name == 'moderator'
                    if current_user.is_authenticated else False))


class MyFileAdmin(FileAdmin):

    def is_accessible(self):
        return (current_user.role.role_name in ['admin', 'owner']
                if current_user.is_authenticated else False)


admin._set_admin_index_view(MyAdminView())

admin.add_view(OwnerView(User, db.session))
admin.add_view(OwnerView(UserInfo, db.session))
admin.add_view(EditorView(Country, db.session))
admin.add_view(EditorView(CountryInfo, db.session))
admin.add_view(EditorView(Article, db.session))
admin.add_view(OwnerView(Comment, db.session))
admin.add_view(OwnerView(Message, db.session))
admin.add_view(OwnerView(Role, db.session))

static_path = path.join(path.dirname(__file__), 'static')
admin.add_view(MyFileAdmin(static_path, base_url='static', name='Static'))
