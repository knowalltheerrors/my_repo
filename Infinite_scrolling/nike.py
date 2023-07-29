# Nike Scraping Project 
import time 
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import pandas as pd

option = webdriver.ChromeOptions()
driver = webdriver.Chrome(options = option)

driver.get('https://www.nike.com/il/w/womens-sale-tops-t-shirts-3yaepz5e1x6z9om13')
last_height = driver.execute_script('return document.body.scrollHeight')
product_name = []


while True:
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
    time.sleep(3)
    new_height  = driver.execute_script('return document.body.scrollHeight')
    if new_height == last_height:
        break
    last_height = new_height


soup = BeautifulSoup(driver.page_source,features='lxml')
products = soup.select('div.product-grid__items div.product-card')

for name in products:

    d = {

   'Name':name.select_one('div.product-card__title').text.strip(),
   'Price':name.select_one('div.product-card__price div.product-price__wrapper div.product-price.is--current-price.css-1ydfahe').text.strip(),

    }

    product_name.append(d)

    print('successfully scraped the product ....')

df = pd.DataFrame.from_dict(data = product_name)
print(df)