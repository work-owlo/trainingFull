from utils import *
import io
import os
import PIL.Image as Image
import time
import numpy as np
import cv2
from element import *
import botocore
from configs import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


class Page: 
    def __init__(self, source_element_id=None, url=None, cookies=None, driver=None, parse_id=None, add_to_db=True, id=None):
        self.hash = 1
        self.parse_id = parse_id
        self.url = url or driver.current_url
        self.page_id = str(id)
        self.cookies = cookies
        self.source_element_id = source_element_id
        self.screenshot = None

        
        if add_to_db:
            self.add_page()
            self.cookies = self.save_cookies(driver.get_cookies())
            self.get_screenshots(driver)
        

    def save_cookies(self, cookies):
        '''Save cookies to db'''
        with get_db_connection() as conn:
            for cookie in cookies:
                cur = conn.cursor()
                cur.execute('INSERT INTO cookie (page_id, cookie_name, cookie_value, parse_id) VALUES (%s, %s, %s, %s)', (self.page_id, cookie['name'], cookie['value'], self.parse_id))
                conn.commit()
        return cookies


    def get_all_same_pngs(page_id, parse_id):
        '''get all pngs from static folder'''
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT screenshot_name FROM screenshot WHERE node_id = %s AND parse_id = %s', (page_id, parse_id))
            files = cur.fetchone()
        if files:
            return files['screenshot_name']
        else:
            return None


    def read_screenshot(filename):
        '''Read screenshot from Wasabi '''
        # get file from static folder
        bucket = 'owlo'
        try:
            obj = wasabi.Object(bucket, filename)
            file_content = obj.get()['Body'].read()
            
            return np.frombuffer(file_content, np.uint8)
        except Exception as e:
            print("Error reading file: ", e)


    def get_mse_between_images(self, img2):
        # get files in Wasabi bucket and read as CV2 image
        img1 = cv2.imdecode(np.frombuffer(self.screenshot, np.uint8), cv2.IMREAD_COLOR)
        # save image to static folder
        # img1 = cv2.imdecode(self.screenshot, cv2.IMREAD_COLOR)
        Log.add_log('\tComparing to ' + str(img2))
        img2 = cv2.imdecode(Page.read_screenshot(img2), cv2.IMREAD_COLOR)
        # img2 = cv2.imread('images/' + img2, cv2.IMREAD_COLOR)
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        # if sizes are different, return 1
        if img1.shape != img2.shape:
            return 1
        h, w = img1.shape[:2]
        diff = cv2.subtract(img1, img2)
        err = np.sum(diff**2)
        mse1 = err/(float(h*w))

        # swap images and try again
        diff = cv2.subtract(img2, img1)
        err = np.sum(diff**2)
        mse2 = err/(float(h*w))
        Log.add_log('\tMSE1: ' + str(mse1))
        Log.add_log('\tMSE2: ' + str(mse2))
        return max(mse1, mse2)
    

    def identical_pages(self, next_page_id):
        # get all pngs from wasabi folder that contain cur_page_id
        parse_id = self.parse_id
        # get all pngs from wasabi folder that contain next_page_id
        next_page = Page.get_all_same_pngs(next_page_id, parse_id)
        mse = self.get_mse_between_images(next_page)
        Log.add_log('\tMSE: ' + str(mse))
        if mse > 0.0001:
            return False
        return True 


    def get_all_other_page_ids(page_id, parse_id):
        '''get all page ids from db'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            page_id = str(page_id)
            cur.execute("SELECT node_id FROM screenshot WHERE node_id::text != %s AND parse_id = %s", (page_id, parse_id))
            return cur.fetchall()
        

    def page_visited(self):
        # Compare screenshots to see if page has been visited
        Log.add_log('\tChecking if page has been visited')
        page_id = self.page_id
        prev_pages = Page.get_all_other_page_ids(page_id, self.parse_id)
        for p in prev_pages:
            Log.add_log('\tComparing to ' + str(p[0]))
            if self.identical_pages(p[0]):
                Log.add_log('\tIdentical pages found ' + str(page_id) + ' ' + str(p[0]))
                Page.delete_page(page_id, self.parse_id)
                return p[0]
        return -1


    def delete_page(page_id, parse_id):
        # delete page from db
        with get_db_connection() as conn:
            cur = conn.cursor()
            page_id = str(page_id)
            cur.execute('DELETE FROM page WHERE page_id = %s', (page_id,))
            conn.commit()
            Page.delete_screenshots(page_id, parse_id)


    def delete_screenshots(page_id, parse_id):
        # delete from wasabi files any screenshots that contain page_id in the filename
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT screenshot_name FROM screenshot WHERE node_id = %s and parse_id = %s', (page_id, parse_id))
            file_names = cur.fetchall()

        for file in file_names:
            Page.delete_screenshot(file[0])
                    
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM screenshot WHERE node_id = %s and parse_id = %s', (page_id, parse_id))
            conn.commit()


    def get_source_element(self):
        return self.source_element    


    def add_page(self):
        # add page to db and return new page id
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('INSERT INTO page (page_id, page_hash, page_url, parse_id, source_element_id) VALUES (%s, %s, %s, %s, %s)', (self.page_id, self.hash, self.url, self.parse_id, self.source_element_id))
            conn.commit()


    def get_url(page_id):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT page_url FROM page WHERE page_id = %s', (page_id,))
            page = cur.fetchone()
            return page[0]


    def get_pages():
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM page')
            pages = cur.fetchall()
            return pages


    def get_source_element_page(self):
        '''Get page id from db'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('''SELECT element.page_id 
                                    FROM element
                                    WHERE id = %s''', (self.source_element_id,))
            page = cur.fetchone()
            if page is None:
                return None
            return Page.get_page(page[0], self.parse_id)


    def get_page(page_id, parse_id):
        '''Get page from db as a Page object'''
        page_id = str(page_id)
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM page WHERE page_id = %s AND parse_id = %s", (page_id, parse_id))
            page = cur.fetchone()
            cur.execute("SELECT cookie_name as name, cookie_value as value FROM cookie WHERE page_id = %s and parse_id = %s", (page_id, parse_id))
            cookies = cur.fetchall()
            return Page(id=page['page_id'], url=page['page_url'], parse_id=page['parse_id'], cookies=cookies, source_element_id=page['source_element_id'], add_to_db=False)


    def save_screenshot(self):
        
        # save self.screenshot in static folder
        img_name = str(self.page_id) + 'screenshot' + str(self.parse_id) + '.png'
        Page.insert_screenshot_into_db(0, self.page_id, img_name, 0, 0, 0, self.parse_id)
        bucket_name = 'owlo'
        try:
            # upload file to wasabi as a bytes object
            my_bucket = wasabi.Bucket('owlo')
            my_bucket.upload_fileobj(io.BytesIO(self.screenshot), img_name)
            print("File uploaded successfully!")
        except botocore.exceptions.ClientError as e:
            print("Error uploading file: ", e)

    
    def delete_screenshot(screenshot_name):
        bucket_name = 'owlo'
        try:
            # delete file from wasabi
            wasabi.Object(bucket_name, screenshot_name).delete()
            print("File deleted successfully!")
        except botocore.exceptions.ClientError as e:
            print("Error deleting file: ", e)


    def insert_screenshot_into_db(img_counter, node_id, screenshot_name, y, height, window_height, parse_id):
        '''Inserts a screenshot into the database'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if (height - y) < window_height and height > window_height:
                y = height % window_height
            cur.execute('INSERT INTO screenshot (img_counter, node_id, screenshot_name, y, parse_id) VALUES (%s, %s, %s, %s, %s)', (img_counter, node_id, screenshot_name, y, parse_id))
            conn.commit()


    def check_if_scrollable(driver):
        '''Checks if the page is scrollable'''
        screenshot = driver.get_screenshot_as_png()
        actions = ActionChains(driver)
        actions.send_keys(Keys.PAGE_DOWN)
        time.sleep(.5)
        actions.perform()
        screenshot2 = driver.get_screenshot_as_png()
        driver.execute_script("window.scrollTo(0, 0);")
        # unfocus any focused elements
        driver.execute_script("document.activeElement.blur();")
        if len(screenshot) != len(screenshot2):
            return True
        Log.add_log('\tChecking if scrollable: ' + str(screenshot != screenshot2))
        return screenshot != screenshot2
            

    def get_screenshots(self, driver):
        '''Takes screenshots of the page and saves them in the wasabi bucket'''
                # print focused elements
        driver.execute_script("window.scrollTo(0, 0);")
        height = driver.execute_script("return document.documentElement.scrollHeight")
        window_height = driver.execute_script("return Math.max(window.innerHeight, document.documentElement.clientHeight);")
        screenshot_y = 0
        screenshot = None
        if not Page.check_if_scrollable(driver):
            Log.add_log('\tPage is not scrollable')
            time.sleep(.5)
            screenshot = driver.get_screenshot_as_png()
            screenshot = np.array(Image.open(io.BytesIO(screenshot)))
        else:
            Log.add_log('\tPage is scrollable')
            for h in range(max(height // window_height,1)):
                driver.execute_script("window.scrollTo(0, " + str(screenshot_y) + ");")
                # print any focused elements
                focused_elements = driver.find_elements(By.XPATH, "//*[@focused='true']")
                for element in focused_elements:
                    print(element.get_attribute('id'))
                time.sleep(.5)
                while not self.is_page_scrolled(driver, screenshot_y):
                    time.sleep(.5)
                append_screenshot = driver.get_screenshot_as_png()
                
                if screenshot is None:
                    screenshot = np.array(Image.open(io.BytesIO(append_screenshot)))
                else:
                    append = np.array(Image.open(io.BytesIO(append_screenshot)))
                    screenshot = np.vstack((screenshot, append))
                
                screenshot_y = (h + 1) * window_height

            remaining_height = height%window_height
            if remaining_height > 0:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight+1000);")
                time.sleep(.5)
                append_screenshot = driver.get_screenshot_as_png()
                append = np.array(Image.open(io.BytesIO(append_screenshot)))
                offset = driver.execute_script("return window.pageYOffset;")
                
                # crop the screenshot so that it only contains the remaining part of the page
                ratio = append.shape[0] / window_height
                append = append[int((800-remaining_height) * ratio):, :, :]

                screenshot = np.concatenate((screenshot, append), axis=0)

        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        screenshot = cv2.imencode('.png', screenshot)[1].tostring()
        self.screenshot = screenshot
        driver.execute_script("window.scrollTo(0, 0);")

    def is_page_scrolled(self, driver, screenshot_y):
        '''Checks whether the page has finished scrolling to the specified position'''
        return driver.execute_script("return window.pageYOffset;") >= screenshot_y - 10




    def get_page_elements(page_id, parse_id):
        '''Return a list of elements and the screenshots related to the page'''
        # images, buttons, inputs, forms = [], [], [], []
        with get_db_connection() as conn:
            '''Get all images'''
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('''SELECT screenshot_name, img_counter, y 
                                    FROM screenshot WHERE node_id = %s and parse_id = %s ORDER BY img_counter ASC''', (page_id, parse_id))
            images = cur.fetchall()
            '''Get all buttons'''
            cur.execute('''SELECT distinct element.context, element.id, element_value as button_text, width, height, x, y, element_action.to_page_id
                                    FROM element, element_action WHERE element.page_id = %s AND parse_id = %s AND element.id = element_action.element_id
                                    AND form_id is Null and element_type = 'button'
                                    ORDER BY element.id ASC''', (page_id, parse_id))
            buttons = cur.fetchall()
            buttons = [dict(b) for b in buttons]
            '''Get all inputs'''
            cur.execute('''SELECT distinct input_value as input_value, element.context, element_subtype as type, element.id, element_value as value, placeholder as placeholder, width, height, x, y, element_action.to_page_id
                                    FROM element, element_action, input
                                    WHERE element.page_id = %s AND parse_id = %s AND element.id = element_action.element_id AND element.id = input.element_id   
                                    AND form_id is Null and element_type = 'input'
                                    ORDER BY element.id ASC''', (page_id, parse_id))
            inputs = cur.fetchall()
            inputs = [dict(i) for i in inputs]
            '''Get forms'''
            cur.execute('''SELECT form_id as id FROM form WHERE page_id = %s AND parse_id = %s ORDER BY form_id ASC''', (page_id, parse_id))
            forms = cur.fetchall()
            form_list = []
            for form in forms:
                form_dict = {}
                cur.execute('''SELECT element_action.to_page_id as action FROM element, element_action WHERE element.page_id = %s AND element.id = element_action.element_id
                                                    AND form_id = %s''', (page_id, form['id']))
                action = cur.fetchone()
                
                if action is not None:
                    form_dict['action'] = action['action']
                else:
                    form_dict['action'] = None

                cur.execute('''SELECT Distinct input_value as input_value, element.context, element_subtype as type, element.id, element_value as value, placeholder, width, height, x, y, element_action.to_page_id as next
                                            FROM element, element_action, input
                                            WHERE element.page_id = %s AND element.id = element_action.element_id AND element.id = input.element_id
                                            AND form_id = %s and element_type = 'input' 
                                            ORDER BY element.id ASC''', (page_id, form['id']))
                input_form = cur.fetchall()
                form_dict['inputs'] = [dict(i) for i in input_form]
                
                cur.execute('''SELECT Distinct element.context, element.id, element_value as button_text, width, height, x, y, element_action.to_page_id
                                                                FROM element, element_action WHERE element.page_id = %s AND element.id = element_action.element_id
                                                                AND form_id = %s and element_type = 'button'
                                                                ORDER BY element.id ASC''', (page_id, form['id']))
                button_form = cur.fetchall()
                form_dict['buttons'] = [dict(b) for b in button_form]
                form_list.append(form_dict) 

        return images, buttons, inputs, form_list


    def add_elements(self, driver, parse_id):
        self.elements = Element.get_elements(driver, self.page_id, self.url, parse_id=parse_id)
        # self.forms = Webform.get_forms(driver, self.page_id, self.url, parse_id=parse_id)
