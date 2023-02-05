from utils import * 
import os
import pyrebase
from firebase_admin import auth
from firebase_init import *

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
                "SELECT status FROM employee_user WHERE email = %s", (email,)
            )
            status = cur.fetchone()
            if status[0] != 'active':
                return return_error("Invalid Credentials")
        return {
                'status': 'success', 
                'token': user['idToken'], 
                'refresh_token': user['refreshToken']
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


def employee_create_account(first_name, last_name, email, password):
    ''' Use Firebase to create a manager account '''
    try:
        uid = generate_uid()
        # create user in firebase
        user = auth.create_user(uid=uid, email=email, password=password)
        # create user in db
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO employee_user (user_id, first_name, last_name, email, status) VALUES (%s, %s, %s, %s, %s)", (uid, first_name, last_name, email, 'active')
            )
            conn.commit()
        # sign in user
        return employee_login(email, password)
    except:
        return return_error("Email already exists")


def employee_forgot_password(email):
    ''' Use Firebase to send a password reset email '''
    pyrebase_auth.send_password_reset_email(email)
    return return_success()


def employee_change_self_email(uid, curr_email, email, password):
    ''' Change user email in Firebase and DB '''
    try:
        # see if credentials are valid
        if not employee_login(curr_email, password)['status'] == 'success':
            return return_error("Invalid Credentials")
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
        if info:
            if (email and info['users'][0]['email'] == email) or not email:
                return return_success({"uid": info['users'][0]['localId'], "email": info['users'][0]['email'], "token": token})
        return return_error()
    except:
        return return_error()


def employee_change_password(uid, email, curr_password, password):
    ''' Use Firebase to change a user's password '''
    try:
        # see if credentials are valid
        if not employee_login(email, curr_password)['status'] == 'success':
            return {'error': 'Invalid Credentials'}
        auth.update_user(uid, password=password)
        # sign out user
        return return_success()
    except:
        return return_error("Failed to change password")


def employee_refresh_token(token, refresh_token):
    ''' Refresh a user's token '''
    info = employee_verify_login(token)
    if info['status'] == 'error':
        return return_error("Invalid Token")
    try:
        user = pyrebase_auth.refresh(refresh_token)
        return {"status": "success", "token": user['idToken'], "refresh_token": user['refreshToken']}
    except:
        return return_error()