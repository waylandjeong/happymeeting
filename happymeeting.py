from flask import Flask, render_template, request, redirect, url_for
from flask_images import Images
from datetime import datetime, timedelta
import os
import calendar
import random
from model import *
from peewee import *
import json
# import matplotlib.pyplot as plt
# import io
# import base64

app_config = {}
app = Flask(__name__)
app.secret_key = 'monkey'
images = Images(app)
LOG_ENTRIES = 20


def init():
    with open('app_config.json') as json_data_file:
        data = json.load(json_data_file)
    app_config['NAME'] = data['dbname']
    app_config['HOMEPAGE'] = data['homepage']
    app_config['POSTPAGE'] = data['postpage']
    app_config['ABOUTPAGE'] = data['aboutpage']
    app_config['CONTACTPAGE'] = data['contactpage']
    app_config['LOGPAGE'] = data['logpage']
    app_config['TRENDPAGE'] = data['trendpage']
    app_config['DEBUG'] = data['debug']
    app_config['TESTING'] = data['testing']
    # is there a better way to do this?
    global db
    db = SqliteDatabase(app_config['NAME'])
    proxy.initialize(db)
    print('setup database')


@app.before_request
def before_request():
    # create db if needed and connect
    print('initializing database')
    initialize_db()


@app.teardown_request
def teardown_request(exception):
    # close db connection
    print('closing database')
    db.close()


@app.route('/')
def home():
    return render_template(app_config['HOMEPAGE'])


@app.route('/new_post/')
def new_post():
    score = request.args.get('score', default='', type=str)
    print(score)
    return render_template(app_config['POSTPAGE'], score=score)


@app.route('/about/')
def about():
    return render_template(app_config['ABOUTPAGE'])


@app.route('/contact/')
def contact():
    return render_template(app_config['CONTACTPAGE'])


@app.route('/log/')
def log_page():
    # all_posts = Post.select().order_by(Post.date.descr())
    all_posts = Post.select().order_by(Post.date.desc())
    filtered_posts = []
    count = 0
    for post in all_posts:
        filtered_posts.append(post)
        count+=1
        if count >= LOG_ENTRIES:
            break
    return render_template(app_config['LOGPAGE'], posts=filtered_posts)


# Simple class to implement an enumerated type for the graph duration interval
class GraphDurationType:
    day, month, year = range(3)


# Helper function to build a list of date keys
def build_date_keys(num, gtype):
    keys = []
    weekdays =[]
    if gtype == GraphDurationType.day:
        for i in range(0, num):
            date_n_days_ago = datetime.datetime.now() - timedelta(days=(num-i-1))
            weekdays.append(calendar.day_name[date_n_days_ago.weekday()])
            keys.append(date_n_days_ago.strftime('%m%d%Y'))
    elif gtype == GraphDurationType.month:
        pass
    elif gtype == GraphDurationType.year:
        pass

    return keys, weekdays


# Helper function to gather daily average happiness scores
# Schema: <primary key> <date> <title> <text> <score>
def create_score_dict(keyval, keys, posts):
    score_dict = dict.fromkeys(keys, None)
    for score in score_dict:
        score_dict[score] = [0, 0]
    for post in posts:
        key = post.date.strftime(keyval)
        if key in score_dict:
            entry = [score_dict[key][0] + 1, score_dict[key][1] + post.score]
            score_dict[key] = entry
    for key in score_dict:
        print("%s -> %d %d" % (key, score_dict[key][0], score_dict[key][1]))
    return score_dict


# Helper function to generate a list of the past N days or months. Function accepts two parameters:
# First parameter is 'n' which is the number of items. The second parameter is an enumerated type that indcates
# the duration of the graph. The third parameter is the list of posts in the posts database.
def build_graph_data(num, gtype, posts):
    # dummy date for test
    # labels = ["March","April","May","June","July","August"]
    values = []
    keys, labels = build_date_keys(num, GraphDurationType.day)
    print(keys, labels)
    if gtype == GraphDurationType.day:
        scores = create_score_dict('%m%d%Y', keys, posts)
        print(scores)
        for score in sorted(scores):
            if scores[score][0] == 0:
                values.append(0)
            else:
                print("scores = %d / %d" % (scores[score][1], scores[score][0]))
                values.append(scores[score][1] // scores[score][0])
    elif gtype == GraphDurationType.month:
        pass
    elif gtype == GraphDurationType.year:
        pass
    # return 2d list
    return labels, values


# Create simple chart that tracks happiness trend. Calculate a happiness score for that day. Simply sum all happiness
# scores and create a percentage score based on maximum happiness (5 * # entries). Plot this score per day for the
# past <n> days.
@app.route('/trends/')
def trend_page():
    legend = '5=very happy 4=happy 3=neutral 2=sad 1=very sad 0=no data'
    labels, values = build_graph_data(5, GraphDurationType.day, Post.select().order_by(Post.date.desc()))
    return render_template(app_config['TRENDPAGE'], labels=labels, values=values, legend=legend)


@app.route('/create/', methods=['POST'])
def create_post():
    score = request.args.get('score', default=0, type=int)
    if score == 0:
        score = request.form.get('entry_score', default=0, type=int)
    # create the new post
    Post.create(
        title=request.form.get('title', default='', type=str),
        text=request.form.get('text', default='', type=str),
        score=score
    )

    # return the user to the home page
    print(url_for('home'))
    return redirect(url_for('home'))


if __name__ == '__main__':
    init()
    if app_config['DEBUG'] == 'True':
        print("Debugging Enabled")
        # remove database fle if it exists
        try:
            os.remove(app_config['NAME'])
        except OSError:
            pass
        # populate database
        print('initializing database')
        initialize_db()
        for i in range(0, 10):
            d = datetime.datetime.now() - timedelta(days=i)
            for j in range(0, 5):
                Post.create(
                    date=d.date(),
                    title="Meeting title for %d / %d" % (i, j),
                    text="Description of meeting %d / %d" % (i, j),
                    score=random.randint(1, 5)
                )

    app.run(host='0.0.0.0', debug=True, port=8080)
