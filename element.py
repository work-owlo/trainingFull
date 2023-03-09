from utils import *
from log import Log
import openai
import re
import time
from selenium.webdriver.support.ui import Select

class Element:
    def __init__(self, x, y, width, height, context, page_id, element_type, value=None, id=None, sub_type = None, form_id=None, add_to_db=True, id_val = None, placeholder = None, name = None, outer_html = None, parse_id=None):
        self.x = x
        self.y = y
        self.parse_id = parse_id
        self.width = width
        self.height = height
        self.context = context
        self.to_page = None
        self.page_id = page_id
        self.form_id = form_id
        self.value = value
        self.type = element_type
        self.subtype = sub_type
        self.id = id
        self.id_val = id_val
        self.placeholder = placeholder
        self.name = name
        self.outer_html = outer_html
        if add_to_db:
            self.id = generate_id()
            self.add_element_to_db()


    def get_element(element_id):
        '''Returns an element object from the database'''
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM element WHERE id = %s', (element_id,))
            element = cur.fetchone()
            return Element(element['x'], element['y'], element['width'], element['height'], element['context'], element['page_id'], element['element_type'], value=element['element_value'], id=element['id'], sub_type=element['element_subtype'], form_id=element['form_id'], id_val=element['id_val'], placeholder=element['placeholder'], name=element['element_name'], outer_html=element['outerhtml'], parse_id=element['parse_id'], add_to_db=False)


    def delete_self(self, reason):
        Log.add_log('\tDeleting element for reason: ' + reason)
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE element SET deleted = %s WHERE id = %s', (reason, self.id,))
            conn.commit()


    def add_element_to_db(self):
        Log.add_log('\tAdding element ' + str(self.id) + ' with value ' + str(self.value) + ' to db')
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO element (id, page_id, to_page_id, form_id, element_value, element_type, element_subtype, width, height, x, y, id_val, placeholder, element_name, outerhtml, parse_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (self.id, self.page_id, self.to_page, self.form_id, self.value, self.type, self.subtype, self.width, self.height, self.x, self.y, self.id_val, self.placeholder, self.name, self.outer_html, self.parse_id))
            conn.commit()


    def get_to_page_id(self):
        Log.add_log('\tGetting to page id for element ' + str(self.id))
        actions = self.get_actions()
        if len(actions) > 0:
            return actions[0]['to_page_id']
        return None


    def get_actions(self):
        Log.add_log('\tGetting actions for element ' + str(self.id))
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM element_action WHERE element_id = %s', (self.id,))
            actions = cur.fetchall()
            return actions


    def get_page_id(self):
        Log.add_log('\tGetting page id for element ' + str(self.id))
        return self.page_id


    def get_page_id(self):
        Log.add_log('\tGetting page id for element ' + str(self.id))
        return self.page_id


    def contains_action(self, action):
        Log.add_log('\tChecking if element ' + str(self.id) + ' contains action ' + str(action))
        for a in self.get_actions():
            if a['type'] == action:
                return True
        return False


    def element_has_action(element_id, action):
        Log.add_log('\tChecking if element ' + str(element_id) + ' has action ' + str(action))
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM element_action WHERE element_id = %s AND action_type = %s', (element_id, action))
            count = cur.fetchone()[0]
            return count > 0


    def get_actions_db(element_id):
        Log.add_log('\tGetting actions for element ' + str(element_id))
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM element_action WHERE element_id = %s', (element_id,))
            actions = cur.fetchall()
            return actions


    def get_real_actions_db(element_id):
        Log.add_log('\tGetting real actions for element ' + str(element_id))
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""SELECT * 
            FROM element_action 
            WHERE element_id = %s 
            and action_type != 'existing'""", (element_id,))
            actions = cur.fetchall()
            return actions


    def get_elements(driver, page_id, url, parse_id):
        '''Get all the elements on the page'''
        buttons = Button.get_buttons(driver, page_id, url, parse_id=parse_id)
        # inputs = Input.get_inputs(driver, page_id)

        return buttons # + inputs
        

    def find_element(self, driver):
        '''Find the element on the page'''
        Log.add_log('\tFinding element at ' + str(self.x) + ', ' + str(self.y))

        x = self.x
        y = self.y
        width = self.width
        height = self.height
        
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(.5)
        elements = driver.find_elements("xpath", '//*')
        for element in elements:  
            if element.location['x'] == x and element.location['y'] == y and element.size['width'] == width and element.size['height'] == height:
                Log.add_log('\tFound element at ' + str(x) + ', ' + str(y))
                if element.get_attribute("target") and element.get_attribute("target") == "_blank":
                    driver.execute_script("arguments[0].setAttribute('target', '_self')", element)
                return element
            
        # scroll driver to top
        Log.add_log('\tCould not find element at ' + str(x) + ', ' + str(y) + ' height ' + str(height) + ' width ' + str(width))
        # TAKE SCREENSHOT HERE
        return None


    def find_element_self(self, driver):
        '''Find the element at the given coordinates'''
        elements = driver.find_elements("xpath", '//*')
        for element in elements:
            if element.location['x'] == self.x and element.location['y'] == self.y:
                if element.get_attribute("value") and element.get_attribute("value") == self.value:
                    return element
                elif not element.get_attribute("value"):
                    return element
        return None


    def get_all_elements(parse_id):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            elements = cur.execute('SELECT * FROM element WHERE parse_id=%s', (parse_id,))
            elements = cur.fetchall()
            return elements


    def set_type(self, type):
        Log.add_log('\tSetting type for element ' + str(self.id) + ' to ' + str(type))
        self.type = type
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE element SET element_type = %s WHERE id = %s', (self.type, self.id))
            conn.commit()


    def set_subtype(self, subtype):
        Log.add_log('\tSetting subtype for element ' + str(self.id) + ' to ' + str(subtype))
        self.subtype = subtype
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE element SET element_subtype = %s WHERE id = %s', (self.subtype, self.id))
            conn.commit()

    
    def get_next_element(parse_id):
        # get the last element added to db order by created desc
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM element AS e WHERE parse_id = %s AND NOT EXISTS (SELECT element_id FROM element_action WHERE element_id = e.id AND parse_id = %s) AND deleted IS NULL ORDER BY page_id::INTEGER DESC, form_id ASC, element_value, x, y LIMIT 1", (parse_id, parse_id))
            element = cur.fetchone()
            if element is not None:
                if element['element_type'] == 'button':
                    Log.add_log('\tFound next element ' + str(element['id']) + ' value: ' + str(element['element_value'] + ' on page ' + element['page_id']))
                    return Button(element['x'], element['y'], element['width'], element['height'], element['context'], element['page_id'], element['element_type'], element['element_value'], element['element_subtype'], element['form_id'], add_to_db=False, id=element['id'], id_val=element['id_val'])
                elif element['element_type'] == 'input':
                    Log.add_log('\tFound next element ' + str(element['id']) + ' value: ' + str(element['element_value'] + ' on page ' + element['page_id']))
                    return Input(element['x'], element['y'], element['width'], element['height'], element['context'], element['page_id'], element['element_type'], element['element_value'], element['element_subtype'], element['form_id'], add_to_db=False, id=element['id'], id_val=element['id_val'])
            Log.add_log('\t No next element found')
            return None

    
    def has_next_element(parse_id):
        Log.add_log('\nChecking if there is a next element')
        return Element.get_next_element(parse_id) is not None

    
    def add_context(element_id):
        '''Generates context using the GPT-3 model'''
        # get outer_html of element
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT context, outerhtml FROM element WHERE id = %s', (element_id,))
            element = cur.fetchone()
            context = element['context']
            outer_html = element['outerhtml']
            
            if not context or context is None:
                context = Element.generate_context(outer_html)
                cur.execute('UPDATE element SET context = %s WHERE id = %s', (context, element_id))
            conn.commit()


    def generate_context(outer_html):
        print('OPenai credits vrooom')
        prompt = 'Starting from the verb, in one phrase describe what action this block allows me to do. \n\n'
        prompt +=  outer_html

        model = "text-davinci-003"

        response = openai.Completion.create(
            engine=model,
            prompt=prompt,
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.7,
        )

        response = response.choices[0].text
        # remove quotes from response
        response = response.replace('"', '')

        return response


    def generate_sample(self):
        '''Generates a sample using the GPT-3 model'''
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT outerhtml FROM element WHERE id = %s', (self.id,))
            element = cur.fetchone()
            prompt = 'Give me one sample input that I can feed into this input. Only give the input'
            prompt += element['outerhtml']
            
            print(prompt)
            model = "text-davinci-003"

            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=10,
                n=1,
                stop=None,
                temperature=0.7,
            )

            return response.choices[0].text


    def get_elements_next_page(page_id, next_page_id, parse_id):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM element WHERE page_id = %s AND EXISTS (SELECT element_id FROM element_action WHERE element_id = element.id AND to_page_id = %s AND parse_id=%s) AND parse_id=%s', (page_id, next_page_id, parse_id, parse_id))
            elements = cur.fetchall()
            return elements


class Button(Element):
    def __init__(self, x, y, width, height, context, page_id, element_type, value=None, sub_type=None, form_id=None, add_to_db=True, id=None, id_val = None, outer_html=None, parse_id=None):
        super().__init__(x, y, width, height, context, page_id, element_type, value, sub_type=sub_type, form_id=form_id, add_to_db=add_to_db, id=id, id_val=id_val, outer_html=outer_html, parse_id=parse_id)


    def get_buttons(driver, page_id, url, form_id=None, add_to_db=True, parse_id=None):
        buttons = []
        if form_id == None:
            buttons = driver.find_elements("xpath", '//button[not(ancestor::form)]')
            a_tag = driver.find_elements("xpath", '//a')
            input = driver.find_elements("xpath", '//input[@type="submit"][not(ancestor::form)]')
            role_buttons = driver.find_elements("xpath", '//*[@role="button"][not(ancestor::form)]')
            buttons = buttons + a_tag + role_buttons + input
        else:
            buttons = driver.find_elements("xpath", './/button[ancestor::form]')
            inputs = driver.find_elements("xpath", './/input[@type="submit"][ancestor::form]')
            buttons = buttons + inputs

        # remove buttons that include "Sign Out"
        buttons = [button for button in buttons if "Sign Out" not in button.text]
        buttons = [button for button in buttons if button.is_displayed()]

        # order buttons based on x, y, and value
        buttons = sorted(buttons, key=lambda button: (button.location['x'], button.location['y'], button.size['width'], button.size['height'], button.text))

        button_objects = []

        for button in buttons:
            if button.get_attribute("href") is None or (button.get_attribute("href") is not None):
                value = button.text
                outer_html = button.get_attribute("outerHTML")
                # remove any svgs from the outer html
                outer_html = re.sub(r'<svg.*%ssvg>', '', outer_html)
                # remove spaces
                outer_html = re.sub(r'\s+', ' ', outer_html)
                context = ''
                x = button.location['x']
                y = button.location['y']
                width = button.size['width']
                height = button.size['height'] 
                id_val = button.get_attribute("id")
                
                button_objects.append(Button(x, y, width, height, context, page_id, 'button', form_id=form_id, value=value, add_to_db=True, id_val=id_val, outer_html=outer_html, parse_id=parse_id))
        return button_objects


    def valid_url(url, new_url):
        if url[:8] == 'https://':
            url = url[8:]
        url = url[0:url.find('/')]
        return url in new_url


class Input(Element):
    def __init__(self, x, y, width, height, context, page_id, element_type, value=None, sub_type=None, form_id=None, add_to_db=True, id=None, id_val = None, name=None, placeholder=None, outer_html=None, parse_id=None):
        super().__init__(x, y, width, height, context, page_id, element_type, value, sub_type=sub_type, form_id=form_id, add_to_db=add_to_db, id=id, id_val=id_val, name=name, placeholder=placeholder, outer_html=outer_html, parse_id=parse_id)


    def get_inputs(driver, page_id, form_id=None, add_to_db=False, parse_id=None):
        Input.get_selects(driver, page_id, form_id=form_id, add_to_db=add_to_db, parse_id=parse_id)

        # driver, page_id, form_id=None, add_to_db=False):
        inputs = driver.find_elements("xpath", './/input')
        txt_area = driver.find_elements("xpath", './/textarea')
        inputs = inputs + txt_area
        inputs = [input for input in inputs if input.is_displayed()]

        # order inputs based on x, y, and value
        inputs = sorted(inputs, key=lambda x: (x.location['x'], x.location['y'], x.get_attribute("value")))
        input_objects = []

        for input in inputs:
            value = input.get_attribute("value")
            outer_html = input.get_attribute("outerHTML")
            outer_html = re.sub(r'<svg.*%ssvg>', '', outer_html)
            # remove spaces
            outer_html = re.sub(r'\s+', ' ', outer_html)
            context = None
            x = input.location['x']
            y = input.location['y']
            width = input.size['width']
            height = input.size['height'] 
            sub_type = input.get_attribute("type")
            id_val = input.get_attribute("id")
            placeholder = input.get_attribute("placeholder")
            name = input.get_attribute("name")
            input_objects.append(Input(x, y, width, height, context, page_id, 'input', placeholder=placeholder, name=name, value=value, sub_type=sub_type, form_id=form_id, add_to_db=add_to_db, id_val=id_val, outer_html=outer_html, parse_id=parse_id))

        # Log.add_log('\tGetting Inputs \n \t Found ' + str(len(input_objects)) + ' inputs')
        return input_objects


    def has_value(self):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""SELECT generated_value FROM element WHERE id = %s AND generated_value IS NOT NULL""", (self.id,))
            element = cur.fetchone()
            Log.add_log('\tChecking if input has value')
            if element is not None:
                Log.add_log('\t\t' + str(element[0]))
            else:
                Log.add_log('\t\tNo value')
            return element is not None


    def get_input_values(self):
        '''Get input from database'''
        Log.add_log('\tGetting input from database')
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""SELECT generated_value FROM element WHERE id = %s""", (self.id,))
            element = cur.fetchone()
            return element[0]


    def get_user_input(self):
        '''Ask user for input to a field'''
        Log.add_log('\tGetting user input for input')
        if self.value is not None and self.value != '':
            input_val = self.value
        
        if self.subtype is None or self.subtype == '':
            input_val= input('Enter input: ')

        
        if self.subtype ==  'text':
            input_val = input('Enter text: ')
        if self.subtype ==  'password':
            input_val = input('Enter password: ')
        if self.subtype ==  'email':
            input_val = input('Enter email: ')
        if self.subtype ==  'tel':
            input_val = input('Enter phone number: ')
        if self.subtype ==  'number':
            input_val = input('Enter number: ')
        if self.subtype ==  'date':
            input_val = input('Enter date: ')
        if self.subtype ==  'time':
            input_val = input('Enter time: ')
        if self.subtype ==  'datetime-local':
            input_val = input('Enter date and time: ')
        if self.subtype ==  'month':
            input_val = input('Enter month: ')
        if self.subtype ==  'week':
            input_val = input('Enter week: ')
        if self.subtype ==  'url':
            input_val = input('Enter url: ')

        self.save_input(input_val, 'user')
        return input_val


    def save_input(self, val, generated_by=None):
        '''Save input to database'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE element SET generated_value = %s WHERE id = %s', (val, self.id))
        

    def get_ai_input(self):
        '''Return a sample input for input based on input type'''
        Log.add_log('\tGetting sample input for input')
        if self.value is not None and self.value != '':
            input_val = self.value
        if self.subtype is None or self.subtype == '':
            input_val = 'sample input'
        input_val = {
            'text': 'sample text',
            'password': 'sample password',
            'email': 'sample@owlo.co',
            'tel': '1234567890',
            'number': '1234567890',
            'date': '2020-01-01',
            'time': '12:00',
            'datetime-local': '2020-01-01T12:00',
            'month': '2020-01',
            'week': '2020-W01',
            'url': 'https://owlo.co',
        }[self.subtype]
        self.save_input(input_val, 'ai')
        return input_val


    def get_selects(driver, page_id, form_id=None, add_to_db=False, parse_id=None):
        
        selects = driver.find_elements("xpath", './/select')
        selects = [select for select in selects if select.is_displayed()]

        # order selects based on x, y, and value
        selects = sorted(selects, key=lambda x: (x.location['x'], x.location['y'], x.get_attribute("value")))
        select_objects = []

        for select in selects:
            value = select.get_attribute("value")
            context = ""
            x = select.location['x']
            y = select.location['y']
            width = select.size['width']
            height = select.size['height'] 
            id_val = select.get_attribute("id")
            name = select.get_attribute("name")
            select_obj = Input(x, y, width, height, context, page_id, 'select', parse_id=parse_id, name=name, value=value, form_id=form_id, add_to_db=add_to_db, id_val=id_val)
            for option in select.find_elements("xpath", './/option'):
                # if displayed and not disabled
                if option.is_displayed() and option.is_enabled():
                    select_obj.add_select_options(option)
            
            select_objects.append(select_obj)
        return select_objects


    def add_select_options(self, option):
        '''Add Select option to db'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO select_option (parse_id, element_id, option_id, option_value, selected) VALUES (%s, %s, %s, %s, %s)', (self.parse_id, self.id, option.get_attribute("value"), option.get_attribute("text"), option.is_selected()))
            conn.commit()


    def get_select_options(self):
        '''Get Select options from db'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            options = cur.execute("""SELECT option_id, option_value, selected FROM select_option WHERE element_id = %s""", (self.id,))
            options = cur.fetchall()
            return [dict(option) for option in options]


class Webform:
    def __init__(self, page_id, context, action=None, method=None, outer_html=None, parse_id=None):
        self.id = generate_id()
        self.page_id = page_id
        self.action = action
        self.method = method
        self.context = context
        self.outer_html = outer_html
        self.parse_id = parse_id
        self.add_form_to_db()


    def add_form_to_db(self):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO form (page_id, form_id, action_name, action_link, context, outerhtml, parse_id) VALUES (%s, %s, %s, %s, %s, %s, %s)', (self.page_id, self.id, self.action, self.method, self.context, self.outer_html, self.parse_id))
            conn.commit()


    def get_screenshots(form_id, parse_id):
        '''Take a screen shot from db'''
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('''SELECT * 
                            FROM screenshot 
                            WHERE node_id = (SELECT page_id FROM form WHERE form_id = %s) AND parse_id = %s
                            ORDER BY img_counter ASC
                            ''', (form_id, parse_id))
            images = cur.fetchall()
            if images is not None:
                return images
            return None


    def get_elements(form_id):
        Log.add_log('\tGetting elements for form')
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM element WHERE form_id = %s', (form_id,))
            rows = cur.fetchall()
        elements = []
        for row in rows:
            if row['element_type'] == 'button':
                elements.append(Button(row['x'], row['y'], row['width'], row['height'], row['context'], row['page_id'], row['element_type'], value=row['element_value'], id=row['id'], sub_type=row['element_subtype'], form_id=row['form_id'], add_to_db=False, parse_id=row['parse_id']))
            elif row['element_type'] == 'input' or row['element_type'] == 'select':
                elements.append(Input(row['x'], row['y'], row['width'], row['height'], row['context'], row['page_id'], row['element_type'], value=row['element_value'], id=row['id'], sub_type=row['element_subtype'], form_id=row['form_id'], add_to_db=False, parse_id=row['parse_id']))
        
        return elements
    

    def get_button_elements(self):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM element WHERE form_id = %s AND element_type = %s', (self.id,'button'))
            rows = cur.fetchall()
        return [Element(*row) for row in rows]


    def get_forms(driver, page_id, url, parse_id=None):
        Log.add_log('Getting forms')
        forms = driver.find_elements("xpath", '//form')
        forms = [form for form in forms if form.is_displayed()]
        form_list = {}
        for form in forms:
            outer_html = form.get_attribute("outerHTML")
            action = form.get_attribute("action")
            method = form.get_attribute("method")
            context = ""
            form_obj = Webform(page_id, context, action, method, outer_html=outer_html, parse_id=parse_id)
            form_id = form_obj.id
            form_list[form_id] = form_obj
            inputs = Input.get_inputs(form, page_id, form_id=form_id, add_to_db=True, parse_id=parse_id)
            buttons = Button.get_buttons(form, page_id, url, form_id=form_id, add_to_db=True,  parse_id=parse_id)

        Log.add_log('\tGetting Forms \n \t Found ' + str(len(form_list)) + ' forms')
            
        return form_list

        