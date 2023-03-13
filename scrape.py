from utils import *
import time
from element import Element
from page import Page
from element import *
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException

import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout

from log import Log


class Parse:
    def __init__(self, input_type, url, software_name=None, company_id=None, description=None, add_to_db=False, id=None):
        self.id = id or generate_id()
        self.cur_page = None
        self.company_id = company_id
        self.url = url
        self.software_name = software_name
        self.description = description
        self.input_type = input_type
        Log.add_log('Parse initialized')
        if add_to_db:
            Parse.add_to_db(self)


    def get_pages(parse_id):
        '''Return a list of pages in the parse'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT page_id FROM page WHERE parse_id = %s", (parse_id,))
            pages = cur.fetchall()
            return pages


    def parse_page_count(self):
        '''Get the number of pages in the parse'''
        Log.add_log('Getting page count')
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM page WHERE parse_id = %s", (self.id,))
            count = cur.fetchone()
            return count[0]


    def get_page_id(self):
        return self.parse_page_count() + 1


    def get_parse(parse_id):
        '''Return a parse object from the database'''
        Log.add_log('Getting parse from database')
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM parse WHERE parse_id = %s", (parse_id,))
            parse = cur.fetchone()
            return Parse(parse['input_type'], parse['website_url'], company_id=parse['company_id'], id=parse['parse_id'], add_to_db=False)


    def add_to_db(self):
        '''Adds the parse to the database'''
        Log.add_log('Adding parse to database')
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO parse (company_id, parse_id, website_url, website_name, website_description, status, input_type) VALUES (%s, %s, %s, %s, %s, %s, %s)", (self.company_id, self.id, self.url, self.software_name, self.description, 'pending', self.input_type))
            conn.commit()


    def complete(self):
        '''Update parse in db set status to complete'''
        Log.add_log('Completing parse')
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE parse SET status = %s WHERE parse_id = %s', ('parsed', self.id))
            conn.commit()


    def set_current_page(self, page):
        Log.add_log('\tSetting current page to ' + str(page.page_id))
        self.cur_page = page


    def perform_action(self, driver, element, check_page_change=False):
        '''Performs the action associated with the element'''
        Log.add_log('\tPerforming action: ' + str(element))
        # scroll to element
        if element.type == 'button' and not element.form_id:
            Log.add_log('\t\tClicking Button')
            time.sleep(.3)
            btn = element.find_element(driver)
            Log.add_log('\t\t\tButton found,' + str(btn))
            # driver.execute_script("arguments[0].scrollIntoView();", btn)
            # btn.click()
            # if Page.check_if_scrollable(driver):
            try:
                if btn != None:
                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                    time.sleep(.5)
                    if btn.tag_name == 'a' or btn.tag_name == 'button' or btn.tag_name == 'input':
                        btn.click()
                    else:
                        # find clickable element inside of btn (a, button, input)
                        clickable = btn.find_elements(By.XPATH, './/a|.//button|.//input')[0]
                        Log.add_log('\t\t\tClickable element found: ' + str(clickable))
                        Log.add_log('\t\t\t' + clickable.get_attribute('outerHTML'))
                        driver.execute_script("arguments[0].scrollIntoView();", clickable)
                        time.sleep(.5)
                        clickable.click()
                else:
                    Log.add_log('\t\t\tButton not found')
                    return False, [], driver
            except ElementNotInteractableException as e:
                Log.add_log('\t\t\tButton not interactable' + str(e))
                Log.add_log('\t\t\t' + btn.get_attribute('outerHTML'))

                return False, [], driver
            elements = [element]
        elif element.form_id != None:
            Log.add_log('\t\tSubmitting Form')
            # get all input elements for the form
            elements = Webform.get_elements(element.form_id)
            for e in elements:
                if e.type == 'input' or e.type == 'select':
                    # add something here
                    if not e.has_value():
                        Log.add_log('\t\t\tIncomplete input')
                        return 'incomplete_input', [], driver

                    sample_input = e.get_input_values()
                    input_field = e.find_element(driver)
                    driver.execute_script("arguments[0].scrollIntoView();", input_field)
                    # if input_field has an outer tag that is not an input, get the input tag
                    time.sleep(.3)
                    if e.type == 'input':
                        if input_field.tag_name != 'input':
                            input_field = input_field.find_element(By.XPATH, './/input')
                        if input_field.get_attribute('type') == 'checkbox':
                            if sample_input == 'on':
                                input_field.click()
                        else: 
                            input_field.clear()
                            input_field.send_keys(sample_input)
                    elif e.type == 'select':
                        options = input_field.find_elements(By.XPATH, './/option')
                        for option in options:
                            if option.get_attribute("value") == sample_input:
                                option.click()

            button = [e for e in elements if e.type == 'button']
            if len(button) == 0:
                input_field.submit()
            else:
                button[0].find_element(driver).click()
            time.sleep(.3)
        return True, elements, driver


    def get_status(self):
        '''Returns the status of the parse'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT status FROM parse WHERE parse_id = %s", (self.id,))
            status = cur.fetchone()
            return status[0]


    def traverse_to_state_change_root(self, driver, element, parse_id):
        '''Traverses to the root of the state change tree'''
        cur_page = self.cur_page
        source_page = Page.get_page(element.page_id, parse_id)
        if cur_page.page_id != element.page_id:
            if source_page.source_element_id and Element.element_has_action(source_page.source_element_id,'state_change'):
                Log.add_log('\t\tTraversing to state change root')
                Log.add_log('\t\t\tCurrent page: ' + str(cur_page.page_id))
                Log.add_log('\t\t\tSource page: ' + str(source_page.page_id))

                traverse_elements = []
                traverse_page = source_page
                while traverse_page.source_element_id and Element.element_has_action(traverse_page.source_element_id,'state_change'):
                    Log.add_log('\t\t\tTraversing up to: ' + str(traverse_page.page_id))
                    traverse_elements.append(Element.get_element(traverse_page.source_element_id))
                    traverse_page = traverse_page.get_source_element_page()

                # get the page we need to go to
                cur_page = traverse_page
                driver.get(cur_page.url)
                
                while cur_page.page_id != source_page.page_id:
                    visit_element = traverse_elements.pop()
                    Log.add_log('\t\t\tTraversing down to: ' + str(visit_element.page_id))
                    cur_page = Page.get_page(visit_element.get_to_page_id(), parse_id)
                    try:
                        time.sleep(.3)
                        driver.delete_all_cookies()
                        visit_page = Page.get_page(visit_element.page_id, parse_id)
                        for cookie in visit_page.cookies:
                            driver.add_cookie(dict(cookie))
                        self.perform_action(driver, visit_element)
                    except Exception as e:
                        Log.add_log('\t\t\t\tFailed to click element: ' + str(e))
                        # Log.
                        return False, driver, cur_page
            else:
                # navigate to the page of the element
                Log.add_log('\tDirectly go to page')
                driver.delete_all_cookies()
                for cookie in source_page.cookies:
                    driver.add_cookie(dict(cookie))
                driver.get(Page.get_url(element.page_id))
                time.sleep(.3)
        return True, driver, cur_page


    def get_screenshots(parse_id):
        '''Get all the screenshots for a parse'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT page_id FROM page WHERE parse_id = %s", (parse_id,))
            pages = cur.fetchall()
            screenshots = []
            for page in pages:
                cur.execute("SELECT * FROM screenshot WHERE node_id = %s and parse_id=%s ORDER BY img_counter ASC", (page['page_id'],parse_id))
                screenshot = cur.fetchall()
                screenshots.append([dict(s) for s in screenshot])

            return screenshots



        
