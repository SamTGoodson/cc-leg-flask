from flask import Blueprint

leg_bp = Blueprint('leg', __name__, template_folder='templates')

from . import routes