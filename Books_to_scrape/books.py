import requests
from bs4 import BeautifulSoup
import pandas as pd

with open('books.html','r') as f:
    html = f.read()

results = []
soup = BeautifulSoup(html,features='html.parser')

numbers = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5}

base_url = 'https://books.toscrape.com' 

while True:
    books = soup.select('ol.row li')
    
    for title in books:
        
        a = {
            
        'Title':title.select_one('h3 a')['title'],
        'Link':'https://books.toscrape.com/' + title.select_one('h3 a')['href'],
        'Price':title.select_one('div.product_price p.price_color').text.replace('Â£','£').strip(),
        'Stock':title.select_one('div.product_price p.instock').text.strip(),
        'Rating':numbers[title.select_one('p.star-rating')['class'][1]]

        }

        results.append(a)
                
        
    print(f'{base_url} is successfully scraped')
    n_page_html = soup.select_one('li.next a')

    if not n_page_html:
        break
    if 'catalogue' in n_page_html['href']:
        base_url = 'https://books.toscrape.com/' + soup.select_one('li.next a')['href']
    else:
        base_url = 'https://books.toscrape.com/catalogue/' + soup.select_one('li.next a')['href']
        
    res =requests.get(base_url)
    soup = BeautifulSoup(res.text,features='html.parser')

df = pd.DataFrame.from_dict(data = results)
print(df)
print('successfull')