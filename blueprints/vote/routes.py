from flask import Blueprint, render_template
from app.utils.db import get_db_connection
from . import vote_bp


vote_bp = Blueprint('vote', __name__, template_folder='templates')

@vote_bp.route('/')
def vote():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vote;')  
    vote_data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('vote.html', data=vote_data)
