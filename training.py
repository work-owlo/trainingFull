from classes import *
from utils import *
from generate import *

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


def get_public_modules(tool_id, company_id):
    '''Get all public modules for a tool.'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT module_id, module_title, module_description FROM module WHERE tool_id = %s AND access = 'public' AND not module.company_id = %s  ORDER BY module_title asc", (tool_id,company_id))
        modules = cur.fetchall()
        modules_list = []
        if modules != None:
            for module in modules:
                modules_list.append(Module(id=module[0], name=module[1], description=module[2]))
    return modules_list


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


# add module to db
def add_module(company_id, title, desc, tool_id, text, access='private'):
    module_id = generate_id()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO module (module_id, company_id, tool_id, module_title, module_description, access, module_text) VALUES (%s, %s, %s, %s, %s, %s, %s)", (module_id, company_id, tool_id, title, desc, access, text))
    return module_id


def add_module_simulator(company_id, title, desc, tool_id, num_chats, customer, situation, problem, respond, access='private', text=None):
    module_id = generate_id()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO module (module_id, company_id, tool_id, module_title, module_description, access, module_text, num_chats, customer, situation, problem, respond) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (module_id, company_id, tool_id, title, desc, access, text, num_chats, customer, situation, problem, respond))
    return module_id


def save_queries(module_id, q_list):
    with get_db_connection() as conn:
        cur = conn.cursor()
        for i in range(len(q_list)):
            q_id = generate_id()
            q = q_list[i]
            cur.execute("INSERT INTO query (query_id, module_id, query, query_type, path_id) VALUES (%s, %s, %s, %s, %s)", (q_id, module_id, q, 'compliance', i))
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
                cur.execute("SELECT query FROM query WHERE module_id = %s", (module_id,))
                query_ids = cur.fetchall()
                for query_id in query_ids:
                    print(query_id[0])
                    training_id = generate_id()
                    cur.execute("INSERT INTO training (training_id, team_id, module_id, query_id, training_status) VALUES (%s, %s, %s, %s, %s)", (training_id, team_id, module_id, query_id[0], training_status))
                    conn.commit()


def get_training_compliance(module_id, team_id):
    '''Get training data for compliance'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='completed' ORDER BY id asc ", (module_id, team_id))
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
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='pending' ORDER BY id asc LIMIT 1 ", (module_id, team_id))
        pending = cur.fetchone()
        if pending:
            training_data.append({'from': 'bot', 'text': pending['query_id']})
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

        # get pending training data
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s AND training_status='pending' ORDER BY id asc LIMIT 1 ", (module_id, team_id))
        pending = cur.fetchone()
        if pending:
            if pending['query_id'] is None:
                # generate text and update
                question = generate_simulation_response(generate_prompt(module_id), training_data[:])
                cur.execute("UPDATE training SET query_id = %s WHERE training_id = %s", (question, pending['training_id']))
                conn.commit()
                training_data.append({'role': 'assistant', 'content': question})
            else:
                training_data.append({'role': 'assistant', 'content': pending['query_id']})
            
        return training_data
    

def generate_prompt(module_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM module WHERE module_id = %s", (module_id,))
        module = cur.fetchone()
        prompt = f"Problem: {module['problem']} "
        prompt += f"You play the role of a {module['customer']}"
        prompt += f"Sitation: {module['situation']}"
        prompt += f"Respond: {module['respond']}"
        prompt += f"Make the conversation last {module['num_chats'] * 2} chats"
        prompt += "Only give me the first chat of the conversation"
    return {'role': 'assistant', 'content': prompt}



def update_training_status(training_id, response, status, score=None):
    print(training_id, response, status)
    '''Update training status'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE training SET training_status = %s, response = %s, responsetoresponse = %s WHERE training_id = %s", (status, response, score, training_id))
        conn.commit()

