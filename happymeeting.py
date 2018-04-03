from flask import Flask, render_template, request, redirect, url_for
from flask_images import Images
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
    return render_template(app_config['LOGPAGE'], posts=Post.select().order_by(Post.date.desc()))


@app.route('/trends/')
def trend_page():
    # img = io.BytesIO()
    # y = [1,2,3,4,5]
    # x = [0,2,1,3,4]
    # plt.plot(x,y)
    # plt.savefig(img, format='png')
    # img.seek(0)
    #
    # plot_url = base64.b64encode(img.getvalue()).decode()
    #
    # return '<img src="data:image/png;base64,{}">'.format(plot_url)
    return render_template(app_config['TRENDPAGE'])


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
    app.run(debug=True, port=5000)
