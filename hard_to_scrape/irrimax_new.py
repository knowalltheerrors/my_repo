import re as regex 
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import time as t 
import re as regex


class new_irrimax():
    
    # Constructor for all the variables 
    def __init__(self):
        self.results = []
        self.clean_result = []    
        self.driver = None 
        self.start_time = t.time()
                
    # connector method will take care of the selenium connections 
    def connector(self):
        option = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options = option)
        self.driver.get("https://www.irrimaxlive.com/#:c/")

    # This method handles logging part to the website.
    def logging(self):
        u = self.driver.find_element("name","username")
        u.send_keys("put_your_username")
        p =self.driver.find_element("name","password")
        p.send_keys("put_your_password")
        button = self.driver.find_element("xpath",'/html/body/div[2]/div/form/div[4]/div[2]/button')
        button.click()
        
    # This method starts all the stages
    def starter(self):
        self.connector()
        self.logging()
        t.sleep(2)
        self.transformation()
        print('successfully logged in')
        print(self.clean_result)
        print(str(t.time()-self.start_time) + ' ' +  'seconds')  

    # Transformation method will start parsing, cleaning and append clean result to the empty variable. 
    def transformation(self):
        soup = BeautifulSoup(self.driver.page_source,features = 'html.parser')
        regions = soup.select('div.gallerycontainer div.galleryitem')

        for link in regions:
            self.results.append(str(link))
 
        for x in self.results:
            match = regex.search(r"imxid=(.*?)imxuid", x)
            if match:
                extracted_part = match.group(1).strip('" "')
                self.clean_result.append(extracted_part.rstrip())
        return True
    

item = new_irrimax()
print(item.starter()) 