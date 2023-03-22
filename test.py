from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
import os
import cv2
from parse import *
from page import *
import time
import unittest

parse = setup('https://owlo-training.herokuapp.com/company', 'test', '1', '123')
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
driver.get(parse.url)

# find button that has value "Join Waitlist"
button = driver.find_element(By.XPATH, "//button[contains(text(), 'Join Waitlist')]")
print(button)
button.click()
time.sleep(1)
print(Page.check_if_scrollable(driver))



