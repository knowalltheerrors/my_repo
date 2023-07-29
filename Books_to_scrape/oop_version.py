import requests as re
from bs4 import BeautifulSoup
import pandas as pd 
import json 
    
class scraper():
    def __init__(self) -> None:
        self.results = []
        self.html = None 

    def get_books(self):
        soup = BeautifulSoup(self.html,features='html.parser')
        books = soup.select('ol.row li')
        for title in books:

            a = {

            'Title':title.select_one('h3 a')['title'],
            'Link':'https://books.toscrape.com/' + title.select_one('h3 a')['href'],
            'Price':title.select_one('div.product_price p.price_color').text.replace('Â£','£').strip(),
            'Stock':title.select_one('div.product_price p.instock').text.strip()


            }

            self.results.append(a)

    def next_page(self):
        soup = BeautifulSoup(self.html,features='html.parser')
        n_page_html = soup.select_one('li.next a')
            
        if not n_page_html:
           return False
        if 'catalogue' in n_page_html['href']:
            base_url = 'https://books.toscrape.com/' + soup.select_one('li.next a')['href']
        else:
            base_url = 'https://books.toscrape.com/catalogue/' + soup.select_one('li.next a')['href']
        return base_url
            

    def start_scrape(self):
        res = re.get('https://books.toscrape.com/')
        self.html = res.text
        self.get_books()
        npage_url = self.next_page()
        counter = 0
        while True:
            if not npage_url:
                break
            res = re.get(npage_url) 
            self.html = res.text 
            self.get_books()
            npage_url = self.next_page()
            counter+=1
            print(f'{counter} page is done')
        
        with open("results.json","w") as f:
            f.write(json.dumps(self.results))

item = scraper()
print(item.start_scrape())