from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route("/jobs")
@app.route("/")
def jobs():
    return render_template('index.html')
