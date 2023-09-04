from scraping.web_scraping import WebScraping

import os
from dotenv import load_dotenv

load_dotenv()

PAGE = os.getenv("PAGE")
HEADLESS = os.getenv("HEADLESS").lower().strip() == "true"

class Scraper (WebScraping): 
    
    def __init__(self):
        """ Start scraper of the page
        """
        
        # Css selectors 
        self.selectors_pages = {
            "soccer24": {
                "hello": "world",
            }
        }
        self.pages = {
            "soccer24": "https://www.soccer24.com/",
        }  
        
        # Scraping data
        self.matches = []
        
        # Get current page and selectors
        self.page = self.pages.get(PAGE, None)
        self.selectors = self.selectors_pages.get(PAGE, None)
        
        if not self.page or not self.selectors:
            print ("ERROR: Invalid page. Check your .env file")
            quit ()
            
        print (f"Starting scraper for {PAGE}")
            
        # Start chrome and load page
        self.load_page ()
            
    def load_page (self): 
        
        # Close current chrome instance
        try:
            self.kill ()
        except:
            pass
            
        # Load page
        super().__init__(headless=HEADLESS)
        self.set_page (self.page)
        
        
    
if __name__ == "__main__":
    
    scraper = Scraper()
    print ()