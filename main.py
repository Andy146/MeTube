#!/usr/bin/python3

import mysql.connector as mariadb
import flask
import sys
import os
from urllib.parse import quote

root = os.path.realpath(os.path.dirname(__file__))

app = flask.Flask(__name__, template_folder=f'{root}/website/html', static_folder=root)
print(app.root_path)
print(root)

def db_connect():
    try:
        conn = mariadb.connect(
            user="admin",
            password="Passw0rd",
            host="localhost",
            port=3306,
            db='me_tube')
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    
    return conn

@app.route('/')
def home():
    conn = db_connect()

    cursor = conn.cursor(dictionary=True)   #Means returned data will be in a dictionary instead of a tuple
    query = 'select * from video'

    cursor.execute(query)

    db_return = cursor.fetchall()
    cursor.close()
    conn.close()


    return flask.render_template('home.html', previews=db_return)

@app.route('/play/<int:video_id>/', methods=["GET", "POST"])
def player(video_id):
    conn = db_connect()

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

    cursor.close()
    conn.close()

    return flask.render_template('player.html', video=video_data[0], previews=preview_data)
    # return video_data[0]

@app.route('/upload/')
def upload_page():
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
            "uploader":1
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
    conn = db_connect()
    
    cursor = conn.cursor()

    query = 'INSERT INTO video (title, description, uploader_id) VALUES (%s, %s, %s)'

    try:
        vals = (data['title'], data['desc'], data['uploader'])
    except:
        vals = (data['title'], data['desc'], 1)
    finally:
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
    
    print(tag_ids)
    print(data['tags'])

    for tag_id in tag_ids:
        query = 'INSERT INTO video_tags (video_id, tag_id) VALUES (%s, %s)'
        vals = (id, tag_id)
        cursor.execute(query, vals)
        conn.commit()

    
    return id

@app.route('/search/', methods=['GET'])
def search_page():
    query = flask.request.args['query']
    # query = quote(query)
    results = search(query)
    return flask.render_template('search.html', query=query, results=results)

def search(query):
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    
    sql_query = "SELECT * FROM video"
    cursor.execute(sql_query)


    db_return = cursor.fetchall()
    results = set()     #Inits as set to not have duplicate results
    query = query.split(' ')

    for keyword in query:
        for video in db_return:
            if(keyword.lower() in video['title'].lower()):
                results.add(video['video_id'])
            elif(keyword.lower() in video['description'].lower()):
                results.add(video['video_id'])
    
    if(len(results)==1):        #If there is only one result, then you can't create a valid tuple for sql, therefore this is an exception
        results = list(results)
        results = int(results[0])
        sql = f"SELECT * FROM video WHERE video_id={results}"
    elif(len(results)==0):
        return list()
    else:
        results = tuple(results)
        sql = f"SELECT * FROM video WHERE video_id IN {results}"
        
    cursor.execute(sql)

    results = cursor.fetchall()

    return results
