import pandas 
from flask import Flask, render_template
import psycopg2
import sqlalchemy
import os
from config import psql_user,psql_pass

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='city-council',
                            user=psql_user,
                            password=psql_pass)
    return conn



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/leg')
def leg():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM leg;')
    leg_data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('leg.html', data=leg_data)

@app.route('/vote')
def vote():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vote;')
    vote_data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('vote.html', data=vote_data)

if __name__ == '__main__':
    app.run(debug=True)
