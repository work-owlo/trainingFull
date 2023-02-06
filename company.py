from utils import *
from classes import *
from managers import *


def get_company(company_id):
    '''Fetch company related information '''
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM company WHERE company_id = %s", (company_id,))
        company = cur.fetchone()
        company.pop('id')
        return return_success(company)

def update_company_name(uid, company_name, company_id):
    ''' Update company name '''
    if not get_curr_permissions(uid)['edit_company']:
        return return_error("User does not have permission to edit company")
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE company SET company_name = %s WHERE company_id = %s", (company_name, company_id))
        conn.commit()
    return return_success()


def add_company(uid, name, company_description):
    if manager_get_company_id(uid) != None:
        return return_error("User already has a company")
    company_id = generate_uid()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO company (company_id, company_name, company_description, status) VALUES (%s, %s, %s, %s)", (company_id, name, company_description, "active"))
        conn.commit()
    assign_company_id_to_manager(uid, company_id)
    return return_success()


def assign_company_id_to_manager(uid, company_id):
    ''' Assign company_id to manager creating company '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE manager_user SET company_id = %s WHERE user_id = %s", (company_id, uid))
        conn.commit()


# def edit_company(uid, company_id, info: Edit_company):
#     ''' Edit company information'''
#     if not get_curr_permissions(uid)['edit_company']:
#         return return_error("User does not have permission to edit company")
#     try:
#         with get_db_connection() as conn:
#             cur = conn.cursor()
#             cur.execute(
#                 "UPDATE company SET company_name = %s, address_street = %s, address_city = %s, address_state = %s, address_zip = %s, logo_link = %s, website = %s, company_description = %s WHERE company_id = %s", (info.name, info.address_street, info.address_city, info.address_state, info.address_zip, info.logo_link, info.website, info.company_description, company_id))
#             conn.commit()
#         return return_success()
#     except:
#         return_error()


def delete_company(uid, company_id):
    ''' Delete company by setting status to terminated'''
    if not get_curr_permissions(uid)['edit_company']:
        return return_error("User does not have permission to edit company")

    try:
        # delete all managers from company who are not uid
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM manager_user WHERE company_id = %s AND user_id != %s", (company_id, uid))
            conn.commit()

        # set status of all roles to inactive
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE job_roles SET status = %s WHERE company_id = %s", ("terminated", company_id))
            conn.commit()

        # set status of all shifts to inactive
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE shifts SET status = %s WHERE company_id = %s", ("terminated", company_id))
            conn.commit()

        # set status of all shifts to inactive
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE company SET status = %s WHERE company_id = %s", ("terminated", company_id))
            conn.commit()

        # set company_id to null for manager
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE manager_user SET company_id = %s WHERE user_id = %s", (None, uid))
            conn.commit()

        return return_success("Company deleted")
    except:
        return_error()