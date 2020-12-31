import lib.db_connect as db_lib
import os
def search(query):
    conn = db_lib.db_connect()
    cursor = conn.cursor(dictionary=True)
    
    sql_query = "SELECT * FROM video"
    cursor.execute(sql_query)
    db_return = cursor.fetchall()

    sql_query = "SELECT * FROM tags"
    cursor.execute(sql_query)
    tags = cursor.fetchall()

    results = set()     #Inits as set to not have duplicate results
    while True:
        if(query[0]==' '):
            query = query[1:]
        else:
            break
    query = query.split(' ')

    sql_query = "SELECT user_id, username FROM user"
    cursor.execute(sql_query)
    users = cursor.fetchall()
    user_results = list()

    for keyword in query:
        for video in db_return:
            if(keyword.lower() in video['title'].lower()):
                results.add(video['video_id'])
            elif(keyword.lower() in video['description'].lower()):
                results.add(video['video_id'])
        for tag in tags:
            if(keyword.lower() == tag['tag'].lower()):
                sql_query = f"SELECT video_id FROM video_tags WHERE tag_id={tag['tag_id']}"
                cursor.execute(sql_query)
                _temp_videos = cursor.fetchall()

                for dictionary in _temp_videos:
                    results.add(dictionary['video_id'])
        for user in users:
            if(keyword.lower() in user['username'].lower() or user['username'].lower() in keyword.lower()):
                try:
                    root = os.path.realpath(os.path.dirname("__main__"))
                    with open(f'{root}/users/{user["user_id"]}/profile.png', 'r') as f:
                        f.close()
                    user['img'] = f'/MeTube/users/{user["user_id"]}/profile.png'
                except FileNotFoundError:
                    user['img'] = '/MeTube/assets/blank_user.svg'
                user_results.append(user)
                sql_query = f"SELECT video_id FROM video WHERE uploader_id={user['user_id']}"
                cursor.execute(sql_query)
                _temp_videos = cursor.fetchall()

                for video in _temp_videos:
                    results.add(video['video_id'])

    if(len(results)==1):        #If there is only one result, then you can't create a valid tuple for sql, therefore this is an exception
        results = list(results)
        results = int(results[0])
        sql_query = f"SELECT * FROM video WHERE video_id={results}"
    elif(len(results)==0):
        cursor.close()
        conn.close()
        return [user_results]
    else:
        results = tuple(results)
        sql_query = f"SELECT * FROM video WHERE video_id IN {results}"
        
    cursor.execute(sql_query)

    results = cursor.fetchall()


    cursor.close()
    conn.close()

    results = [user_results, results]

    return results