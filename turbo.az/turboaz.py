import urllib3
import re 
from selenium import webdriver
import time as t 
from bs4 import BeautifulSoup
import pandas as pd
from selenium.common.exceptions import NoSuchElementException


option = webdriver.ChromeOptions()
driver = webdriver.Chrome(options = option)
driver.get("https://turbo.az/autos?q%5Bmake%5D%5B%5D=41")

results = []

while True:

    soup = BeautifulSoup(driver.page_source,features = 'lxml')
    cars = soup.select('div.products div.products-i')


    for features in cars:


        des = {

        'Product_name':features.select_one('div.products-i__name').text.strip(),
        'Price':features.select_one('div.products-i__price').text.strip(),
        'Attributes':features.select_one('div.products-i__attributes').text.strip(),
        'Date':features.select_one('div.products-i__datetime').text.strip()
        
        }

        results.append(des)

    try:
        load_more_button = driver.find_element("link text",'Növbəti')
        driver.execute_script('arguments[0].click()',load_more_button)
        t.sleep(3)
    except NoSuchElementException:
        break

data_frame = pd.DataFrame.from_dict(data = results)
print(data_frame)
print('done')