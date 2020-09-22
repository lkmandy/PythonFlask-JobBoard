# import g (global namespace) to provide access to the database throughout the application
from flask import Flask, g, request
from flask import render_template, redirect, url_for
import datetime
import sqlite3

PATH = 'db/jobs.sqlite'

app = Flask(__name__)


def open_connection():
    # Global database attribute
    connection = getattr(g, '_connection', None)
    if connection is None:
        # Global database connection
        connection = g._connection = sqlite3.connect(PATH)
    # To make accessing data easier. All rows returned from the database will be named tuples.
    connection.row_factory = sqlite3.Row
    return connection


# Query Database Function: used to query the database
def execute_sql(sql, values=(), commit=False, single=False):
    connection = open_connection()
    cursor = connection.execute(sql, values)
    if commit:
        results = connection.commit()
    else:
        results = cursor.fetchone() if single else cursor.fetchall()

    cursor.close()
    return results


# Makes sure the database connection is closed when the app_context is destroyed
@app.teardown_appcontext
def close_connection(exception):
    connection = getattr(g, '_connection', None)
    if connection is not None:
        connection.close()


@app.route("/jobs")
@app.route("/")
def jobs():
    jobs = execute_sql('SELECT job.id, job.title, job.description, job.salary, employer.id as employer_id, '
                       'employer.name as employer_name FROM job JOIN employer ON employer.id = job.employer_id')
    return render_template('index.html', jobs=jobs)


@app.route("/job/<job_id>")
def job(job_id):
    job = execute_sql('SELECT job.id, job.title, job.description, job.salary, employer.id as employer_id, '
                      'employer.name as employer_name FROM job JOIN employer ON employer.id = job.employer_id WHERE '
                      'job.id = ?', [job_id], single=True)
    # job=job : give the template access to the job data
    return render_template('job.html', job=job)


@app.route("/employer/<employer_id>")
def employer(employer_id):
    employer = execute_sql('SELECT * FROM employer WHERE id=?', [employer_id], single=True)

    # Query to get all jobs listed by an employer
    jobs = execute_sql('SELECT job.id, job.title, job.description, job.salary FROM job JOIN employer ON'
                       ' employer.id = job.employer_id WHERE employer.id = ?', [employer_id])

    # Query to get all reviews for an employer
    reviews = execute_sql('SELECT review, rating, title, date, status FROM review JOIN employer ON '
                          'employer.id = review.employer_id WHERE employer.id = ?', [employer_id])
    return render_template('employer.html', employer=employer, jobs=jobs, reviews=reviews)


@app.route("/employer/<employer_id>/review")
def review(employer_id, methods=('GET', 'POST')):
    if request.method == 'POST':
        review = request.form['review']
        rating = request.form['rating']
        title = request.form['title']
        status = request.form['status']
        date = datetime.datetime.now().strftime("%m/%d/%Y")

        execute_sql('INSERT INTO review (review, rating, title, date, status, employer_id) VALUES (?, ?, ?, ?, ?, ?)',
                    (review, rating, title, date, status, employer_id), commit=True)

        return redirect(url_for('employer', employer_id=employer_id))

    return render_template("review.html", employer_id=employer_id)
