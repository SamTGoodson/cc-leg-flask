from flask import Flask, render_template
from app.blueprints.vote.routes import vote_bp
from app.blueprints.leg.routes import leg_bp

app = Flask(__name__)


app.register_blueprint(vote_bp, url_prefix='/vote')
app.register_blueprint(leg_bp, url_prefix='/leg')

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
