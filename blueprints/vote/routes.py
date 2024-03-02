import pandas as pd
from flask import Blueprint, render_template
from app.utils.db import get_db_connection
from app.utils.cluster import start_hierarchical,create_dendrogram
from app.utils.leg_api import find_close_votes
from plotly.offline import plot 
from . import vote_bp


vote_bp = Blueprint('vote', __name__, template_folder='templates')

@vote_bp.route('/')
def vote():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vote;')  
    vote_raw = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    df_vote = pd.DataFrame(vote_raw, columns=columns)
    close_votes = find_close_votes(df_vote)
    Z = start_hierarchical(close_votes)
    dendrogram = create_dendrogram(Z)
    dendrogram_div = plot(dendrogram, output_type='div', include_plotlyjs=False)
    return render_template('vote.html', dendrogram=dendrogram_div)
