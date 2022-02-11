from database import Database
from database import CursorFromConnectionFromPool

def user_profile_all():
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute('SELECT * FROM userdetails ud INNER JOIN usr u ON ud.userid=u.userid AND isActive=true')
        user_profile = cursor.fetchall()
        return {'user_profile': user_profile}

def profile_by_id(userId):
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

def profile_edit(first_name, last_name, nickname, userid):
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(f'UPDATE userdetails SET firstname=%s,lastname=%s,nickname=%s WHERE userid=%s',
                       (first_name, last_name, nickname, userid))
        return {'message': 'Edit profile successful'}
