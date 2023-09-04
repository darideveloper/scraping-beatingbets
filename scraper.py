from scraping.web_scraping import WebScraping

import os
from time import sleep
from dotenv import load_dotenv
from logs import logger

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
                "cookies": "#onetrust-accept-btn-handler",
                "display_events": ".event__expander.icon--expander.expand",
                "class_event_header": "event__header",
                "row": "#live-table > section > div > div > div",
                "country": "div.icon--flag div span:nth-child(1)",
                "liga": "div.icon--flag div span:nth-child(2)"
            }
        }
        self.pages = {
            "soccer24": "https://www.soccer24.com/",
        }  
        
        # Scraping data
        self.matches_groups = []
        
        # Get current page and selectors
        self.page = self.pages.get(PAGE, None)
        self.selectors = self.selectors_pages.get(PAGE, None)
        
        if not self.page or not self.selectors:
            logger.error (f"Invalid page {PAGE}. Check your .env file")
            quit ()
            
        logger.info (f"Starting scraper for {PAGE}")
        
    def __accept_cookies__ (self):
        """ Click in 'accpet cookies' button if exists """
        
        sleep(5)
        try:
            self.click_js(self.selectors["cookies"])
        except Exception as err:
            logger.debug (f"can't click in cookies button: {err}")
            pass
            
    def __load_page__ (self): 
        """ Kill open browser instances and load page """
        
        # Close current chrome instance
        try:
            self.kill ()
        except Exception as err:
            logger.debug (f"Can't kill chrome instance: {err}")
            pass
            
        # Load page
        super().__init__(headless=HEADLESS)
        self.set_page (self.page)
        
    def __display_events__ (self):
        """ Show all events in table """
        
        # Display all events
        display_buttons = self.get_elems(self.selectors["display_events"])

        for display_button in display_buttons: 
            try:
                self.driver.execute_script("arguments[0].click();", display_button)
            except Exception as err:
                logger.debug (f"Can't click in display button: {err}")
                pass       
            
        self.refresh_selenium ()
    
    def load_matches (self):
        """ Load matches and save country-ligue relation """
        
        print ("Reading matches...")
        
        # Start scraper
        self.__load_page__ ()
        self.__accept_cookies__ ()
        self.__display_events__ ()
        
        self.go_bottom ()
        
        # Loop each row for detect headers and matches
        current_match_group = {}
        max_rows = len(self.get_elems(self.selectors["row"]))
               
        for index in range (1, max_rows + 1):
            
            selector_row = f"{self.selectors['row']}:nth-child({index})"
            classes_row = self.get_elem(selector_row).get_attribute("class")
            
            
            if self.selectors["class_event_header"] in classes_row:
                
                # Get country and liga
                selector_country = f"{selector_row} {self.selectors['country']}"
                selector_liga = f"{selector_row} {self.selectors['liga']}"
                country = self.get_text (selector_country)
                liga = self.get_text (selector_liga)
                
                if not country or not liga:
                    logger.error (f"Can't get country or liga in row {index}")
                
                # Create new match group
                self.matches_groups.append ({
                    "country": country,
                    "liga": liga,
                    "matches_data": [],
                    "matches_indexs": [],
                })
                current_match_group = self.matches_groups[-1]   
                
            else: 
                
                # Get general match data
                id = self.get_attrib (selector_row, "id")
                
                # Save match data
                current_match_group["matches_data"].append ({
                    "id": id
                })
                
                # Save match id
                current_match_group["matches_indexs"].append (index)
        
        print ()
        
        
    
if __name__ == "__main__":
    
    scraper = Scraper()
    scraper.load_matches ()
    print ()