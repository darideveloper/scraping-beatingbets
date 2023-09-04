from scraping.web_scraping import WebScraping

import os
import json
from time import sleep
from dotenv import load_dotenv
from logs import logger

load_dotenv()

PAGE = os.getenv("PAGE")
HEADLESS = os.getenv("HEADLESS").lower().strip() == "true"

CURRENT_PATH = os.path.dirname(__file__)

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
                "league": "div.icon--flag div span:nth-child(2)"
            }
        }
        self.pages = {
            "soccer24": "https://www.soccer24.com/",
        }  
        
        # Scraping data
        self.matches_groups = []
        
        # Filters
        self.countries = []
        self.leagues = []
        self.translate_status = {}
        self.translate_countries = {}
        self.translate_leagues = {}
        
        # Load data from jsons
        self.__load_filters__ ()
        
        # Get current page and selectors
        self.page = self.pages.get(PAGE, None)
        self.selectors = self.selectors_pages.get(PAGE, None)
        
        if not self.page or not self.selectors:
            logger.error (f"Invalid page {PAGE}. Check your .env file")
            quit ()
            
        # Detect if required translations
        self.required_translations = False
        if PAGE == "soccerstand":
            self.required_translations = True
            
            
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
        
    def __load_filters__ (self): 
        """ Load country, leagues and translations from json """
        
        path_filters = os.path.join (CURRENT_PATH, "filters")
        path_countries = os.path.join (path_filters, "countries.json")
        path_leagues = os.path.join (path_filters, "leagues.json")
        path_translate = os.path.join (path_filters, "translate.json")
        
        with open (path_countries, encoding='UTF-8') as file:
            self.countries = json.load (file)
            
        with open (path_leagues, encoding='UTF-8') as file:
            self.leagues = json.load (file)
            
        with open (path_translate, encoding='UTF-8') as file:
            json_data = json.load (file)
            self.translate_status = json_data["status"]
            self.translate_countries = json_data["countries"]
            self.translate_leagues = json_data["leagues"]
    
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
        is_skipping = False   
        for index in range (1, max_rows + 1):
            
            selector_row = f"{self.selectors['row']}:nth-child({index})"
            classes_row = self.get_elem(selector_row).get_attribute("class")
            
            if self.selectors["class_event_header"] in classes_row:
                
                # Get country and league
                selector_country = f"{selector_row} {self.selectors['country']}"
                selector_league = f"{selector_row} {self.selectors['league']}"
                country = self.get_text (selector_country)
                league = self.get_text (selector_league)
                
                if not country or not league:
                    logger.error (f"Can't get country or league in row {index}")
                
                # Translate country and league 
                if self.required_translations: 
                    country = self.translate_countries.get(country, country)
                    league = self.translate_leagues.get(league, league)
                
                # Validate countries and leagues
                if country not in self.countries:
                    logger.debug (f"Country {country} not in filters, skipped")
                    is_skipping = True
                    continue
                
                if league not in self.leagues:
                    logger.debug (f"League {league} not in filters, skipped")
                    is_skipping = True
                    continue         
                
                logger.info (f"Reading matches of {country} - {league}")
                is_skipping = False       
                
                # Create new match group
                self.matches_groups.append ({
                    "country": country,
                    "league": league,
                    "matches_data": [],
                    "matches_indexs": [],
                })
                current_match_group = self.matches_groups[-1]   
                
            else: 
                
                # Ignore if country or league is not valid
                if is_skipping:
                    continue
                
                # Save match id
                current_match_group["matches_indexs"].append (index)
        
    
if __name__ == "__main__":
    
    scraper = Scraper()
    scraper.load_matches ()
    