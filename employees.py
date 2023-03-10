from utils import * 
import os
from classes import *


def get_training_invited(uid, keyword=None, filter_status=None):
    ''' Get all training programs an employee is invited to '''
    if keyword is None:
        keyword = '' 
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT t.team_id, c.company_name, r.role_name, r.role_description
            FROM job_roles as r, company as c, team as t
            WHERE r.company_id = c.company_id AND t.role_id = r.role_id AND t.employee_id = %s AND r.status = 'active'
            AND (lower(r.role_name) LIKE %s or lower(r.role_description) LIKE %s or lower(c.company_name) LIKE %s)
            AND (t.status = 'pending' or t.status = 'incomplete')
        ''', (uid, '%'+keyword.lower()+'%', '%'+keyword.lower()+'%', '%'+keyword.lower()+'%' ))
        training = cur.fetchall()
        for t in training:
            t['status'] = get_training_status(t['team_id'])
        if filter_status == 'incomplete':
            training = [t for t in training if t['status'] < 100 and t['status'] > 0]
        elif filter_status == 'complete':
            training = [t for t in training if t['status'] == 100]
        elif filter_status == 'pending':
            training = [t for t in training if t['status'] == 0]
    return training


def get_training_permission(employee_id, team_id):
    # Check if employee is assigned to the role
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT job_roles.role_name FROM team, job_roles WHERE team.role_id = job_roles.role_id AND employee_id = %s AND team.team_id = %s AND job_roles.status = 'active' 
        ''', (employee_id, team_id))
        role_name = cur.fetchone()
        if role_name:
            return role_name['role_name']
    return False


def get_training_tools(team_id):
    # get tools for a role
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT role_tools.rt_id as id, tools.tool_name, tools.tool_icon, tools.status
            FROM tools, team, role_tools
            WHERE team.role_id = role_tools.role_id AND tools.tool_id = role_tools.tool_id AND team.team_id = %s AND tools.status = 'active'
        ''', (team_id,))
        tools = cur.fetchall()
        tool_lst = []
        if tools:
            for tool in tools:
                tool_lst.append(Tool(id=tool['id'], name=tool['tool_name'], icon=tool['tool_icon'], status=tool['status']))
    return tool_lst

def get_module_permissions(employee_id, rt_id):
    ''' Check if employee is assigned to the role '''
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT r.role_id as role_id
            FROM team as t, role_tools as r
            WHERE r.role_id = t.role_id AND t.employee_id = %s AND r.rt_id = %s
            ''', (employee_id, rt_id))
        count = cur.fetchone()
    return count['role_id'] if count else False


def get_training_modules_tool(employee_id, rt_id):
    # get modules for a tool
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT module.module_id, module_title, module_description, training.status as status 
            FROM module, role_tools, role_module, training, team
            WHERE role_tools.rt_id = %s AND role_tools.role_id = role_module.role_id AND module.tool_id = role_tools.tool_id AND role_module.module_id = module.module_id AND team.team_id = training.team_id AND team.employee_id = %s AND training.module_id = module.module_id
            ORDER BY training.status, module.module_id
            ''', (rt_id, employee_id))
        modules = cur.fetchall()
        if not modules:
            return []
        print(modules)
        return modules


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