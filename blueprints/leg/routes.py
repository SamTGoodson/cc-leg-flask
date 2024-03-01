from flask import Blueprint, render_template
from app.utils.db import get_db_connection

leg_bp = Blueprint('leg', __name__, template_folder='templates')

@leg_bp.route('/')
def leg():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM leg;')
    leg_data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('leg.html', data=leg_data)