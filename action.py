from utils import *
from page import Page
from log import Log

class Action:
    def __init__(self, action_type, page_id, element_id, to_page_id, cookies_added=None, cookies_removed=None, cookies_changed=None):
        self.type = action_type
        self.id = generate_id()
        self.page_id = page_id
        self.element_id = element_id
        self.to_page_id = to_page_id
        self.cookies_added = cookies_added
        self.cookies_removed = cookies_removed
        self.cookies_changed = cookies_changed
        self.add_action_to_db()

    def get_type(self):
        return self.type


    def add_action_to_db(self):
        '''Add the action to the database'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO element_action (id, element_id, action_type, to_page_id, page_id) VALUES (%s, %s, %s, %s, %s)', (self.id, self.element_id, self.type, self.to_page_id, self.page_id))
            conn.commit()


    def get_page_id(self):
        '''Returns the page id of the action'''
        return self.page_id


    # def get_actions(cur_link, cur_page_hash, new_link, new_page_hash, page_id, element_id, to_page_id, cur_cookies, new_cookies):
    def get_actions(driver, cur_page, next_page, element, parse_id, actions=None):
        '''Returns a list of actions that can be performed on the element'''
        cur_link = cur_page.url
        new_link = next_page.url
        
        page_id = cur_page.page_id
        element_id = element.id
        to_page_id = next_page.page_id

        cur_cookies = cur_page.cookies
        new_cookies = next_page.cookies

        if not actions:
            actions = []
            if cur_link == new_link:
                actions.append('state_change')
            elif cur_link != new_link:
                actions.append('redirect')


        # detect cookie change
        actions = [Action(action, page_id, element_id, to_page_id) for action in actions]
        added, removed, changed = Action.cookie_changes(cur_cookies, new_cookies)
        # print(added, removed, changed)
        if len(added) + len(removed) + len(changed) > 0:
            actions.append(Action('cookie_change', page_id, element_id, to_page_id, added, removed, changed))

        return actions


    def delete_actions_db(id):
        Log.add_log('\tDeleting actions for element ' + str(id))
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM element_action WHERE element_id = %s', (id,))
            cur.execute('DELETE FROM element WHERE id = %s', (id,))
            conn.commit()



    def cookie_changes(cur_cookies, new_cookies):
        '''Returns a list of cookies that have been added, removed, or changed'''
        added = []
        removed = []
        changed = []

        cur_cookies = {cookie['name']: cookie['value'] for cookie in cur_cookies}
        new_cookies = {cookie['name']: cookie['value'] for cookie in new_cookies}


        for cookie in cur_cookies.keys():
            if cookie not in new_cookies.keys():
                removed.append(cookie)

        for cookie in new_cookies.keys():
            if cookie not in cur_cookies.keys():
                added.append(cookie)
            elif cookie in cur_cookies.keys() and new_cookies[cookie] != cur_cookies[cookie]:
                changed.append(cookie)

        return added, removed, changed
