from scraping.web_scraping import WebScraping

import os
import json
from time import sleep
from dotenv import load_dotenv
from logs import logger
from db import Database

load_dotenv()

PAGE = os.getenv("PAGE")
HEADLESS = os.getenv("HEADLESS").lower().strip() == "true"

CURRENT_PATH = os.path.dirname(__file__)

class Scraper (WebScraping): 
    
    def __init__(self):
        """ Start scraper of the page
        """
        
        # Instance database
        self.db = Database ()
        
        # Css selectors 
        self.selectors_pages = {
            "soccer24": {
                "cookies": "#onetrust-accept-btn-handler",
                "display_events": ".event__expander.icon--expander.expand",
                "class_event_header": "event__header",
                "row": "#live-table > section > div > div > div",
                "country": "div.icon--flag div span:nth-child(1)",
                "league": "div.icon--flag div span:nth-child(2)",
                "team_home": ".event__participant.event__participant--home",
                "team_away": ".event__participant.event__participant--away",
                "time": 'div.eventSubscriber + div',
                "c1": 'div.event__odd--odd1',
                "c2": 'div.event__odd--odd2',
                "c3": 'div.event__odd--odd3',
                "score_home": '.event__score.event__score--home',
                "score_away": '.event__score.event__score--away',
            }
        }
        self.pages = {
            "soccer24": "https://www.soccer24.com/",
        }  
        
        # Scraping data
        self.matches_groups = []
        """ Structure of matches_groups:
        {
            "country": str,
            "league": str,
            "matches_data": [{
                "home_team": str, 
                "away_team": str,
                "id": str,
                "index": int,
            }],
            "matches_indexes": [int],
        }
        """
        
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
            
            
        logger.info (f"\nStarting scraper for {PAGE}")
        
        
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
        
        logger.info ("\nReading matches...")
        
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
                if country not in self.countries or league not in self.leagues:
                    logger.debug (f"Skipping matches of {country} - {league}")
                    is_skipping = True
                    continue
                
                logger.info (f"Reading matches of {country} - {league}")
                is_skipping = False       
                
                # Create new match group
                self.matches_groups.append ({
                    "country": country,
                    "league": league,
                    "matches_data": [],
                    "matches_indexes": [],
                })
                current_match_group = self.matches_groups[-1]   
                
            else: 
                
                # Ignore if country or league is not valid
                if is_skipping:
                    continue
                
                # Save match id
                current_match_group["matches_indexes"].append (index)
    
    def scrape_basic_general (self):
        """ Scrape general data (teams and ids), and save in db """
        
        logger.info ("\nScraping teams and ids in basic...")
        
        # Loop each match group
        for match_group in self.matches_groups:
            page_indexes = match_group["matches_indexes"]
            first_index = page_indexes[0]
            last_index = page_indexes[-1]
            
            # Get all matches data
            selector_matches = f"{self.selectors['row']}:nth-child(n+{first_index}):nth-child(-n+{last_index})"
            selector_home_teams = f"{selector_matches} {self.selectors['team_home']}"
            selector_away_teams = f"{selector_matches} {self.selectors['team_away']}"
            
            ids = self.get_attribs (selector_matches, "id")
            home_teams = self.get_texts (selector_home_teams)
            away_teams = self.get_texts (selector_away_teams)
            
            # Format and save data
            for index, id in enumerate (ids):               
                match_group["matches_data"].append ({
                    "home_team": home_teams[index],
                    "away_team": away_teams[index],
                    "id": id,
                    "index": page_indexes[index],
                })
                
        # Save data in db with a thread
        logger.info ("\tSaving in db...")
        self.db.save_basic_general (self.matches_groups)            
    
    def scrape_basic_oods (self):
        """ Scraper odds data (time, c1, c2, c3) """
        
        logger.info ("\nScraping quotes in basic...")
        
        # Loop each match group
        for match_group in self.matches_groups:
            page_indexes = match_group["matches_indexes"]
            first_index = page_indexes[0]
            last_index = page_indexes[-1]
            
            # Get all matches data
            selector_matches = f"{self.selectors['row']}:nth-child(n+{first_index}):nth-child(-n+{last_index})"
            selector_time = f"{selector_matches} {self.selectors['time']}"
            selector_c1 = f"{selector_matches} {self.selectors['c1']}"
            selector_c2 = f"{selector_matches} {self.selectors['c2']}"
            selector_c3 = f"{selector_matches} {self.selectors['c3']}"
            selector_score_home = f"{selector_matches} {self.selectors['score_home']}"
            selector_score_away = f"{selector_matches} {self.selectors['score_away']}"
            
            times = self.get_texts (selector_time)
            c1s = self.get_texts (selector_c1)
            c2s = self.get_texts (selector_c2)
            c3s = self.get_texts (selector_c3)
            scores_home = self.get_texts (selector_score_home)
            scores_away = self.get_texts (selector_score_away)
            
            for index, time in enumerate (times):
                
                # Validate if matches_data already have info
                if len(match_group["matches_data"]) <= index:
                    continue
                
                # Format score
                score_home = scores_home[index]
                score_away = scores_away[index]
                if score_home != "-" and score_away != "-":
                    score = f"{score_home} - {score_away}"
                else: 
                    score = "none"
                
                # update data in row
                match_group["matches_data"][index]["time"] = time
                match_group["matches_data"][index]["c1"] = c1s[index]
                match_group["matches_data"][index]["c2"] = c2s[index]
                match_group["matches_data"][index]["c3"] = c3s[index]
                match_group["matches_data"][index]["score"] = score
        
         # Save data in db with a thread
        logger.info ("\tSaving in db...")
        self.db.save_basic_odds (self.matches_groups) 
        
        
    
if __name__ == "__main__":
    
    scraper = Scraper()
    scraper.load_matches ()
    scraper.scrape_basic_general ()
    
    
    scraper.scrape_basic_oods () 
    