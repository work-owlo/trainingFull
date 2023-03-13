from utils import * 
import os
import pyrebase
from firebase_admin import auth
from firebase_init import *
# from managers import *
# from firebase_init import *
from employee_auth import *
from classes import *
firebase = pyrebase.initialize_app(firebase_config)
pyrebase_auth = firebase.auth()



def manager_login(email, password):
    ''' Use Firebase to login a user '''
    email = email.lower()
    email = email.strip()
    try:
        user = pyrebase_auth.sign_in_with_email_and_password(email, password)
        # check if manager_user status is active in db
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT status FROM manager_user WHERE email = %s", (email,)
            )
            status = cur.fetchone()
            if status[0] != 'active':
                return return_error("Invalid Credentials")
        create_session_token_db(access_token=user['idToken'], refresh_token=user['refreshToken'])
        return {
                'status': 'success', 
                'token': user['idToken'], 
                'refresh_token': user['refreshToken']
            }
    except:
        return return_error("Invalid Credentials")


def manager_create_admin_account(first_name, last_name, email, password, uid=None, add_to_firebase=True):
    ''' Use Firebase to create a manager account '''
    try:        
        verify_password = check_password(password)
        if not verify_password:
            return return_error("Password must be at least 6 characters, contain at least one number, and contain at least one special character")
        uid = generate_uid() if uid is None else uid
        # create user in firebase
        user = auth.create_user(uid=uid, email=email, password=password) if add_to_firebase else None
        # create user in db
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO manager_user (user_id, first_name, last_name, email, status) VALUES (%s, %s, %s, %s, %s)", (uid, first_name, last_name, email, 'active')
            )
            conn.commit()
        # add permissions
        add_admin_permissions(uid)
        # sign in user
        return manager_login(email, password)
    except:
        return return_error("Email already exists")


def manager_email_exists(email):
    ''' Check if email exists in db '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM manager_user WHERE email = %s", (email,)
        )
        user = cur.fetchone()
        if user is None:
            return False
        return True


def manager_create_account(uid, manager_uid, first_name, last_name, email, password, company_id):
    ''' Use Firebase to create a manager account in the case that the company already exists'''
    email = email.lower()
    email = email.strip()
    try:
        # create user in firebase
        if manager_email_exists(email):
            return return_error("Email already exists")
        verify_password = check_password(password)
        if not verify_password:
            return return_error("Password must be at least 6 characters, contain at least one number, and contain at least one special character")
        user = auth.create_user(uid=manager_uid, email=email, password=password)
        # create user in db
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO manager_user (user_id, first_name, last_name, email, company_id, status) VALUES (%s, %s, %s, %s, %s, %s)", (manager_uid, first_name, last_name, email, company_id, 'active')
            )
            conn.commit()
        # add permissions
        copy_permissions_node(uid, manager_uid)
        return return_success()
    except:
        return return_error("An Error Occured")


def copy_permissions_node(uid, manager_uid):
    ''' Copy permissions node from company to new manager '''
    with get_db_connection() as conn:
        permissions = get_curr_permissions(uid)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO manager_permissions (user_id, add_managers, edit_managers, delete_managers, read_managers, add_roles, edit_roles, delete_roles, add_shifts, edit_shifts, delete_shifts, edit_company, delete_company) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (manager_uid, permissions['add_managers'], permissions['edit_managers'], permissions['delete_managers'], permissions['read_managers'], permissions['add_roles'], permissions['edit_roles'], permissions['delete_roles'], permissions['add_shifts'], permissions['edit_shifts'], permissions['delete_shifts'], permissions['edit_company'], permissions['delete_company'])
        )
        conn.commit()


def get_curr_permissions(uid):
    ''' Get permissions of curr user'''
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM manager_permissions WHERE user_id = %s", (uid,))
        permissions = cur.fetchone()
        permissions.pop('user_id')
        permissions.pop('id')
        permissions.pop('created')
        permissions.pop('updated')
        return permissions


def add_admin_permissions(uid):
    ''' Create a permissions node with complete access '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO manager_permissions (user_id, add_managers, edit_managers, delete_managers, read_managers, add_roles, edit_roles, delete_roles, add_shifts, edit_shifts, delete_shifts, edit_company, delete_company) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (uid, True, True, True, True, True, True, True, True, True, True, True, True)
        )
        conn.commit()


def manager_forgot_password(email):
    ''' Use Firebase to send a password reset email '''
    try:
        pyrebase_auth.send_password_reset_email(email)
        return return_success()
    except:
        return return_success()


def manager_change_self_email(uid, curr_email, email):
    ''' Change user email in Firebase and DB '''
    email = email.lower()
    email = email.strip()
    try:
    # see if credentials are valid
        if email == curr_email:
            return return_error("Cannot use same email")
        # if not manager_login(curr_email, password)['status'] == 'success':
        #     return return_error("Invalid Credentials")
        # change email in firebase
        auth.update_user(uid, email=email, email_verified=False)
        # change email in db
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE manager_user SET email = %s WHERE user_id = %s", (email, uid))
            conn.commit()
        # sign out user client side
        return return_success()
    except:
        return return_error("Email Already Exists")


def firebase_edit_manager_email(uid, email):
    ''' Change user email in Firebase'''
    try:
        # change email in firebase
        auth.update_user(uid, email=email, email_verified=False)
        return return_success()
    except:
        return return_error("Email Already Exists")


def firebase_edit_manager_password(uid, password):
    ''' Change user password in Firebase'''
    try:
        # change email in firebase
        auth.update_user(uid, password=password, email_verified=False)
        return return_success()
    except:
        return return_error("Error")


def manager_verify_login(token, email=None):
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
                    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
                    cur.execute(
                        "SELECT * FROM manager_user WHERE user_id = %s", (info['users'][0]['localId'],))
                    user = cur.fetchone()
                    user = Manager(company_id=user['company_id'], first_name=user['first_name'], last_name=user['last_name'], uid=user['user_id'], email=user['email'])
                    if user:
                        return return_success({'user': user, 'token': token})
                    else:
                        return return_error("User not found")
        return return_error()
    except:
        return return_error()


def manager_change_password(uid, email, curr_password, password):
    ''' Use Firebase to change a user's password '''
    try:
        # see if credentials are valid
        if not manager_login(email, curr_password)['status'] == 'success':
            return {'error': 'Invalid Credentials'}
        verify_password = check_password(password)
        if verify_password['status'] == 'error':
            return verify_password
        auth.update_user(uid, password=password)
        # sign out user
        return return_success()
    except:
        return return_error("Failed to change password")


def manager_refresh_token(token):
    ''' Refresh a user's token '''
    info = manager_verify_login(token)
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