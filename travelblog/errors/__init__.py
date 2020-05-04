from flask import Blueprint

bp = Blueprint('errors', __name__)

from travelblog.errors import handlers