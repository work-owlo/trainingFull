from utils import * 
import os
from manager_auth import *

def get_managers(uid, company_id):
    ''' Get all managers within a company '''
    if not get_curr_permissions(uid)['read_managers']:
        return return_error("User does not have permission to view managers")
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, first_name, last_name, email, status, created, updated FROM manager_user WHERE company_id = %s", (company_id,))
        managers = cur.fetchall()
        return return_success(managers)


def manager_get_company_id(uid):
    ''' Get the company id of a manager '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT company_id FROM manager_user WHERE user_id = %s", (uid,)
        )
        company_id = cur.fetchone()[0]
    return company_id


def get_manager(uid, manager_id):
    ''' Get comprehensive account details for a given manager'''
    if not get_curr_permissions(uid)['read_managers']:
        return return_error("User does not have permission to view managers")
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, first_name, last_name, email, status, created, updated FROM manager_user WHERE user_id = %s", (manager_id,))
        manager = cur.fetchone()
        return return_success(manager)


def add_manager(uid, company_id, email, password, first_name, last_name):
    ''' Add a manager to a company'''
    if not get_curr_permissions(uid)['add_managers']:
        return return_error("User does not have permission to add managers")
    new_uid = generate_uid()
    # add to firebase and db
    manager = manager_create_account(uid, new_uid, first_name, last_name, email, password, company_id)
    return manager


def edit_manager_password(uid, manager_id, password):
    '''Edit manager account information'''
    if not get_curr_permissions(uid)['edit_managers']:
        return return_error("User does not have permission to edit managers")
    try:
        firebase_edit_manager_password(manager_id, password)
        return return_success("Password Updated")
    except:
        return_error()


def edit_manager_email(uid, manager_id, email):
    '''Edit manager account information'''
    if not get_curr_permissions(uid)['edit_managers']:
        return return_error("User does not have permission to edit managers")
    try:
        firebase_edit_manager_email(manager_id, email)
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE manager_user SET email = %s WHERE user_id = %s", (email, manager_id))
            conn.commit()
        return return_success("Email updated")
    except:
        return_error()


def edit_manager_name(uid, manager_id, first_name, last_name):
    '''Edit manager account information'''
    if not get_curr_permissions(uid)['edit_managers']:
        return return_error("User does not have permission to edit managers")
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE manager_user SET first_name = %s, last_name = %s WHERE user_id = %s", (first_name, last_name, manager_id))
            conn.commit()
        return return_success()
    except:
        return_error()


def get_manager_permissions(uid, manager_id):
    ''' Get manager permissions '''
    if not get_curr_permissions(uid)['read_managers']:
        return return_error("User does not have permission to get maanger permissions")
    return get_curr_permissions(manager_id)


# edit manager permissions
def edit_manager_permissions(uid, edit_uid, permissions_dict):
    permissions = get_curr_permissions(uid)
    for key in permissions_dict:
        if not permissions[key] and permissions_dict[key]:
            return return_error("You cannot grant a permission you do not have")
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE manager_permissions SET add_managers = %s, edit_managers = %s, delete_managers = %s, read_managers = %s, add_roles = %s, edit_roles = %s, delete_roles = %s, add_shifts = %s, edit_shifts = %s, delete_shifts = %s WHERE user_id = %s", (permissions_dict['add_managers'], permissions_dict['edit_managers'], permissions_dict['delete_managers'], permissions_dict['read_managers'], permissions_dict['add_roles'], permissions_dict['edit_roles'], permissions_dict['delete_roles'], permissions_dict['add_shifts'], permissions_dict['edit_shifts'], permissions_dict['delete_shifts'], edit_uid)) 
    return return_success()


def delete_manager(uid, manager_id):
    ''' Delete by setting status to terminated '''
    if not get_curr_permissions(uid)['delete_managers']:
        return return_error("User does not have permission to delete managers")
    with get_db_connection() as conn:
        if get_manager_status(manager_id) == 'terminated':
            return return_error("You do not have permission view terminated this manager")
        cur = conn.cursor()
        cur.execute(
            "UPDATE manager_user SET status = 'terminated' WHERE user_id = %s", (manager_id,))
        conn.commit()
        return return_success()


def get_manager_status(uid):
    '''Get the employment status of a given manager'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM manager_user WHERE user_id = %s", (uid,))
        status = cur.fetchone()[0]
        return status


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


def copy_permissions_node(uid, new_uid):
    ''' Create a duplicate permissions node '''
    permissions = get_curr_permissions(uid)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO manager_permissions (user_id, add_managers, edit_managers, delete_managers, read_managers, add_roles, edit_roles, delete_roles, add_shifts, edit_shifts, delete_shifts) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",  (new_uid, permissions['add_managers'], permissions['edit_managers'], permissions['delete_managers'], permissions['read_managers'], permissions['add_roles'], permissions['edit_roles'], permissions['delete_roles'], permissions['add_shifts'], permissions['edit_shifts'], permissions['delete_shifts'])
        )
        conn.commit()
        return return_success()
        

def get_available_qualifications(role_id):
    # get all qualifications except ones that are already included
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT qualifications_id, qual_title, qual_description FROM qualifications WHERE qual_id not in (SELECT qualifications_id FROM job_roles WHERE role_id = %s", (role_id,)
        )

    conn.commit()
    return return_success()