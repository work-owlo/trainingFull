from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
import os
import cv2
from parse import *
import unittest

parse = setup('https://owlo-training.herokuapp.com/', 'test', '1', '123')
parser(parse.id)
        # assert True



im = cv2.imread('images/1352.0screenshot.png')

# print(type(im))
# # <class 'numpy.ndarray'>

print('width: {} pixels'.format(im.shape[1]))
print('height: {} pixels'.format(im.shape[0]))
# class TestScreenshots(unittest.TestCase):

#     def test_no_errors(self):
#         '''Ensure no errors are thrown'''
       

#     # parse = setup('https://owlo-training.herokuapp.com/', 'test', '1', '123')
#     # parser(parse.id)

#     def test_num_screenshots(self):
#         '''Ensure the correct number of screenshots are being supplied'''
#         # get the number of png files in images
#         num_images = len([name for name in os.listdir('images') if name.endswith('.png')])
#         self.assertEqual(num_images, 6, "Should be 6")



# if __name__ == '__main__':
#     unittest.main()
