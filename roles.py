import sqlite3

from utils import *
from classes import *



def assign_employee_role(company_id, id_input, first_name, last_name, email, role_id, employment_type):
    with get_db_connection() as conn:
        ''' Assign role to employee '''
        cur = conn.cursor()
        new_id = generate_uid()
        employee_id = get_employee_id(email)
        cur.execute(
            "INSERT INTO team (team_id, company_id, id_input, first_name, last_name, employee_id, role_id, employment_type, email, status) VALUES (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s)", (new_id, company_id, id_input, first_name, last_name, employee_id, role_id, employment_type, email, "pending"))
        conn.commit()
    conn.commit()
    return return_success()


def get_employee_id(email):
    ''' Get employee_id from email '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id FROM employee_user WHERE email = %s", (email,))
        employee_id = cur.fetchone()
        if employee_id == None:
            return None
    return employee_id[0]


def get_team(company_id, keyword=None, status=None):
    ''' Get all employees in company and filter if needed'''
    # lowercase keyword and status
    keyword_ubiq = '%%'
    if keyword != None:
        keyword_ubiq = "%" + keyword.lower() + "%"
        keyword = keyword.lower()
    status='%%' if (status == None or status == '') else status.lower()

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
                """SELECT a.team_id as unique_id, a.employee_id as employee_id, a.role_id as role_id, id_input as id, a.first_name as first, a.last_name as last, a.email as email, j.role_name as role, a.employment_type as type, a.status 
                FROM team as a, job_roles as j 
                WHERE a.role_id = j.role_id AND
                a.company_id = %s AND
                (LOWER(a.first_name) = %s OR LOWER(a.last_name) = %s OR LOWER(id_input) LIKE %s OR LOWER(a.email) LIKE %s OR LOWER(j.role_name) LIKE %s) AND LOWER(a.status) LIKE %s AND a.status != 'unassigned' """, (company_id, keyword, keyword, keyword_ubiq, keyword_ubiq, keyword_ubiq, status))
        employees = cur.fetchall()
        team_list = []
        if employees != None:
            for employee in employees:
                team_list.append(Member(id=employee[0], id_input=employee[3], first_name=employee[4], last_name=employee[5], email=employee[6], role=employee[7], employee_id=employee[1], role_id=employee[2], employment_type=employee[8], status=employee[9]))
    return team_list


def get_roles(company_id):
    '''Get all active roles frmo job_roles table'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT role_id, role_name FROM job_roles WHERE company_id = %s AND status = %s", (company_id, "active"))
        roles = cur.fetchall()
        role_list = []
        if roles != None:
            for role in roles:
                role_list.append(Role(role_id=role[0], role_name=role[1]))
    return role_list


def get_role_comprehensive(company_id, keyword=None):
    '''Get all the roles and their stats for active roles'''
    # lowercase keyword
    if keyword != None:
        keyword = '%' + keyword.lower() + '%'
    else:
        keyword = '%%'
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT j.role_id, j.role_name, (SELECT count(*) from team WHERE team.role_id = j.role_id AND team.status='unassigned'), (SELECT count(*) from team WHERE team.role_id = j.role_id AND team.status='completed'), completion_rate, average_score, average_time 
            FROM job_roles as j
            WHERE
            j.company_id = %s AND
            j.status = %s AND
            lower(j.role_name) LIKE %s""", (company_id, "active", keyword))
        roles = cur.fetchall()
        role_list = []
        if roles != None:
            for role in roles:
                role_list.append(Role_Info(role_id=role[0], role_name=role[1], count=role[2], completed=role[3], completion_rate=role[4], average_score=role[5], average_time=role[6]))
    return role_list


def check_emp_in_team(company_id, team_id):
    '''Check if employee is in team'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM team WHERE company_id = %s AND team_id = %s AND status != 'unassigned'" , (company_id, team_id))
        employee = cur.fetchone()
        if employee == None:
            return False
    return True


def unasign_employee_role(company_id, team_id):
    '''Unassign employee from role by setting status to unassigned'''
    if check_emp_in_team(company_id, team_id) == False:
        return return_error("Permission Denied")
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE team SET status = %s WHERE company_id = %s AND team_id = %s", ("unassigned", company_id, team_id))
        conn.commit()
    return return_success()
