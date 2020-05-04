from flask import Blueprint

bp = Blueprint('main', __name__)

from travelblog.main import routes