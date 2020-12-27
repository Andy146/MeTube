#!/usr/bin/python3

import mysql.connector as mariadb
import flask
import sys
import os
from urllib.parse import quote
import lib.search as search
import lib.db_connect as db_lib
import uuid

root = os.path.realpath(os.path.dirname(__file__))

app = flask.Flask(__name__, template_folder=f'{root}/website/html', static_folder=root)
app.secret_key = uuid.uuid4().hex
print(app.root_path)
print(root)

@app.route('/')
def home():
    conn = db_lib.db_connect()

    cursor = conn.cursor(dictionary=True)   #Means returned data will be in a dictionary instead of a tuple
    query = 'select * from video'

    cursor.execute(query)

    db_return = cursor.fetchall()
    cursor.close()
    conn.close()


    return flask.render_template('home.html', previews=db_return)

@app.route('/play/<int:video_id>/', methods=["GET", "POST"])
def player(video_id):
    conn = db_lib.db_connect()

    cursor = conn.cursor(dictionary=True)
    query = f'select * from video where video_id={video_id}'
    cursor.execute(query)

    video_data = cursor.fetchall()

    query = f'select * from video where video_id between {video_id+1} and {video_id+10}'
    cursor.execute(query)
    preview_data = cursor.fetchall()

    if(len(preview_data)<5):
        query = f'select * from video where video_id between {video_id-10} and {video_id-1}'
        cursor.execute(query)
        preview_data = cursor.fetchall()
    
    query = f"SELECT user_id, username FROM user WHERE user_id={video_data[0]['uploader_id']}"
    cursor.execute(query)
    uploader = cursor.fetchall()[0]

    try:
        root = os.path.realpath(os.path.dirname(__file__))
        with open(f'{root}/users/{uploader["user_id"]}/profile.png', 'r') as f:
            f.close()
        uploader['img'] = f'/MeTube/users/{uploader["user_id"]}/profile.png'
    except FileNotFoundError:
        uploader['img'] = '/MeTube/assets/blank_user.svg'

    cursor.close()
    conn.close()

    return flask.render_template('player.html', video=video_data[0], previews=preview_data, uploader=uploader)
    # return video_data[0]

@app.route('/upload/')
def upload_page():
    if('username' not in flask.session):    #Redirects users to login page if they are trying to upload without being logged in
        return flask.redirect(flask.url_for('login'))
    return flask.render_template('upload.html')

@app.route('/uploader/', methods=['POST'])
def upload_files():
    root = os.path.realpath(os.path.dirname(__file__))
    if flask.request.method == 'POST':
        video = flask.request.files['video_upload']
        thumb = flask.request.files['thumb_upload']


        data = {
            "title":flask.request.form['title'],
            "desc":flask.request.form['desc'],
            "uploader":flask.session['user_id']
        }
        try:
            tags = flask.request.form['tags']
            tags = tags.replace(', ', ',')
            tags = tags.split(',')
            data['tags'] = tags
        except:
            pass

        id = insert_video_data(data)

        os.makedirs(f'{root}/videos/{id}')
        video.save(f'{root}/videos/{id}/video.mp4')
        thumb.save(f'{root}/videos/{id}/thumbnail.png')

        return flask.redirect('/')
    else:
        return flask.redirect('/')

def insert_video_data(data):
    conn = db_lib.db_connect()
    
    cursor = conn.cursor()

    query = 'INSERT INTO video (title, description, uploader_id) VALUES (%s, %s, %s)'

    vals = (data['title'], data['desc'], data['uploader'])
    cursor.execute(query, vals)

    conn.commit()
    id = cursor.lastrowid

    tag_ids = []
    for tag in data['tags']:
        tag = (tag,)
        try:
            query = 'INSERT INTO tags (tag) VALUES (%s)'
            cursor.execute(query, tag)
            conn.commit()
            tag_ids.append(cursor.lastrowid)
        except:
            query = 'SELECT tag_id FROM tags WHERE tag=(%s)'
            cursor.execute(query, tag)
            _temp_id = cursor.fetchall()[0][0]
            tag_ids.append(_temp_id)
    
    # print(tag_ids)
    # print(data['tags'])

    for tag_id in tag_ids:
        query = 'INSERT INTO video_tags (video_id, tag_id) VALUES (%s, %s)'
        vals = (id, tag_id)
        cursor.execute(query, vals)
        conn.commit()

    conn.close()
    return id

@app.route('/search/', methods=['GET'])
def search_page():
    query = flask.request.args['query']
    # query = quote(query)
    results = search.search(query)
    return flask.render_template('search.html', query=query, results=results)

@app.route('/user/<string:username>')
def profile_page(username):
    conn = db_lib.db_connect()
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM user WHERE username='{username}'"

    cursor.execute(query)
    user_data = cursor.fetchall()
    if(len(user_data) == 0):
        user_exists = False
        user_has_videos = False
        video_data = list()
    else:
        user_exists = True
        try:
            root = os.path.realpath(os.path.dirname(__file__))
            with open(f'{root}/users/{user_data[0]["user_id"]}/profile.png', 'r') as f:
                f.close()
            user_data[0]['img'] = f'/MeTube/users/{user_data[0]["user_id"]}/profile.png'
        except FileNotFoundError:
            user_data[0]['img'] = '/MeTube/assets/blank_user.svg'

        query = f"SELECT * FROM video WHERE uploader_id={user_data[0]['user_id']}"
        cursor.execute(query)
        video_data = cursor.fetchall()
        if(len(video_data) == 0):
            user_has_videos = False
        else:
            user_has_videos = True
    conn.close()
    return flask.render_template('profile.html', user_data=user_data, videos=video_data, user_exists=user_exists, username=username, user_has_videos=user_has_videos)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if(flask.request.method == 'POST'):
        conn = db_lib.db_connect()
        cursor = conn.cursor(dictionary=True)

        query = f"SELECT * FROM user WHERE username='{flask.request.form['username']}'"
        cursor.execute(query)
        user_data = cursor.fetchall()
        conn.close()

        if(len(user_data) == 0):
            failure = True
            return flask.render_template('login.html', failure=failure)
        else:
            user_data = user_data[0]
            if(user_data['password'] == flask.request.form['password']):
                flask.session['username'] = flask.request.form['username']
                flask.session['user_id'] = user_data['user_id']
                try:
                    root = os.path.realpath(os.path.dirname(__file__))
                    with open(f'{root}/users/{user_data["user_id"]}/profile.png', 'r') as f:
                        f.close()
                    flask.session['default_img'] = False
                except FileNotFoundError:
                    flask.session['default_img'] = True
                return flask.redirect(flask.url_for('home'))
            else:
                failure = True
                return flask.render_template('login.html', failure=failure)
    return flask.render_template('login.html')

@app.route('/logout/')
def logout():
    if('username' in flask.session):
        flask.session.pop('username', None)
        flask.session.pop('user_id', None)
        flask.session.pop('default_img', None)
    return flask.redirect(flask.url_for('home'))
