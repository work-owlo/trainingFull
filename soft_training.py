from utils import *

def get_next_page(team_id, module_id, adjustment_factor):
    '''Get the next page to be trained'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""SELECT training_id, training.query_id, query.page_id, query, query_type, prev_query_id
                        FROM training, query 
                        WHERE training_status = %s AND team_id = %s AND training.module_id = query.module_id
                        AND training.query_id = query.query_id AND training.module_id = %s
                        ORDER BY CAST(query.path_id as INTEGER) ASC LIMIT 1""", ('pending', team_id, module_id))
        query = cur.fetchone()
        if query is not None:
            screenshots = get_screenshot(query['page_id'], adjustment_factor)
            cur.execute("SELECT * FROM query_element WHERE query_id = %s", (query['query_id'],))
            elements = cur.fetchall()
            elements = [dict(element) for element in elements]
            elements = get_elements(elements, adjustment_factor)
            return query['training_id'], elements, screenshots


def has_pending_training(team_id, module_id):
    '''Check if there are any pending training for this team member with the module_id'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT training_id FROM training WHERE training_status = %s AND team_id = %s AND module_id = %s""", ('pending', team_id, module_id))
        query = cur.fetchone()
        return query is not None


def check_training_status(team_id, training_id):
    '''Check if there are any pending training'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT training_id
                        FROM training, query 
                        WHERE training_status = %s AND team_id = %s AND training.query_id = query.query_id
                        AND training_id = %s
                        ORDER BY query.path_id ASC LIMIT 1""", ('pending', team_id, training_id))
        query = cur.fetchone()
        return query is not None


def get_elements(e, adjustment_factor):
    elements = {}

    with get_db_connection() as conn:
        cur = conn.cursor()

    elements['input'] = []
    elements['button'] = []
    for element in e:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if element['element_type'] == 'input':
                cur.execute('''SELECT element.id, generated_value as input_value, element.context as context, element_subtype as type, element_value as value, placeholder as placeholder, round((width * %s), 2) as width, round((height * %s),2) as height, round((x * %s),2) as x, round((y * %s),2) as y, element_action.to_page_id
                                        FROM element, element_action
                                        WHERE element.id = %s AND element.id = element_action.element_id  
                                        and (element_type = 'input' or element_type = 'select')
                                        ORDER BY element.id ASC''', (adjustment_factor, adjustment_factor, adjustment_factor, adjustment_factor, element['element_id'],))
                inputs = cur.fetchone()
                inputs = dict(inputs)
                if inputs['type'] == 'select':
                    cur.execute('''SELECT * FROM select_option WHERE element_id = %s''', (element['element_id'],))
                    options = cur.fetchall()
                    options = [dict(option) for option in options]
                    inputs['options'] = options
                elements['input'].append(inputs)
                
            if element['element_type'] == 'button':
                cur.execute('''SELECT element.id, element.context as context, element_value as button_text, round((width * %s), 2) as width, round((height * %s),2) as height, round((x * %s),2) as x, round((y * %s),2) as y, element_action.to_page_id
                            FROM element, element_action WHERE element.id = %s AND element.id = element_action.element_id
                            and element_type = 'button'
                            ORDER BY element.id ASC''', (adjustment_factor, adjustment_factor, adjustment_factor, adjustment_factor, element['element_id'],))
                buttons = cur.fetchone()
                # store as set
                if buttons not in elements['button']:
                    elements['button'].append(dict(buttons))
    return elements


def get_screenshot(page_id, adjustment_factor):
    with get_db_connection() as conn:
        '''Get all images'''
        page_id = str(page_id)
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''SELECT screenshot_name, img_counter, (y * %s) as y
                        FROM screenshot WHERE node_id = %s ORDER BY img_counter ASC''', (adjustment_factor, page_id))
        images = cur.fetchall()
        images = [dict(image) for image in images]
        return images


def verify_input(input, element_id, training_id):
    '''Verify the input value'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # confirm element_id is a part of training_id
        cur.execute('''SELECT training.query_id 
                        FROM training, query_element
                        WHERE training_id = %s AND query_element.query_id = training.query_id AND element_id = %s''', (training_id, element_id))
        query_id = cur.fetchone()
        if query_id is None:
            return False

        cur.execute('''SELECT generated_value FROM element WHERE id = %s''', (element_id,))
        input_value = cur.fetchone()[0]
        return input_value == input



