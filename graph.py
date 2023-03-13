import networkx as nx
from element import *
from utils import *
from scrape import *

def graph(parse_id, company_id):
    # create directed graph
    G = nx.DiGraph()
    root = '0'
    pages = [p[0] for p in Parse.get_pages(parse_id)]
    context_list = []
    for element in Element.get_all_elements(parse_id):
        actions = Element.get_real_actions_db(element['id'])
        for action in actions:
            # find shortest path from root to to_page_id
            # if to_page_id is not in the graph, add it
            if not action['to_page_id'] == action['page_id']:
                if G.has_node(action['page_id']) or action['page_id'] == root:
                    if not G.has_node(action['to_page_id']) and action['to_page_id'] in pages:
                        G.add_edge(element['page_id'], action['to_page_id'], element=element, action=action)
                        # element add context
                        context_list.append(element['id'])
                    elif action['to_page_id'] in pages:
                        G.add_edge(element['page_id'], action['to_page_id'], element=element, action=action)
                        shortest_path = nx.shortest_path(G, root, action['to_page_id'])
                        print('Shortest path', shortest_path)
                        print(len(shortest_path))
                        if action['page_id'] not in shortest_path:
                            # remove the edge from page_id to to_page_id
                            G.remove_edge(element['page_id'], action['to_page_id'])
                        else:
                            # remove all edges into to_page_id other than the shortest path
                            inner = list(G.in_edges(action['to_page_id']))
                            # get the first shortest path
                            for node in inner:
                                if node[0] not in shortest_path:
                                    G.remove_edge(node[0], action['to_page_id'])
                            context_list.append(element['id'])

        
    for e in context_list:
        Element.add_context(e)
    
            
    module_id = add_module_graph(parse_id, company_id)
    paths = find_paths(G, parse_id)
    print('Paths', paths)
    add_query(module_id, paths)
    # add_training_graph(module_id)
    return module_id


def find_paths(G, parse_id, root='0'):
    '''Find a path from the root to all leaves'''
    paths = []
    for node in G.nodes():
        if G.out_degree(node) == 0:
            # if there are two paths to the same node, only add one
            # if not nx.shortest_path(G, root, node) in paths: 
            #     path = nx.shortest_path(G, root, node)
            #     if len(path) > 1:
            #         path = path[1:]
            #     paths.append(path)
            paths.append(nx.shortest_path(G, root, node))
    path_element = []
    for path in paths:
        list_obj = []
        for i in range(len(path) - 1):
            # get elements that point to the next node
            elements = Element.get_elements_next_page(path[i], path[i + 1], parse_id)
            list_obj.append([path[i], elements])
        list_obj.append([path[-1], []])
        path_element.append(list_obj)
    return path_element


def clean_table():
    #  delete all from query, training, and query_element tables
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM query")
        cur.execute("DELETE FROM training")
        cur.execute("DELETE FROM query_element")
        cur.execute("UPDATE element SET context = NULL")
        conn.commit()


def add_query(module_id, paths):
    '''Alternative method'''
    query_type = 'software'
    path_id = 0
    with get_db_connection() as conn:
        cur = conn.cursor()
        for path in paths:
            prev_query_id = None
            for p in path:
                query_id = generate_id()
                element_id = p[1][0]['id'] if len(p[1]) > 0 else None
                cur.execute("SELECT query_id FROM query_element WHERE element_id = %s", (element_id,))
                query_element_match = cur.fetchone()
                if query_element_match is not None:
                    prev_query_id = query_element_match[0]
                else:
                    # check if page_id for this query already exists
                    query_element_id = generate_id()
                    cur.execute("INSERT INTO query (query_id, module_id, path_id, page_id, query, query_type, prev_query_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", (query_id, module_id, path_id, p[0], query_element_id, query_type, prev_query_id))
                    conn.commit()
                    for element in p[1]:
                        query_element_id = generate_id()
                        cur.execute("INSERT INTO query_element (query_element_id, query_id, element_id, element_type, form_id) VALUES (%s, %s, %s, %s, %s)", (query_element_id, query_id, element['id'], element['element_type'], element['form_id']))
                        conn.commit()
                    prev_query_id = query_id
            path_id += 1


def add_module_graph(parse_id, company_id):
    '''Create a new module'''
    module_id = generate_id()
    tool_id = 4
    access = 'private'
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT website_name, website_description FROM parse WHERE parse_id = %s", (parse_id,))
        website = cur.fetchone()
        cur.execute("INSERT INTO module (module_id, company_id, tool_id, module_title, module_description, access) VALUES (%s, %s, %s, %s, %s, %s)", (module_id, company_id, tool_id, website[0], website[1], access))
        # cur.execute("DELETE FROM parse WHERE parse_id = %s", (parse_id,))
        # cur.execute("DELETE FROM cookie WHERE cookie.page_id IN (SELECT page_id FROM page WHERE page.parse_id = %s)", (parse_id,))
        # cur.execute("DELETE FROM element_action WHERE element_action.element_id IN (SELECT id FROM element WHERE element.parse_id = %s)", (parse_id,))
        conn.commit()
    return module_id

        
def add_training_graph(module_id, company_id):
    '''Add sample training data'''
    team_id = company_id
    training_status = 'pending'
    training_type = 'software'
    # get data from query
    with get_db_connection() as conn:
        # check if training already exists
        cur = conn.cursor()
        cur.execute("SELECT * FROM training WHERE module_id = %s AND team_id = %s", (module_id, company_id))
        training = cur.fetchall()
        if training:
            cur.execute("""UPDATE training SET response=NULL, training_status=%s
                        WHERE team_id=%s AND module_id = %s""", ('pending', company_id, module_id))
            conn.commit()
        else:
            cur.execute("SELECT query_id FROM query WHERE module_id = %s", (module_id,))
            query_ids = cur.fetchall()
            for query_id in query_ids:
                training_id = generate_id()
                cur.execute("INSERT INTO training (training_id, team_id, module_id, query_id, training_status, training_type) VALUES (%s, %s, %s, %s, %s, %s)", (training_id, team_id, module_id, query_id[0], training_status, training_type))
                conn.commit()
