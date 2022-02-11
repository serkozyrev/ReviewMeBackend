from database import Database
from database import CursorFromConnectionFromPool

def all_wishlist_item():
    try:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('select * from wishlist')
            wishlist_data = cursor.fetchall()
            return{'wishlist':wishlist_data}
    except:
        return {'message': 'Something went wrong when fetching wishlist'}

def wishlist_item_by_id(userId):
    try:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"SELECT * FROM wishlist WHERE userid=%s", (userId, ))
            wishlist_by_user = cursor.fetchall()
            wishlist_list = []
            for i in range(len(wishlist_by_user)):
                wishlist_element={ 'wishlistid': wishlist_by_user[i][0],
                    'bookcover': wishlist_by_user[i][3], 'booktitle': wishlist_by_user[i][2],
                    'bookid': wishlist_by_user[i][4], 'author':wishlist_by_user[i][5]
                }
                wishlist_list.append(wishlist_element)
            return{'wish_list': wishlist_list}
    except:
        return{'message':'Something went wrong while fetching wishlists'}


def wishlist_item_add(user_id, book_title, book_cover, book_id, author):
    try:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"INSERT INTO wishlist(userid, booktitle, bookcover, bookid, author)  "
                           f"VALUES(%s, %s, %s, %s, %s)", (user_id, book_title, book_cover, book_id, author))
            return{'message':'Add wishlist item successfully'}
    except:
        return{'message': 'Adding wishlist item failed'}