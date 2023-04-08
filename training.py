from classes import *
from utils import *
from generate import *
from nlp import *
import datetime
import spacy
import numpy as np
import requests
from scipy.spatial.distance import cosine

def get_job_roles(company_id):
    '''Get all roles that from company_id from the database.'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT role_id, role_name FROM job_roles WHERE company_id = %s and status != 'deleted' ORDER BY role_name asc", (company_id,))
        roles = cur.fetchall()
        roles_list = []
        roles_list.append(Role(role_id=0, role_name="--- Yours ---", disabled='1'))
        if roles != None:
            for role in roles:
                roles_list.append(Role(role_id=role[0], role_name=role[1]))
    roles_list.append(Role(role_id=0, role_name="--- Public ---", disabled='1'))
    return roles_list + get_public_roles()


def get_public_roles():
    '''Get all roles that from company_id from the database.'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT role_id, role_name FROM job_roles WHERE company_id = %s ORDER BY role_name asc", ('1',))
        roles = cur.fetchall()
        roles_list = []
        if roles != None:
            for role in roles:
                roles_list.append(Role(role_id=role[0], role_name=role[1]))
    return roles_list


def get_tools():
    '''Get all tools from the database.'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT tool_id, tool_name, tool_icon, status FROM tools ORDER BY status asc, tool_name asc")
        tools = cur.fetchall()
        tools_list = []
        if tools != None:
            for tool in tools:
                tools_list.append(Tool(id=tool[0], name=tool[1], icon=tool[2], status=tool[3], tool_id=tool[0]))
    return tools_list


# def get_public_modules(tool_id, company_id):
#     '''Get all public modules for a tool.'''
#     with get_db_connection() as conn:
#         cur = conn.cursor()
#         tool_id = str(tool_id)
#         cur.execute("SELECT module_id, module_title, module_description FROM module WHERE tool_id = %s AND access = 'public' AND not module.company_id = %s  ORDER BY module_title asc", (tool_id,company_id))
#         modules = cur.fetchall()
#         modules_list = []
#         if modules != None:
#             for module in modules:
#                 modules_list.append(Module(id=module[0], name=module[1], description=module[2]))
#     return modules_list

def get_similar(wordvec, n=3):
    with get_db_connection() as conn:
        cur = conn.cursor()
        vec1 = [float(i) for i in wordvec]
        cur.execute("SELECT role_id, wordvec FROM job_roles WHERE company_id='1'")
        roles = cur.fetchall()
        similarity_list = []
        for role in roles:
            r_id = role[0]
            vec2 = role[1]
            similarity = cosine(vec1, vec2)
            similarity_list.append((r_id, similarity))

        similarity_list.sort(key=lambda x: x[1])
        return similarity_list[:n]
    

def get_recommended_modules(role_id, tool_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        # get role_name from role_id
        cur.execute("SELECT wordvec FROM job_roles WHERE role_id=%s", (role_id,))
        wordvec = cur.fetchone()[0]
        # get similar roles
        similar_roles = get_similar(wordvec)
        # get modules for similar roles
        modules = []
        mod_names = []
        for role in similar_roles:
            # print(role)
            cur.execute("SELECT module.module_id, module.module_title, module.module_description  FROM role_module, module WHERE role_module.module_id=module.module_id AND role_id=%s AND tool_id=%s", (role[0], tool_id))
            mods=cur.fetchall()
            if mods != None:
                for mod in mods:
                    if mod[1] not in mod_names and len(modules) < 20:
                        mod_names.append(mod[1])
                        modules.append(Module(id=mod[0], name=mod[1], description=mod[2]))

        return modules[:20]


def get_private_modules(tool_id, company_id):
    '''Get all private modules for a tool.'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT module_id, module_title, module_description FROM module WHERE tool_id = %s AND company_id = %s ORDER BY module_title asc", (tool_id, company_id))
        modules = cur.fetchall()
        modules_list = []
        if modules != None:
            for module in modules:
                modules_list.append(Module(id=module[0], name=module[1], description=module[2]))
    return modules_list


def search_modules_by_keyword(keyword, tool, company_id):
    '''Search modules to see if keyword is a substring of title, description, text, problem, situation, respond'''
    with get_db_connection() as conn:
        keyword = keyword.lower()
        cur = conn.cursor()
        cur.execute("""SELECT module_id, module_title, module_description 
        FROM module WHERE tool_id = %s AND (company_id = %s or access = 'public') 
            AND (LOWER(module_title) LIKE %s OR LOWER(module_description) LIKE %s OR LOWER(module_text) LIKE %s OR LOWER(problem) LIKE %s OR LOWER(situation) LIKE %s OR LOWER(respond) LIKE %s) 
            LIMIT 20
            """, (tool, company_id, '%'+keyword+'%', '%'+keyword+'%', '%'+keyword+'%', '%'+keyword+'%', '%'+keyword+'%', '%'+keyword+'%'))
        modules = cur.fetchall()
        modules_list = []
        if modules != None:
            for module in modules:
                modules_list.append(Module(id=module[0], name=module[1], description=module[2]))
    return modules_list


def get_role_modules(role_id, tool_id):
    '''Get all modules for a role.'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT module.module_id, module.module_title, module.module_description FROM role_module, module WHERE role_module.module_id=module.module_id AND role_id=%s AND tool_id=%s", (role_id, tool_id))
        modules = cur.fetchall()
        modules_list = []
        if modules != None:
            for module in modules:
                modules_list.append(Module(id=module[0], name=module[1], description=module[2]))
    return modules_list

# add module to db
def add_module(company_id, title, desc, tool_id, text, access='private'):
    module_id = generate_id()
    with get_db_connection() as conn:
        cur = conn.cursor()
        print(company_id, title, desc, tool_id, text)
        cur.execute("INSERT INTO module (module_id, company_id, tool_id, module_title, module_description, access, module_text) VALUES (%s, %s, %s, %s, %s, %s, %s)", (module_id, company_id, tool_id, title, desc, access, text))
    return module_id


def add_module_simulator(company_id, title, desc, tool_id, num_chats, customer, situation, problem, respond, format, access='private', text=None):
    module_id = generate_id()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO module (module_id, company_id, tool_id, module_title, module_description, access, module_text, num_chats, customer, situation, problem, respond, format) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (module_id, company_id, tool_id, title, desc, access, text, num_chats, customer, situation, problem, respond, format))
    return module_id


def save_queries(module_id, q_list):
    with get_db_connection() as conn:
        cur = conn.cursor()
        for i in range(len(q_list)):
            q_id = generate_id()
            q = q_list[i]
            cur.execute("INSERT INTO query (query_id, module_id, query, query_type, path_id) VALUES (%s, %s, %s, %s, %s)", (q_id, module_id, q, 'compliance', i))
            conn.commit()


def save_queries_physical(module_id, q_list, test_bool):
    with get_db_connection() as conn:
        cur = conn.cursor()
        for i in range(len(q_list)):
            q_id = generate_id()
            q = q_list[i]
            cur.execute("INSERT INTO query (query_id, module_id, query, query_type, path_id, test_bool) VALUES (%s, %s, %s, %s, %s, %s)", (q_id, module_id, q, 'physical', i, test_bool))
            conn.commit()


def add_training_sample(module_id, company_id, tool_id):
    '''Add sample training data'''
    # check if training data already exists
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s", (module_id, company_id))
        training = cur.fetchall()
        if training:
            if tool_id in ['1', '2']:
                cur.execute("""UPDATE training SET response=NULL, query_id=NULL, training_status=%s
                            WHERE team_id=%s AND module_id = %s and id > 0""", ('pending', company_id, module_id))
                cur.execute("""UPDATE training SET response=NULL, training_status=%s
                            WHERE team_id=%s AND module_id = %s and id = 0""", ('pending', company_id, module_id))
                conn.commit()
            else:
                cur.execute("""UPDATE training SET response=NULL, training_status=%s
                            WHERE team_id=%s AND module_id = %s""", ('pending', company_id, module_id))
                conn.commit()
        else:
            team_id = company_id
            training_status = 'pending'
            # get data from query
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT query, test_bool FROM query WHERE module_id = %s", (module_id,))
                query_ids = cur.fetchall()
                for query_id in query_ids:
                    print(query_id[0])
                    training_id = generate_id()
                    cur.execute("INSERT INTO training (training_id, team_id, module_id, query_id, training_status, test_bool) VALUES (%s, %s, %s, %s, %s, %s)", (training_id, team_id, module_id, query_id[0], training_status, query_id[1]))
                    conn.commit()


def get_training_compliance(module_id, team_id):
    '''Get training data for compliance'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='completed' and test_bool='false' ORDER BY id asc ", (module_id, team_id))
        training_completed = cur.fetchall()

        # parse training data into chat format
        training_data = []
        for t in training_completed:
            print(t)
            # add query
            training_data.append({'from': 'bot', 'text': t['query_id']})
            if t['response']:
                training_data.append({'from': 'user', 'text': t['response']})
            if t['responsetoresponse']:
                training_data.append({'from': 'bot', 'text': t['responsetoresponse']})

        # get pending training data
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='pending' and test_bool='false' ORDER BY id asc LIMIT 1 ", (module_id, team_id))
        pending = cur.fetchone()
        if pending:
            training_data.append({'from': 'bot', 'text': pending['query_id']})
        print('training_data: ', training_data)
        return training_data
    

def get_training_compliance_chat(module_id, team_id):
    '''Get training data for compliance'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='completed' and test_bool='false' ORDER BY id asc ", (module_id, team_id))
        training_completed = cur.fetchall()

        # parse training data into chat format
        training_data = []
        for t in training_completed:
            print(t)
            # add query
            training_data.append({'from': 'bot', 'text': t['query_id'], 'status': 'completed'})
            if t['response']:
                training_data.append({'from': 'user', 'text': t['response'], 'status': 'completed'})
            if t['responsetoresponse']:
                training_data.append({'from': 'bot', 'text': t['responsetoresponse'], 'status': 'completed'})

        # get pending training data
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='pending' and test_bool='false' ORDER BY id asc LIMIT 1 ", (module_id, team_id))
        pending = cur.fetchone()
        if pending:
            training_data.append({'from': 'bot', 'text': pending['query_id'], 'status': 'pending'})
        print('training_data: ', training_data)
        return training_data
    

def get_training_compliance_slides(module_id, team_id):
    '''Get training data for compliance'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='completed' and test_bool='true' ORDER BY id asc ", (module_id, team_id))
        training_completed = cur.fetchall()
        training_data = []
        for i in range(len(training_completed)):
            t = training_completed[i]
            training_data.append({'from': 'bot', 'text': t['query_id'], 'status': 'completed', 'id': i+1})
        # get pending training data
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='pending' and test_bool='true' ORDER BY id asc LIMIT 1 ", (module_id, team_id))
        pending = cur.fetchone()
        if pending:
            training_data.append({'from': 'bot', 'text': pending['query_id'], 'test_bool': 'true', 'status': 'pending', 'id': len(training_data)+1})
        print('training_data: ', training_data)
        return training_data
    

def get_training_simulator(module_id, team_id):
    '''Get training data for compliance'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='completed' ORDER BY id asc ", (module_id, team_id))
        training_completed = cur.fetchall()

        # parse training data into chat format
        training_data = []
        for t in training_completed:
            # add query
            training_data.append({'role': 'assistant', 'content': t['query_id']})
            if t['response']:
                training_data.append({'role': 'user', 'content': t['response']})
        
        # get tool_name
        cur.execute("SELECT tool_name FROM tools WHERE tool_id = (SELECT tool_id FROM module WHERE module_id = %s)", (module_id,))
        tool_name = cur.fetchone()

        # get pending training data
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='pending' ORDER BY id asc LIMIT 1 ", (module_id, team_id))
        pending = cur.fetchone()
        if pending:
            if pending['query_id'] is None:
                # generate text and update
                question = generate_simulation_response(generate_prompt(module_id), training_data[0:], tool_name)
                cur.execute("UPDATE training SET query_id = %s WHERE training_id = %s", (question, pending['training_id']))
                conn.commit()
                training_data.append({'role': 'assistant', 'content': question})
            else:
                training_data.append({'role': 'assistant', 'content': pending['query_id']})
                if pending['response']:
                    training_data.append({'role': 'user', 'content': pending['response']})
        for i in training_data:
            # remove any occurrences of the phrase "Generate reply to this question with you as the customer only.  I will answer as the customer service representative"
            i['content'] = i['content'].replace("Generate reply to this question with you as the customer only.  I will answer as the customer service representative", "")
            i['content'] = i['content'].replace("Generate reply to this question with you as the customer only. I will answer as the customer service representative", "")
        print('training_data: ', training_data)
        return training_data
    

def generate_prompt(module_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM module WHERE module_id = %s", (module_id,))
        module = cur.fetchone()
        prompt = f" Problem: {module['problem']} "
        prompt += f" You play the role of a {module['customer']}"
        prompt += f" Sitation: {module['situation']}"
        prompt += f" Respond: {module['respond']}"
        prompt += f" Make the conversation last {module['num_chats'] * 2} chats"
        prompt += " Only give me the first chat of the conversation"
    return {'role': 'assistant', 'content': prompt}



def update_training_status(training_id, response, status, score=None):
    '''Update training status'''
    sentiment = get_sentiment_score(response)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE training SET updated = now(), training_status = %s, response = %s, responsetoresponse = %s, sentiment = %s WHERE training_id = %s", (status, response, score, sentiment, training_id))
        
        # get progress for this module, and if 100%, generate action items
        cur.execute("SELECT count(*) FROM training WHERE module_id = (SELECT module_id FROM training WHERE training_id = %s) AND team_id = (SELECT team_id FROM training WHERE training_id = %s)", (training_id, training_id))
        total = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM training WHERE module_id = (SELECT module_id FROM training WHERE training_id = %s) AND team_id = (SELECT team_id FROM training WHERE training_id = %s) AND training_status = 'pending'", (training_id, training_id))
        pending = cur.fetchone()[0]
        progress = (total - pending) / total
        if progress == 1:
            cur.execute("SELECT module_id, team_id FROM training WHERE training_id = %s", (training_id,))
            module_id = cur.fetchone()[0]
            team_id = cur.fetchone()[1]
            training_data = get_training_simulator(module_id, team_id)
            # get goal of module
            cur.execute("SELECT respond FROM module WHERE module_id = %s", (module_id,))
            goal = cur.fetchone()[0]
            simulator = generate_analysis(training_data, goal)
            cur.execute("INSERT INTO goal (team_id, module_id, goal_met, goal_desc, steps) VALUES (%s, %s, %s, %s, %s)", (team_id, module_id, simulator['goal_met'], simulator['goal_desc'], simulator['steps']))


def get_mod_analytics(module_id, team_id):
    '''Get module analytics'''
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM goal WHERE module_id = %s AND team_id = %s", (module_id, team_id))
        return cur.fetchone()
    

def update_training_status_slides(training_id, status):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE training SET training_status = %s, updated = now() WHERE training_id = %s", (status, training_id))
        conn.commit()


def time_tracker(training_id):
    '''Track time for training'''
    tracker_id = generate_id()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO training_time_tracker (time_tracker_token, training_id, started) VALUES (%s, %s, NOW())", (tracker_id, training_id))
        conn.commit()
        return tracker_id
    

def end_time_tracker(tracker_id, training_id):
    '''End time tracker'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        # get time and up
        # cur.execute("UPDATE training_time_tracker SET ended = NOW() WHERE time_tracker_token = %s", (tracker_id,))
        cur.execute("""
        UPDATE training 
        SET seconds_spent = 
            (SELECT EXTRACT(EPOCH FROM (NOW() - started))::int FROM training_time_tracker WHERE time_tracker_token = %s) 
        WHERE training_id = %s
        """, (tracker_id, training_id))
        cur.execute("DELETE FROM training_time_tracker WHERE time_tracker_token = %s", (tracker_id,))
        conn.commit()


def create_simulator_video(text):
    # url = "https://api.d-id.com/talks"
    # print(text)
    # payload = {
    #     "script": {
    #         "type": "text",
    #         "provider": {
    #             "type": "microsoft",
    #             "voice_id": "Jenny"
    #         },
    #         "ssml": "false",
    #         "input": text
    #     },
    #     "config": {
    #         "fluent": "false",
    #         "pad_audio": "0.0"
    #     },
    #     "source_url": "https://clips-presenters.d-id.com/amy/image.png"
    # }
    # headers = {
    #     "accept": "application/json",
    #     "content-type": "application/json",
    #     "authorization": "Basic WVc1emFIVnNjR0YxYkVCaVpYSnJaV3hsZVM1bFpIVTpydm1SQ09DUVFfSTI5ZkItTFU3czk="
    # }

    # response = requests.post(url, json=payload, headers=headers)
    # print(response.json())
    # return get_talk(response.json()['id'])
    id = 'tlk_4z8eg9_SRpae6WUybyL_3'
    return get_talk(id)


def get_talk(id):

    url = "https://api.d-id.com/talks/" + id

    headers = {
        "accept": "application/json",
        "authorization": "Basic WVc1emFIVnNjR0YxYkVCaVpYSnJaV3hsZVM1bFpIVTpydm1SQ09DUVFfSTI5ZkItTFU3czk="
    }

    response = requests.get(url, headers=headers)
    print(response.json()['result_url'])
    return response.json()['result_url']
