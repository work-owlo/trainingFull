from utils import * 
import os
import pyrebase
from firebase_admin import auth
from firebase_init import *
from classes import *
import datetime as dt, time

firebase = pyrebase.initialize_app(firebase_config)
pyrebase_auth = firebase.auth()



def employee_login(email, password):
    ''' Use Firebase to login a user '''
    try:
        user = pyrebase_auth.sign_in_with_email_and_password(email, password)
        # check if employee_user status is active in db
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT status, user_id FROM employee_user WHERE email = %s", (email,)
            )
            status = cur.fetchone()
            if status[0] != 'active':
                return return_error("Invalid Credentials")
        create_session_token_db(access_token=user['idToken'], refresh_token=user['refreshToken'])
        return {
                'status': 'success', 
                'token': user['idToken'], 
                'refresh_token': user['refreshToken'],
                'user_id': status[1]
            }
    except:
        return return_error("Invalid Credentials")


# check if email exists
def employee_email_exists(email):
    ''' Check if email exists in db '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM employee_user WHERE email = %s", (email,)
        )
        user = cur.fetchone()
        if user is None:
            return False
        return True


def check_password(password):
    ''' Check if password is valid '''
    if len(password) < 6:
        return return_error("Password must be at least 6 characters")
    elif len(password) > 20:
        return return_error("Password must be less than 20 characters")
    elif not any(char.isdigit() for char in password):
        return return_error("Password must contain at least one number")
    elif not any(char.isupper() for char in password):
        return return_error("Password must contain at least one uppercase letter")
    elif not any(char.islower() for char in password):
        return return_error("Password must contain at least one lowercase letter")
    return True


def employee_create_account(first_name, last_name, email, password):
    ''' Use Firebase to create a manager account '''
    try:
        uid = generate_uid()
        verify_password = check_password(password)
        if not verify_password:
            return return_error('Password Must Contain At Least One Number, One Uppercase Letter, One Lowercase Letter, and Be Between 6 and 20 Characters')
        # create user in firebase
        user = auth.create_user(uid=uid, email=email, password=password)
        # create user in db
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO employee_user (user_id, first_name, last_name, email, status) VALUES (%s, %s, %s, %s, %s)", (uid, first_name, last_name, email, 'active')
            )
            conn.commit()
        # set uid to team where email is in team table
        update_team_with_uid(email, uid)
        return return_success({"email": email, "password": password})
    except:
        return return_error("Email already exists")


def update_team_with_uid(email, uid):
    ''' Update team table with uid '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE team SET employee_id = %s WHERE email = %s", (uid, email)
        )
        conn.commit()


def employee_forgot_password(email):
    ''' Use Firebase to send a password reset email '''
    try:
        pyrebase_auth.send_password_reset_email(email)
        return return_success()
    except:
        return return_success()


def employee_change_self_email(uid, email, cur_email):
    ''' Change user email in Firebase and DB '''
    try:
        if cur_email == email:
            return return_error('Cannot use same email')
        # see if credentials are valid
        # if not employee_login(curr_email, password)['status'] == 'success':
        #     return return_error("Invalid Credentials")
        # change email in firebase
        auth.update_user(uid, email=email, email_verified=False)
        # change email in db
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE employee_user SET email = %s WHERE user_id = %s", (email, uid))
            conn.commit()
        # sign out user client side
        return return_success()
    except:
        return return_error("Email Already Exists")


def firebase_edit_employee_email(uid, email):
    ''' Change user email in Firebase'''
    try:
        # change email in firebase
        auth.update_user(uid, email=email, email_verified=False)
        return return_success()
    except:
        return return_error("Email Already Exists")


def firebase_edit_employee_password(uid, password):
    ''' Change user password in Firebase'''
    try:
        # change email in firebase
        auth.update_user(uid, password=password, email_verified=False)
        return return_success()
    except:
        return return_error("Error")


def employee_verify_login(token, email=None):
    ''' Verify a user's login token '''
    try:
        info = pyrebase_auth.get_account_info(token)
        # with get_db_connection() as conn:
        #     cur = conn.cursor()
        #     cur.execute("SELECT * FROM auth_token WHERE access_token = %s", (token,))
        #     if not cur.fetchone():
        #         return return_error("Invalid Token")
        if info:
            if (email and info['users'][0]['email'] == email) or not email:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT email, first_name, last_name, status FROM employee_user WHERE user_id = %s", (info['users'][0]['localId'],)
                    )
                    user = cur.fetchone()
                    if user is None:
                        return return_error()
                    user = User(email= user[0], first_name=user[1], last_name=user[2], uid=info['users'][0]['localId'])
                    return return_success({"user": user, "token": token})

        return return_error()
    except:
        return return_error()


def employee_change_password(uid, email, curr_password, password):
    ''' Use Firebase to change a user's password '''
    try:
        # see if credentials are valid
        if not employee_login(email, curr_password)['status'] == 'success':
            return {'error': 'Invalid Credentials'}
        verify_password = check_password(password)
        if verify_password['status'] == 'error':
            return verify_password
        auth.update_user(uid, password=password)
        # sign out user
        return return_success()
    except:
        return return_error("Failed to change password")


def employee_refresh_token(token):
    ''' Refresh a user's token '''
    info = employee_verify_login(token)
    if info['status'] == 'error':
        return return_error("Invalid Token")
    try:
        refresh_token = get_refresh_token_db(token)
        time = get_refresh_time(token)
        if time != False:
            user = pyrebase_auth.refresh(refresh_token)
            update_access_token_db(token, user['idToken'])
            return return_success({'token': user['idToken']})
        return False
    except:
        return return_error()


def create_session_token_db(access_token, refresh_token):
    ''' Create a session token in the db '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        now = dt.datetime.now()
        cur.execute(
            "INSERT INTO auth_token (access_token, refresh_token, updated) VALUES (%s, %s, %s)", (access_token, refresh_token, now)
        )
        conn.commit()
    return return_success()


def get_refresh_time(cur_token):
    '''Get if refreshed in last 30 minutes'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        # get updated time from db
        cur.execute(
            "SELECT updated FROM auth_token WHERE access_token = %s", (cur_token,)
        )
        updated = cur.fetchone()
        if updated is None:
            return False
        updated = updated[0]
        # if 30 minutes or less since update return true
        if (dt.datetime.now() - updated).total_seconds() > 60:
            return True
        return False


def update_access_token_db(cur_token, new_token):
    ''' Update the access token in the db '''
    with get_db_connection() as conn:
        now = dt.datetime.now()
        cur = conn.cursor()
        cur.execute(
            "UPDATE auth_token SET access_token = %s, updated = %s WHERE access_token = %s", (new_token, now, cur_token)
        )
        conn.commit()
    return True


def delete_session_token_db(access_token):
    ''' Delete a session token in the db '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM auth_token WHERE access_token = %s", (access_token,)
        )
        conn.commit()


def get_refresh_token_db(access_token):
    ''' Get a refresh token from the db '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT refresh_token FROM auth_token WHERE access_token = %s", (access_token,)
        )
        refresh_token = cur.fetchone()
        if refresh_token is None:
            return return_error()
    return refresh_token[0]


