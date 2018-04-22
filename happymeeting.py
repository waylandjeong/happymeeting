from flask import Flask, render_template, request, redirect, url_for
from flask_images import Images
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import os
import calendar
import random
from model import *
from peewee import *
import json

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
    return render_template(app_config['HOMEPAGE'], page="home")


@app.route('/new_post/')
def new_post():
    score = request.args.get('score', default='', type=str)
    print(score)
    return render_template(app_config['POSTPAGE'], page="post", score=score)


@app.route('/about/')
def about():
    return render_template(app_config['ABOUTPAGE'], page="about")


@app.route('/contact/')
def contact():
    return render_template(app_config['CONTACTPAGE'], page="contact")


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
    return render_template(app_config['LOGPAGE'], page="log", posts=filtered_posts)


# Simple class to implement an enumerated type for the graph duration interval
class GraphDurationType:
    day, week, month, year = range(4)


# Helper function to build a list of date keys
def build_date_keys(num, gtype):
    keys = []
    weekdays =[]
    if gtype == GraphDurationType.day:
        for index in range(0, num):
            date_n_days_ago = datetime.datetime.now() - timedelta(days=(num-index-1))
            weekdays.append(calendar.day_name[date_n_days_ago.weekday()])
            keys.append(date_n_days_ago.strftime('%Y%m%d'))
    elif gtype == GraphDurationType.week:
        block = 7
        for index in range(0, num):
            print((num*block)-(index*block)-block)
            date_n_days_ago = datetime.datetime.now() - timedelta(days=((num*block)-(index*block)-block))
            weekdays.append("week" + date_n_days_ago.strftime("%U"))
            keys.append(date_n_days_ago.strftime('%Y%U'))
    elif gtype == GraphDurationType.month:
        curr_mon = datetime.datetime.now().month
        count = 0
        for index in range(num-1,-1,-1):
            mon = ((curr_mon-index+12)%12)
            adj_mon = mon if mon != 0 else 12
            weekdays.append(calendar.month_name[adj_mon])
            mon_id = list(calendar.month_name).index(calendar.month_name[adj_mon])
            d_obj = datetime.datetime.now() - relativedelta(months=index)
            keys.append(d_obj.strftime("%Y") + "%02d" % mon_id)
            count += 1
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
    return score_dict


# Helper function to generate a list of the past N days or months. Function accepts two parameters:
# First parameter is 'n' which is the number of items. The second parameter is an enumerated type that indcates
# the duration of the graph. The third parameter is the list of posts in the posts database.
def build_graph_data(num, gtype, posts):
    # dummy date for test
    # labels = ["March","April","May","June","July","August"]
    values = []
    keys, labels = build_date_keys(num, gtype)
    if app_config['DEBUG'] == 'True':
        print("keys, labels in build_graph_data =>", keys, labels)
    if gtype == GraphDurationType.day:
        key_val = '%Y%m%d'
    elif gtype == GraphDurationType.week:
        key_val = '%Y%U'
    elif gtype == GraphDurationType.month:
        key_val = '%Y%m'
    elif gtype == GraphDurationType.year:
        pass

    # return 2d list
    scores = create_score_dict(key_val, keys, posts)
    if app_config['DEBUG'] == 'True':
        print("scores in build_graph_data =>", scores)
    for score in sorted(scores, key=lambda x: datetime.datetime.strptime(x, key_val)):
        if scores[score][0] == 0:
            values.append(0)
        else:
            values.append(int(round(float(scores[score][1]) / float(scores[score][0]))))
    return labels, values


# Create simple chart that tracks happiness trend. Calculate a happiness score for that day. Simply sum all happiness
# scores and create a percentage score based on maximum happiness (5 * # entries). Plot this score per day for the
# past <n> days.
@app.route('/trends/')
@app.route('/trends/<string:duration>/')
def trend_page(duration=None):
    steps = 5
    legend = '5=very happy 4=happy 3=neutral 2=sad 1=very sad 0=no data'
    if duration == "days" or duration is None:
        labels, values = build_graph_data(steps, GraphDurationType.day, Post.select().order_by(Post.date.desc()))
    elif duration == "weeks":
        labels, values = build_graph_data(steps, GraphDurationType.week, Post.select().order_by(Post.date.desc()))
    elif duration == "months":
        labels, values = build_graph_data(steps, GraphDurationType.month, Post.select().order_by(Post.date.desc()))
    elif duration == "years":
        pass
    if app_config['DEBUG'] == 'True':
        print("labels in trend_page =>", labels)
        print("values in trend_page =>", values)
    return render_template(app_config['TRENDPAGE'], page="trends", steps=steps, labels=labels, values=values, legend=legend)


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
    if app_config['DEBUG'] == 'True':
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
        for i in range(0, 100):
            d = datetime.datetime.now() - timedelta(days=i)
            for j in range(0, 5):
                Post.create(
                    date=d.date(),
                    title="Meeting title for %d / %d" % (i, j),
                    text="Description of meeting %d / %d" % (i, j),
                    score=random.randint(1, 5)
                )

    app.run(host='0.0.0.0', debug=True, port=8080)
