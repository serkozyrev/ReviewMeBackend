from flask import Flask, request, jsonify
import jwt
import os
from datetime import datetime, timedelta
import requests
import smtplib
from random import *
from dotenv import load_dotenv
from database import Database
from database import CursorFromConnectionFromPool
from flask_cors import CORS, cross_origin
import bcrypt
from wishlist_item import all_wishlist_item, wishlist_item_by_id, wishlist_item_add

load_dotenv()
my_email = os.getenv('email')
gmail_password = os.getenv('gmail_password')
DB_PWD = os.getenv('DB_PWD')
DB_USER = os.getenv('DB_USER')
DB_HOST = os.getenv('DB_HOST')
jwtsecret = os.getenv('jwtsecret')
API_KEY = os.getenv('API_KEY')
DB = os.getenv('DB')
app = Flask(__name__)
CORS(app)
Database.initialize(user=f'{DB_USER}',
                                            password=f'{DB_PWD}',
                                            host=f'{DB_HOST}',
                                            port=5432,
                                            database=f'{DB}')

@app.route('/reset-pass', methods=['PUT'])
@cross_origin()
def reset_password():
    token_info = request.json['tokenInfo']
    password = request.json['password'].encode('utf8')
    current_pass = request.json['currentPass'].encode('utf-8')
    decoded_token = jwt.decode(token_info, jwtsecret, algorithms=["HS256"])

    user_id=list(decoded_token.items())[2][1]
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"select password from usr where userid=%s", (user_id, ))
        prev_pass = cursor.fetchone()
    hashed_prev_pass=prev_pass[0].encode('utf-8')
    valid_pass = bcrypt.checkpw(current_pass, hashed_prev_pass)
    if not valid_pass:
        return jsonify("Current Password doesn't match our record")
    else:
        salt = bcrypt.gensalt(10)
        hashed_new_pass = bcrypt.hashpw(password, salt).decode('utf-8')
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"update usr set password=%s where userid=%s",(hashed_new_pass, user_id))
            return jsonify('Password successfully updated')


@app.route('/wishlist-item', methods=['GET'])
@cross_origin()
def get_all_wishlist():
    response=all_wishlist_item()
    return jsonify(response)


@app.route('/wishlist-item/<string:userId>', methods=['GET'])
@cross_origin()
def get_wishlist_by_userid(userId):
    response = wishlist_item_by_id(userId)
    return jsonify(response)


@app.route('/wishlist-item/add', methods=['POST'])
@cross_origin()
def add_wishlist():
    book_title = request.json['bookTitle'].replace("'", "''")
    user_id = request.json['userId']
    book_cover = request.json['bookcover']
    book_id = request.json['bookId']
    author = request.json['author'].replace("'", "''")
    response = wishlist_item_add(user_id, book_title, book_cover, book_id, author)
    return jsonify(response)


@app.route('/wishlist-item/delete/<string:id>', methods=['DELETE'])
@cross_origin()
def delete_wishlist_by_id(id):
    try:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f'delete from wishlist where wishlistid in (%s)', (id, ))
            return {'message': 'Delete wishlist item successful'}
    except:
        return{'message': 'Deleting wishlist item failed'}


@app.route('/user-profile', methods=['GET'])
@cross_origin()
def get_all_profiles():
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute('SELECT * FROM userdetails ud INNER JOIN usr u ON ud.userid=u.userid AND isActive=true')
        user_profile = cursor.fetchall()
        return {'user_profile':user_profile}


@app.route('/user-profile/<string:userId>', methods=['GET'])
@cross_origin()
def get_profile_by_id(userId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"SELECT * FROM userdetails ud INNER JOIN usr u ON ud.userid=u.userid WHERE ud.userid=%s AND isActive=true", (userId, ))
        user_profile_byid = cursor.fetchone()
        year = user_profile_byid[4].strftime('%Y')
        month = user_profile_byid[4].strftime('%m')
        day = user_profile_byid[4].strftime('%d')
        date = f'{year}-{month}-{day}'
        profile_list = []
        profile_element={
            'firstname':user_profile_byid[1], 'lastname':user_profile_byid[2],
            'nickname': user_profile_byid[3], 'genderid': user_profile_byid[5],
            'dateofbirth':date, 'email': user_profile_byid[8]
        }
        profile_list.append(profile_element)
        return {'profile': profile_list}


@app.route('/user-profile/edit', methods=['PUT'])
@cross_origin()
def edit_profile():
    first_name=request.json['firstname']
    last_name=request.json['lastname']
    nickname=request.json['nickname']
    userid=request.json['userId']
    if first_name is None or last_name is None or nickname is None or userid is None:
        return {'message': 'Edit profile failed - A field is missing'}
    else:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f'UPDATE userdetails SET firstname=%s,lastname=%s,nickname=%s WHERE userid=%s',
                           (first_name, last_name, nickname, userid))
            return {'message':'Edit profile successful'}


@app.route('/user-profile/delete', methods=['PUT'])
@cross_origin()
def delete_account_profile():
    userid=request.json['userId']
    if userid is None:
        return {'message': 'Account deletion failed'}
    else:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f'update usr set isactive=false where userid=%s', (userid,))
            return {'message':'Account deletion successful'}


@app.route('/reviews', methods=['GET'])
@cross_origin()
def get_all_reviews():
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute('SELECT * FROM review INNER JOIN usr ON review.userid=usr.userid')
        reviews_data = cursor.fetchall()
        return {'reviews':reviews_data}


@app.route('/reviews/<string:bookId>', methods=['GET'])
@cross_origin()
def get_reviews_by_book_id(bookId):
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


@app.route('/reviews/<string:reviewId>', methods=['GET'])
@cross_origin()
def get_review_by_review_id(reviewId):
    review_id=request.json['']
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"SELECT * FROM review r INNER JOIN userdetails u ON r.userid=u.userid "
                       f"WHERE r.reviewid=%s AND isActive=true", (reviewId, ))
        reviews_by_id = cursor.fetchall()
        return{'reviews_by_id': reviews_by_id}


@app.route('/reviews/add', methods=['POST'])
@cross_origin()
def add_review():
    new_date=datetime.now()
    year=new_date.strftime('%Y')
    month=new_date.strftime('%m')
    day=new_date.strftime('%d')
    date = f'{year}-{month}-{day}'
    comment = request.json['comment']
    rating = request.json['rating']
    userId=request.json['userId']
    bookId=request.json['bookId']
    if date is None or comment is None or rating is None or userId is None or bookId is None:
        return {'message': 'Add Review Fail'}
    else:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"INSERT INTO review (createdate, updatedate, comment, rating, userid, bookid, isactive) "
                           f"VALUES(CAST(%s AS date), CAST(%s AS date), "
                           f"%s, %s, %s, %s, true)", (date, date, comment, rating, userId, bookId))
            return {'message': 'Add review success'}


@app.route('/reviews/edit', methods=['PUT'])
@cross_origin()
def edit_review():
    new_date = datetime.now()
    year = new_date.strftime('%Y')
    month = new_date.strftime('%m')
    day = new_date.strftime('%d')
    date = f'{year}-{month}-{day}'
    comment = request.json['comment']
    rating = request.json['rating']
    reviewId = request.json['reviewId']
    if date is None or comment is None or rating is None or reviewId is None:
        return {'message': 'Edit Review Fail'}
    else:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"UPDATE review SET comment=%s, rating=%s,"
                           f" updatedate= CAST(%s AS date) WHERE reviewid=%s", (comment, rating, date, reviewId))
            return {'message': 'edit review success'}


@app.route('/reviews/delete', methods=['PUT'])
@cross_origin()
def delete_review():
    reviewId = request.json['reviewId']
    if reviewId is None:
        return {'message': 'Delete Review Fail - at least one field missing'}
    else:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"UPDATE review SET isActive=false WHERE reviewid=%s", (reviewId, ))
            return {'message':' Delete review success'}


@app.route('/reports', methods=['GET'])
@cross_origin()
def get_all_reports():
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute("SELECT r.reportid, r.reviewid, r.reporttypeid, r.comment, rw.comment,"
                       " rt.reporttype, rd.firstname ||' '|| rd.lastname,"
                       " rwd.firstname ||' '|| rwd.lastname,"
                       " rd.userid, "
                       " rwd.userid"
                       " FROM report r "
                       " INNER JOIN reporttype rt ON r.reporttypeid=rt.reporttypeid "
                       " INNER JOIN userdetails rd ON rd.userid=r.userid "
                       " INNER JOIN review rw ON rw.reviewid=r.reviewid "
                       " LEFT JOIN userdetails rwd ON rwd.userid=rw.userid "
                       " WHERE r.isactive=true")
        report_data = cursor.fetchall()
        report_list = []
        for i in range(len(report_data)):
            review_el={
                'reportid':report_data[i][0], 'reviewid':report_data[i][1], 'reportComment': report_data[i][3],
                'reviewComment':report_data[i][4], 'reporterName':report_data[i][6], 'reviewerName': report_data[i][7]
            }
            report_list.append(review_el)
        return {'reports': report_list}


@app.route('/reports/<string:reportId>', methods=['GET'])
@cross_origin()
def get_report_by_report_id(reportId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"select * from report r inner join reporttype rt on r.reporttypeid=rt.reporttypeid where"
                       f" r.reportid=%s and isActive=true", (reportId, ))
        report_data_by_id = cursor.fetchall()
        return {'reportsById': report_data_by_id}


@app.route('/report/<string:reviewId>', methods=['GET'])
@cross_origin()
def get_report_by_review_id(reviewId):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f"SELECT * FROM report WHERE reviewid=%s AND isActive=true", (reviewId, ))
        report_by_review_id = cursor.fetchall()
        return{'report_by_review': report_by_review_id}


@app.route('/reports/add', methods=['POST'])
@cross_origin()
def add_report():
    new_date = datetime.now()
    year = new_date.strftime('%Y')
    month = new_date.strftime('%m')
    day = new_date.strftime('%d')
    date = f'{year}-{month}-{day}'
    userId = request.json['userId']
    reviewId = request.json['reviewId']
    comment = request.json['comment']
    reporttypeId = request.json['reporttypeId']
    if date is None or comment is None or reporttypeId is None or userId is None or reviewId is None:
        return {'message': 'Add Report Fail'}
    else:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"INSERT INTO report (userid, reviewid, createdate, updatedate, comment, reporttypeid, isactive)"
                           f" VALUES(%s, %s, CAST(%s AS date),"
                           f" CAST(%s AS date), %s, %s, true)", (userId, reviewId, date, date, comment, reporttypeId))
            return {'message': "Add report successful"}


@app.route('/reports/delete', methods=['POST'])
@cross_origin()
def delete_report():
    report_id = request.json['reportId']
    review_id = request.json['reviewId']
    if review_id is None or report_id is None:
        return {'message':'Delete Report failed'}
    else:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"WITH rp AS (UPDATE report SET isactive = false WHERE reportid=%s RETURNING *)"
                           f" UPDATE review rw"
                           f" SET isactive = false"
                           f" FROM rp"
                           f" WHERE rw.reviewid=%s", (report_id, review_id))
            return{'message':'Delete Report Successful'}


@app.route('/reports/keep', methods=['POST'])
@cross_origin()
def keep_report():
    report_id = request.json['reportId']
    if report_id is None:
        return{'message': 'Keep report failed'}
    else:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(f"UPDATE report SET isactive = false WHERE reportid = %s", (report_id, ))
            return {'message': 'Keep report successful'}


@app.route('/library-item', methods=['GET'])
@cross_origin()
def get_all_libraries():
    with CursorFromConnectionFromPool() as cursor:
        if cursor:
            print("Connection pool created successfully")
        cursor.execute('select * from libraryitem')
        user_data = cursor.fetchall()
        return {'libraries':user_data}


@app.route('/library-item/<string:userid>', methods=['GET'])
@cross_origin()
def get_all_library_by_user_id(userid):
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


@app.route('/library-item/delete/<string:id>', methods=['DELETE'])
@cross_origin()
def delete_library_item_by_id(id):
    id_list=id.split(',')
    condition = f'where libraryitemid in ({id_list[0]}'
    for ids in id_list:
        condition += f',{ids}'
    condition += ')'
    with CursorFromConnectionFromPool() as cursor:
        if cursor:
            print("Connection pool created successfully")
        cursor.execute(f'delete from libraryitem {condition}')
        return jsonify({"message": "Delete library item success"})


@app.route('/library-item/add', methods=['POST'])
@cross_origin()
def add_library_item():
    book_title = request.json['bookTitle'].replace("'", "''")
    user_id = request.json['userId']
    book_cover = request.json['bookcover']
    book_id = request.json['bookId']
    author = request.json['author'].replace("'", "''")
    if author is None:
        author = "No Author"
    with CursorFromConnectionFromPool() as cursor:
        if cursor:
            print("Connection pool created successfully")
        cursor.execute(f"INSERT INTO libraryitem(userid, booktitle, bookcover, bookid, author)  "
                       f"VALUES(%s, %s, %s, %s, %s)",
                       (user_id, book_title, book_cover, book_id, author))
        return {'message': 'Add Library Item Successful'}


@app.route('/home/<string:name>', methods=['GET'])
@cross_origin()
def get_book_by_search(name):
    global API_KEY
    response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={name}&key={API_KEY}&maxResults=40")
    return response.json()


@app.route('/home/', methods=['GET'])
@cross_origin()
def empty_home():
    return {"message":"No items selected", 'books': {'items': []}}


@app.route('/book-details/<string:id>', methods=['GET'])
@cross_origin()
def get_book_by_id(id):
    global API_KEY
    response = requests.get(f"https://www.googleapis.com/books/v1/volumes/{id}?key={API_KEY}")
    return response.json()


@app.route("/home/<string:name>&<string:max_results>", methods=["GET"])
@cross_origin()
def get_all_books(name, max_results):
    global API_KEY
    response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={name}"
                            f"&key={API_KEY}&maxResults={max_results}")
    return response.json()


@app.route('/auth/login', methods=['GET', 'POST'])
@cross_origin()
def login():
    email = request.json['email']
    password = request.json['password'].encode('utf8')

    with CursorFromConnectionFromPool() as cursor:
        if cursor:
            print("Connection pool created successfully")
        cursor.execute('select * from usr where email = %s', (email, ))
        user_data = cursor.fetchone()
        if user_data is None:
            return "User doesn't exist! Please enter correct information"
        else:
            user_id = user_data[0]
            password1 = user_data[2].encode('utf8')
            valid_password = bcrypt.checkpw(password, password1)
            with CursorFromConnectionFromPool() as cursor_details:
                cursor_details.execute(f"select * from userdetails where userid = %s", (user_id, ))
                user_details = cursor_details.fetchone()
        dt = datetime.now() + timedelta(hours=1)
        payload={
            'exp':datetime.now() + timedelta(days=1),
            'iat': datetime.now(),
            'id': user_id
        }
        access_token = jwt.encode(payload, jwtsecret, algorithm="HS256")

        return {'users': user_data, 'password': valid_password, 'details': user_details, 'tokenInfo': access_token}

@app.route('/auth/forgotpass', methods=['POST'])
@cross_origin()
def forgot_password():
    forgot_password_email= request.json['email']
    print(forgot_password_email)
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f'select password from usr where email = %s', (forgot_password_email, ))
        email=cursor.fetchone()
    if email is None:
        return jsonify("Please provide email that you use to login to your account!")
    else:
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                   'u',
                   'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
                   'P',
                   'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

        password_letters = [choice(letters) for _ in range(randint(8, 10))]
        password_symbols = [choice(symbols) for _ in range(randint(2, 4))]
        password_numbers = [choice(numbers) for _ in range(randint(2, 4))]
        password_list = password_letters + password_numbers + password_symbols
        shuffle(password_list)


        password = "".join(password_list).encode('utf8')
        pass_decoded=password.decode('utf8')
        print(pass_decoded)
        salt = bcrypt.gensalt(10)
        hashed_pass = bcrypt.hashpw(password, salt).decode('utf-8')
        print(hashed_pass)
        with CursorFromConnectionFromPool() as cursor_update:
            cursor_update.execute(f"UPDATE usr SET password=%s "
                                f" WHERE email=%s", (hashed_pass, forgot_password_email))
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=my_email, password=gmail_password)
            connection.sendmail(
                from_addr=my_email,
                to_addrs=forgot_password_email,
                msg=f"Subject:Temporary password for account with email {forgot_password_email} on website 'ReviewMe'"
                    f"\n\n Hello, \n Here is your generated password to login to your account: \n {pass_decoded}"
            )
        return jsonify('Email with new password was sent to you')
@app.route('/auth/signup', methods=['POST'])
@cross_origin()
def sign():
    first_name = request.json['firstName']
    last_name = request.json['lastName']
    email = request.json['email']
    password = request.json['password'].encode('utf8')
    confirm_password=request.json['confirmPassword']
    gender = request.json['gender']
    nick_name=request.json['nickName']
    dob = request.json['dob']
    user_type = 2

    if gender == 'Male':
        gender_type = 1
    elif gender == 'Female':
        gender_type = 2
    elif gender == 'Prefer not to say':
        gender_type = 3

    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f'select userid from usr where email=%s', (email, ))
        user = cursor.fetchone()
        cursor.execute(f'select nickname from userdetails where nickname=%s', (nick_name, ))
        nickname = cursor.fetchone()

    if user:
        return {'message': 'User already exist'}
    elif nickname:
        return {'message': 'Entered nickname already taken. Please enter another'}
    elif nickname is None or user is None:
        salt = bcrypt.gensalt(10)
        hashed = bcrypt.hashpw(password, salt).decode('utf-8')

        with CursorFromConnectionFromPool() as cursor_user:
            cursor_user.execute(f'insert into usr (userid, email, password, usertypeid, isactive)'
                                f' values((select max(userid)+1 from usr),%s, %s, %s, true) returning *',
                                (email, hashed, user_type))
        with CursorFromConnectionFromPool() as cursor_new_details:
            cursor_new_details.execute(f"insert into userdetails(userdetailid, firstname, lastname, nickname, dateofbirth, "
                                       f"genderid, userid) values((select max(userdetailid)+1 from userdetails),"
                                       f" %s, %s, %s,%s,%s, (select max(userid) from usr))",
                                       (first_name, last_name, nick_name, dob, gender_type))
        return {'message':'User successfully created'}


if __name__ == "__main__":
    app.run(debug=True)
