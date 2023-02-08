from classes import *
from utils import *

def get_tools():
    '''Get all tools from the database.'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT tool_id, tool_name, tool_icon, status FROM tools ORDER BY status asc, tool_name asc")
        tools = cur.fetchall()
        tools_list = []
        if tools != None:
            for tool in tools:
                tools_list.append(Tool(id=tool[0], name=tool[1], icon=tool[2], status=tool[3]))
    return tools_list


def get_public_modules(tool_id):
    '''Get all public modules for a tool.'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT module_id, module_title, module_description FROM module WHERE tool_id = %s AND access = 'public' ORDER BY module_title asc", (tool_id,))
        modules = cur.fetchall()
        modules_list = []
        if modules != None:
            for module in modules:
                modules_list.append(Module(id=module[0], name=module[1], description=module[2]))
    return modules_list