from database import Database
from database import CursorFromConnectionFromPool
from datetime import datetime, timedelta


def all_reviews():
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute('SELECT * FROM review INNER JOIN usr ON review.userid=usr.userid')
        reviews_data = cursor.fetchall()
        return {'reviews':reviews_data}


def review_by_id(bookId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"SELECT * FROM review r INNER JOIN userdetails u ON r.userid=u.userid WHERE r.bookid=%s"
                       f" AND isActive=true ORDER BY updatedate DESC", (bookId, ))
        reviews_by_book = cursor.fetchall()
        review_list = []
        for i in range(len(reviews_by_book)):
            date=datetime.strftime(reviews_by_book[i][2], '%a, %d %b %Y')
            review_element={
                'reviewid': reviews_by_book[i][0], 'updatedate': date, 'comment': reviews_by_book[i][3],
                'rating': reviews_by_book[i][4], 'userid': reviews_by_book[i][5], 'bookid': reviews_by_book[i][6],
                'isactive': reviews_by_book[i][7], 'nickname': reviews_by_book[i][11]
            }
            review_list.append(review_element)
        return {'review_list': review_list}


def review_by_review_id(reviewId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"SELECT * FROM review r INNER JOIN userdetails u ON r.userid=u.userid "
                       f"WHERE r.reviewid=%s AND isActive=true", (reviewId, ))
        reviews_by_id = cursor.fetchall()
        return{'reviews_by_id': reviews_by_id}


def review_adding(date, up_date, comment, rating, user_id, book_id):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"INSERT INTO review (createdate, updatedate, comment, rating, userid, bookid, isactive) "
                       f"VALUES(CAST(%s AS date), CAST(%s AS date), "
                       f"%s, %s, %s, %s, true)", (date, up_date, comment, rating, user_id, book_id))
        return {'message': 'Add review success'}


def review_editing(comment, rating, date, reviewId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"UPDATE review SET comment=%s, rating=%s,"
                       f" updatedate= CAST(%s AS date) WHERE reviewid=%s", (comment, rating, date, reviewId))
        return {'message': 'edit review success'}