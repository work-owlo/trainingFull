from utils import * 
import os
from classes import *


def get_training_invited(uid, keyword=None, filter_status=None):
    ''' Get all training programs an employee is invited to '''
        #     "id": 1,
        # "title": "Driving Fedex",
        # "description": "Some quick example text to build on the card title and make up the bulk of the card's content.",
        # "status": 100,
    if keyword is None:
        keyword = '' 
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT t.team_id, c.company_name, r.role_name, r.role_description, 50 as status
            FROM job_roles as r, company as c, team as t
            WHERE r.company_id = c.company_id AND t.role_id = r.role_id AND t.employee_id = %s AND r.status = 'active'
            AND (lower(r.role_name) LIKE %s or lower(r.role_description) LIKE %s or lower(c.company_name) LIKE %s)
        ''', (uid, '%'+keyword.lower()+'%', '%'+keyword.lower()+'%', '%'+keyword.lower()+'%' ))
        training = cur.fetchall()
    # if keyword:
    #     return [t for t in training if keyword in t['description']]
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
            SELECT tools.tool_id, tools.tool_name, tools.tool_icon, tools.status
            FROM tools, team, role_tools
            WHERE team.role_id = role_tools.role_id AND tools.tool_id = role_tools.tool_id AND team.team_id = %s AND tools.status = 'active'
        ''', (team_id,))
        tools = cur.fetchall()
        tool_lst = []
        if tools:
            for tool in tools:
                tool_lst.append(Tool(id=tool['tool_id'], name=tool['tool_name'], icon=tool['tool_icon'], status=tool['status']))
    return tool_lst


def get_training_status(team_id):
    # get training status (in percentage) for a role
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''COUNT(*) as count FROM role_module, team WHERE role_module.role_id = team.role_id and team_id = %s''', (team_id,))
        total = cur.fetchone()
        cur.execute('''COUNT(*) as count FROM training WHERE team_id = %s AND status = 'completed' ''', (team_id,))
        completed = cur.fetchone()
        if total and completed:
            return round(completed['count']/total['count']*100)
    return 0