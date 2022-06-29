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
from controllers.wishlist_item import all_wishlist_item, wishlist_item_by_id, wishlist_item_add
from controllers.user_profile import user_profile_all, profile_by_id,profile_edit
from controllers.review import all_reviews, review_by_id, review_by_review_id, review_adding,review_editing
from controllers.reports import all_reports, report_by_id, report_by_review_id, report_adding, report_keeping,report_deletion
from controllers.libraries import all_libraries,all_library_by_id, library_item_deletion,library_item_adding


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
    response = user_profile_all()
    return jsonify(response)


@app.route('/user-profile/<string:userId>', methods=['GET'])
@cross_origin()
def get_profile_by_id(userId):
    response = profile_by_id(userId)
    return jsonify(response)

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
        response=profile_edit(first_name, last_name, nickname, userid)
        return jsonify(response)


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
    response = all_reviews()
    return jsonify(response)


@app.route('/reviews/<string:bookId>', methods=['GET'])
@cross_origin()
def get_reviews_by_book_id(bookId):
    response = review_by_id(bookId)
    return jsonify(response)


@app.route('/reviews/<string:reviewId>', methods=['GET'])
@cross_origin()
def get_review_by_review_id(reviewId):
    response = review_by_review_id(reviewId)
    return jsonify(response)


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
    user_id=request.json['userId']
    book_id=request.json['bookId']
    if date is None or comment is None or rating is None or user_id is None or book_id is None:
        return {'message': 'Add Review Fail'}
    else:
        response = review_adding(date, date, comment, rating, user_id, book_id)
        return jsonify(response)


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
        response = review_editing(comment, rating, date, reviewId)
        return jsonify(response)


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
    response = all_reports()
    return jsonify(response)


@app.route('/reports/<string:reportId>', methods=['GET'])
@cross_origin()
def get_report_by_report_id(reportId):
    response = report_by_id(reportId)
    return jsonify(response)


@app.route('/report/<string:reviewId>', methods=['GET'])
@cross_origin()
def get_report_by_review_id(reviewId):
    response = report_by_review_id(reviewId)
    return jsonify(response)

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
        response = report_adding(userId, reviewId, date, date, comment, reporttypeId)
        return jsonify(response)


@app.route('/reports/delete', methods=['POST'])
@cross_origin()
def delete_report():
    report_id = request.json['reportId']
    review_id = request.json['reviewId']
    if review_id is None or report_id is None:
        return {'message':'Delete Report failed'}
    else:
        response = report_deletion(report_id, review_id)
        return jsonify(response)


@app.route('/reports/keep', methods=['POST'])
@cross_origin()
def keep_report():
    report_id = request.json['reportId']
    if report_id is None:
        return{'message': 'Keep report failed'}
    else:
        response = report_keeping(report_id)
        return jsonify(response)



@app.route('/library-item', methods=['GET'])
@cross_origin()
def get_all_libraries():
    response=all_libraries()
    return jsonify(response)


@app.route('/library-item/<string:userid>', methods=['GET'])
@cross_origin()
def get_all_library_by_user_id(userid):
    response = all_library_by_id(userid)
    return jsonify(response)


@app.route('/library-item/delete/<string:id>', methods=['DELETE'])
@cross_origin()
def delete_library_item_by_id(id):
    response=library_item_deletion(id)
    return jsonify(response)


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
    response=library_item_adding(user_id, book_title, book_cover, book_id, author)
    return jsonify(response)


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


@app.route('/auth/login', methods=['POST'])
@cross_origin()
def login():
    email = request.json['email']
    password = request.json['password'].encode('utf8')

    with CursorFromConnectionFromPool() as cursor:
        if cursor:
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
