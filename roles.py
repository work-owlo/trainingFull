import sqlite3

from utils import *
from classes import *


def add_role(company_id, role_id, role_name, role_description):
    ''' Add role to company '''
    # Check if role already exists

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM job_roles WHERE role_name = %s AND company_id = %s AND status != 'deleted'", (role_name, company_id))
        role = cur.fetchone()
        if role != None:
            return return_error("Role already exists")
        cur.execute(
            "INSERT INTO job_roles (role_id, company_id, role_name, role_description, status) VALUES (%s, %s, %s, %s, %s)", (role_id, company_id, role_name, role_description, "pending"))
        conn.commit()
    return return_success()


def add_role_tool_relationship(role_id, tool_id):
    ''' Add relationship between role and tool '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        rt_id = generate_uid()
        cur.execute(
            "INSERT INTO role_tools (rt_id, role_id, tool_id, status) VALUES (%s, %s, %s, %s)", (rt_id, role_id, tool_id, 'pending'))
        conn.commit()


def assign_employee_role(company_id, id_input, first_name, last_name, email, role_id, employment_type):
    with get_db_connection() as conn:
        ''' Assign role to employee '''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM team WHERE role_id = %s AND email = %s AND (status = 'pending' or status='completed')", (role_id, email))
            employee = cur.fetchone()
            if employee != None:
                return return_error("Employee already exists for this role")
            new_id = generate_uid()
            employee_id = get_employee_id(email)
            cur.execute(
                "INSERT INTO team (team_id, company_id, id_input, first_name, last_name, employee_id, role_id, employment_type, email, status) VALUES (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s)", (new_id, company_id, id_input, first_name, last_name, employee_id, role_id, employment_type, email, "pending"))
            conn.commit()
            add_training_tasks(new_id, role_id)
        return return_success()


def add_training_tasks(team_id, role_id):
    ''' Add training tasks to employee '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        training_id = generate_uid()
        cur.execute(
            "SELECT module.module_id, module.tool_id FROM module, role_module WHERE module.module_id = role_module.module_id AND role_id = %s AND status = 'active'", (role_id,))
        modules = cur.fetchall()
        for module in modules:
            cur.execute("SELECT query_id, query FROM query WHERE module_id = %s", (module[0],))
            queries = cur.fetchall()
            if module[1] == '4':
                for query in queries:
                    training_id = generate_uid()
                    cur.execute(
                        "INSERT INTO training (training_id, team_id, module_id, query_id, training_status) VALUES (%s, %s, %s, %s, %s)", (training_id, team_id, module[0], query[0], 'pending'))
                    conn.commit()
            else:
                for query in queries:
                    training_id = generate_uid()
                    print(query)
                    cur.execute("INSERT INTO training (training_id, team_id, module_id, query_id, training_status) VALUES (%s, %s, %s, %s, %s)", (training_id, team_id, module[0], query[1], 'pending'))
                    conn.commit()


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

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
                """SELECT a.team_id as unique_id, a.employee_id as employee_id, a.role_id as role_id, id_input as id, a.first_name as first, a.last_name as last, a.email as email, j.role_name as role, a.employment_type as type, a.status 
                FROM team as a, job_roles as j 
                WHERE a.role_id = j.role_id AND
                a.company_id = %s AND
                (LOWER(a.first_name) = %s OR LOWER(a.last_name) = %s OR LOWER(id_input) LIKE %s OR LOWER(a.email) LIKE %s OR LOWER(j.role_name) LIKE %s) AND a.status != 'unassigned' AND j.status = 'active' """, (company_id, keyword, keyword, keyword_ubiq, keyword_ubiq, keyword_ubiq))
        employees = cur.fetchall()
        team_list = []
        if employees != None:
            for employee in employees:
                team_list.append(Member(id=employee[0], id_input=employee[3], first_name=employee[4], last_name=employee[5], email=employee[6], role=employee[7], employee_id=employee[1], role_id=employee[2], employment_type=employee[8], status=int(get_training_status(employee[0]))))
        print(status)
        if status == 'completed':
            team_list = [t for t in team_list if t.status == '100']
        elif status == 'pending':
            team_list = [t for t in team_list if t.status != '100']
        
    
    return team_list


def get_training_status(team_id):
    # get training status (in percentage) for a role
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT COUNT(*) as count
            FROM training
            WHERE training.team_id = %s
              AND training.training_status = 'completed'
        ''', (team_id,))
        completed = cur.fetchone()['count']
        cur.execute('''
            SELECT COUNT(*) as count
            FROM training
            WHERE training.team_id = %s
        ''', (team_id,))
        total = cur.fetchone()['count']
        print('value', completed, total)
        if total and completed:
            return round(completed/total*100)
    return 0


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
            """SELECT j.role_id, j.role_name, (SELECT count(*) from team WHERE team.role_id = j.role_id AND team.status!='unassigned'), (SELECT count(*) from team WHERE team.role_id = j.role_id AND team.status='completed'), completion_rate, average_score, average_time, j.status 
            FROM job_roles as j
            WHERE
            j.company_id = %s
            AND lower(j.role_name) LIKE %s
            AND j.status != 'deleted' """, (company_id, keyword))
        roles = cur.fetchall()
        role_list = []
        if roles != None:
            for role in roles:
                role_list.append(Role_Info(role_id=role[0], role_name=role[1], count=role[2], completed=role[3], completion_rate=role[4], average_score=role[5], average_time=role[6], status=role[7]))
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


def get_employee_email(team_id):
    '''Get employee email'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT email FROM team WHERE team_id = %s AND status != 'unassigned'" , (team_id,))
        employee = cur.fetchone()
        if employee == None:
            return False
    return employee[0]


def get_comp_email(team_id):
    '''Get company email'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT email FROM manager_user WHERE company_id = (SELECT company_id FROM team WHERE team_id = %s AND status != 'unassigned')" , (team_id,))
        employee = cur.fetchone()
        if employee == None:
            return False
    return employee[0]


def check_role_in_company(company_id, role_id):
    '''Check if role is in company'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM job_roles WHERE company_id = %s AND role_id = %s AND status != 'deleted'" , (company_id, role_id))
        role = cur.fetchone()
        if role == None:
            return False
    return role[0]


def get_role_tools_remaining(role_id):
    '''Get all the tools for a role'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT r.tool_id, tool_name, tool_icon FROM tools as t, role_tools as r WHERE t.tool_id = r.tool_id AND role_id = %s AND r.status = 'pending' ORDER BY tool_name LIMIT 1", (role_id,))
        tool = cur.fetchone()
        return None if tool == None else Tool_info(tool_id=tool[0], tool_name=tool[1], tool_icon=tool[2])


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


def delete_role(company_id, role_id):
    '''Delete role by setting status to deleted'''
    permission = check_role_in_company(company_id, role_id)
    if permission == False:
        return return_error("Permission Denied")
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE job_roles SET status = %s WHERE role_id = %s", ("deleted", role_id))
        conn.commit()
    return return_success()


def add_module_to_role(role_id, module_id):
    '''Add module to role'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO role_module (role_id, module_id, status) VALUES (%s, %s, %s)", (role_id, module_id, 'active'))
        conn.commit()
    return return_success()


def verify_module_access(company_id, module_id, tool_id):
    '''Check if module is in company or has public access'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT module_id
            FROM module, company 
            WHERE module.company_id = company.company_id
                AND (module.company_id = %s OR module.access = 'public')
                AND module_id = %s 
                AND company.status != 'deleted'
                AND module.tool_id = %s
                """, (company_id, module_id, tool_id))
        module = cur.fetchone()
        if module == None:
            return False
    return True


def verify_pending_rool_tool_relationship(role_id, tool_id):
    '''Check if tool is in role'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT tool_id FROM role_tools WHERE role_id = %s AND tool_id = %s and status='pending'", (role_id, tool_id))
        tool = cur.fetchone()
        if tool == None:
            return False
    return True


def update_role_tool_status(role_id, tool_id, status):
    '''Update role tool status'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE role_tools SET status = %s WHERE role_id = %s AND tool_id = %s", (status, role_id, tool_id))
        conn.commit()
    return return_success()


def complete_role(company_id, role_id):
    '''Complete role by setting status to completed'''
    permission = check_role_in_company(company_id, role_id)
    if permission == False:
        return return_error("Permission Denied")
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE job_roles SET status = %s WHERE role_id = %s", ("active", role_id))
        conn.commit()
    return return_success()


def get_role_info(role_id):
    '''Get role info'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT role_id, role_name, role_description, status FROM job_roles WHERE role_id = %s""", (role_id,))
        role = cur.fetchone()
        if role == None:
            return None
        return Role(role_id=role[0], role_name=role[1], role_description=role[2], status=role[3])


def get_role_modules(role_id):
    '''Get all the modules for a role'''
    # get all tools
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """ SELECT r.tool_id, t.tool_name, t.tool_icon, r.status  
            FROM role_tools as r, tools as t
            WHERE r.tool_id = t.tool_id AND role_id = %s AND r.status = 'active'""", (role_id,))
        tools = cur.fetchall()
        if tools == None:
            return None

    # get all modules for each tool
    module_list = []
    
    for tool in tools:
        modules = {}
        modules['tool_name'] = tool['tool_name']
        modules['tool_id'] = tool['tool_id']
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                """ SELECT module_id, module_title, module_description  
                FROM module
                WHERE tool_id = %s""", (tool['tool_id'],))
            modules['modules'] = cur.fetchall()
            module_list.append(modules)

    return module_list