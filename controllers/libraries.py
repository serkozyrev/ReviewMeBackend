from database import Database
from database import CursorFromConnectionFromPool
from datetime import datetime, timedelta


def all_libraries():
    with CursorFromConnectionFromPool() as cursor:
        if cursor:
            print("Connection pool created successfully")
        cursor.execute('select * from libraryitem')
        user_data = cursor.fetchall()
        return {'libraries':user_data}


def all_library_by_id(userid):
    with CursorFromConnectionFromPool() as cursor:
        if cursor:
            print("Connection pool created successfully")
        cursor.execute('select * from libraryitem where userid = %s', (userid, ))
        user_data = cursor.fetchall()
        library_list = []
        for i in range(len(user_data)):
            library_element = { 'libraryitemid':user_data[i][0],
                'bookcover': user_data[i][3], 'booktitle': user_data[i][2],
                'bookid': user_data[i][4], 'author': user_data[i][5]
            }
            library_list.append(library_element)
        return {'libraries':library_list}


def library_item_deletion(id):
    id_list = id.split(',')
    condition = f'where libraryitemid in ({id_list[0]}'
    for ids in id_list:
        condition += f',{ids}'
    condition += ')'
    with CursorFromConnectionFromPool() as cursor:
        if cursor:
            print("Connection pool created successfully")
        cursor.execute(f'delete from libraryitem {condition}')
        return {"message": "Delete library item success"}


def library_item_adding(user_id, book_title, book_cover, book_id, author):
    with CursorFromConnectionFromPool() as cursor:
        if cursor:
            print("Connection pool created successfully")
        cursor.execute(f"INSERT INTO libraryitem(userid, booktitle, bookcover, bookid, author)  "
                       f"VALUES(%s, %s, %s, %s, %s)",
                       (user_id, book_title, book_cover, book_id, author))
        return {'message': 'Add Library Item Successful'}