import lib.db_connect as db_lib
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