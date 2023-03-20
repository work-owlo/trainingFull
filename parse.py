from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options


from page import Page
from element import Element
from action import Action
from utils import *
from scrape import *
from log import Log


def runner_dfs(parse, driver):
    # add the first page
    if parse.parse_page_count() == 0:
        parse.set_current_page(Page(driver=driver, id=0, parse_id=parse.id))
        Log.add_log('First page added ' + str(parse.cur_page.page_id))
        parse.cur_page.add_elements(driver, parse.id)
        parse.cur_page.save_screenshot()
    else:
        parse.set_current_page(Page(driver=driver, id=0, parse_id=parse.id, add_to_db=False))

    while Element.has_next_element(parse.id):
        # parse.draw_graph()
        element = Element.get_next_element(parse.id)
        driver.execute_script("window.scrollTo(0, 0)")
        source_page = Page.get_page(element.page_id, parse.id)
        Log.add_log('\tSource page: ' + str(source_page.page_id))
        element_traversed, driver, parse.cur_page = parse.traverse_to_state_change_root(driver, element, parse.id)
        Log.add_log('\tCurrent page: ' + str(parse.cur_page.page_id))
        Log.add_log('\tElement Traveresed: ' + str(element_traversed))
        
        if element_traversed:
            try:
                time.sleep(.5)
                success, elements, driver = parse.perform_action(driver, element, check_page_change=True)
                if success == 'incomplete_input':
                    print('returing form_id: ' + str(element.form_id))
                    return element.form_id
                # ensure we stay within main domain
                if (parse.url == driver.current_url or driver.current_url.startswith(parse.url)):
                    next_page = Page(driver=driver, source_element_id = element.id, id=parse.get_page_id(), parse_id=parse.id) 
                    visited = next_page.page_visited()
                    if success and visited == -1:
                        Log.add_log('\tNew page added ' + str(next_page.page_id))
                        next_page.save_screenshot()
                        for e in elements:
                            Action.get_actions(driver, source_page, next_page, e, parse.id)
                        next_page.add_elements(driver, parse.id)
                        parse.set_current_page(next_page)
                    elif success and visited != -1:
                        Log.add_log('\tPage already visited - ' + str(visited))
                        if parse.cur_page.page_id != visited:
                            parse.set_current_page(Page.get_page(visited, parse.id))
                            Log.add_log('\tCurrent page: ' + str(parse.cur_page.page_id))
                            Log.add_log('\tAdding actions from ' + str(source_page.page_id) + ' to ' + str(parse.cur_page.page_id))
                            for e in elements: 
                                Action.get_actions(driver, source_page, parse.cur_page, e, parse.id)
                        else:
                            Log.add_log('\tRedirected to same page')
                            element.delete_self('Redirected to same page')
                    elif not success:
                        element.delete_self('Failed to perform action')
                else:

                    element.delete_self('Deviating from domain')
                    driver.back()
            except ElementClickInterceptedException as e:
                Log.add_log('\t\t\t\Intercepted click: ' + str(e))
                Log.add_log('\t\t\t' + element.find_element(driver).get_attribute('outerHTML'))
                element.delete_self('Intercepted click')
        else:
            element.delete_self('Element not found')
    parse.complete()
    return False
        

def setup(url, software_name, company_id, description):
    input_type = 'ai'
    parse = Parse(input_type, url, software_name=software_name, company_id=company_id, description=description, add_to_db=True)
    return parse


def parser(parse_id):  
    parse = Parse.get_parse(parse_id)
    if parse.get_status() == 'complete':
        return False
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1200, 800)
    driver.get(parse.url)
    return runner_dfs(parse, driver)

