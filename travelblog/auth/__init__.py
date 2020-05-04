from flask import Blueprint

bp = Blueprint('auth', __name__)

from travelblog.auth import routes