from selenium_wrapper.web_scraping import WebScraping

import os
import json
from time import sleep
from datetime import datetime
from dotenv import load_dotenv
from logs import logger
from db import Database

load_dotenv()
PAGE = os.getenv("PAGE")
HEADLESS = os.getenv("HEADLESS") == "true"
RESTART_TIME = datetime.strptime(os.getenv("RESTART_TIME"), "%H:%M:%S")

CURRENT_PATH = os.path.dirname(__file__)


class Scraper (WebScraping): 
        
    last_restart = None
    
    threads_status = {
        "basic": "idle", 
        "details": "idle",
        "main": "idle"
    }
        
    # Scraping data
    matches_groups = []
    """ Structure of matches_groups:
    [
        {
            "country": str,
            "league": str,
            "matches_data": [
                {
                    "home_team": str, 
                    "away_team": str,
                    "index": int,
                    "id": str
                }
            ],
            "matches_indexes": [int],
        }
    ]
    """
    
    def __init__(self):
        """ Start scraper of the page
        """
        
        self.restarted_today = False
        
        # Instance database
        self.db = Database ()
        
        # Css selectors 
        self.selectors_pages = {
            "soccer24": {
                "cookies": "#onetrust-accept-btn-handler",
                "display_events": ".arrow.event__expander.event__expander--close",
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
                "score_preview": '.preview-ico.icon--preview',
                "over_under": {
                    "bookmarker": ".oddsTab__tableWrapper .ui-table.oddsCell__odds",
                    "base": ".ui-table__row",
                    "total": "span.oddsCell__noOddsCell",
                    "over": "a:nth-child(3) > span",
                    "under": "a:nth-child(4) > span",                     
                },
                "double_chance": {
                    "base": "#detail div.oddsTab__tableWrapper .ui-table__row > a",
                    "sufix": "> span",
                },
                "both_teams_to_score": {
                    "base": ".oddsTab__tableWrapper div div.ui-table__body > div.ui-table__row:nth-child(1) a.oddsCell__odd",
                    "sufix": "> span",
                }
            }, 
            "soccerstand": {
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
                
                
                "over_under": {
                    "bookmarker": "div.oddsTab__tableWrapper > div > div.ui-table__body > div",
                    "base": ".oddsTab__tableWrapper .ui-table.oddsCell__odds",
                    "total": "div.ui-table__body > div.ui-table__row:nth-child(1) > span",
                    "over": "div.ui-table__body > div.ui-table__row:nth-child(1) > a:nth-child(3) > span",
                    "under": "div.ui-table__body > div.ui-table__row:nth-child(1) > a:nth-child(4) > span",                     
                },
                "double_chance": {
                    "base": ".oddsTab__tableWrapper div div.ui-table__body > div.ui-table__row:nth-child(1) a.oddsCell__odd",
                    "sufix": "> span",
                },
                "both_teams_to_score": {
                    "base": ".oddsTab__tableWrapper div div.ui-table__body > div.ui-table__row:nth-child(1) a.oddsCell__odd",
                    "sufix": "> span",
                }
            }
        }
        
        self.pages = {
            "soccer24": "https://www.soccer24.com/",
        }  
        
        self.odds_links_pages = {
            "soccer24": {
                "dc": "/#/odds-comparison/double-chance/full-time", 
                "ou": "/#/odds-comparison/over-under/full-time", 
                "bts": "/#/odds-comparison/both-teams-to-score/full-time"
            },
            "soccerstand": {
                "dc": "/#/comparacion-cuotas/doble-oportunidad/partido", 
                "ou": "/#/comparacion-cuotas/mas-de-menos-de/partido", 
                "bts": "/#/comparacion-cuotas/ambos-equipos-marcaran/partido"
            }
        }
        
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
        self.odds_links = self.odds_links_pages.get(PAGE, None)
        
        if not self.page or not self.selectors or not self.odds_links:
            logger.error (f"Invalid page {PAGE}. Check your .env file")
            quit ()
            
        # Detect if required translations
        self.required_translations = False
        if PAGE == "soccerstand":
            self.required_translations = True
        
        # Start scraper
        self.__load_page__ ()
        self.__accept_cookies__ ()
        self.__display_events__ ()
        self.refresh_selenium ()
        
        self.go_bottom ()
        
    def __load_page__ (self): 
        """ Open browser instance and load page """
            
        # Load page
        super().__init__(headless=HEADLESS, time_out=500)
        self.set_page (self.page)
  
    def __accept_cookies__ (self):
        """ Click in 'accpet cookies' button if exists """
        
        sleep(5)
        try:
            self.click_js(self.selectors["cookies"])
        except Exception as err:
            logger.debug (f"can't click in cookies button: {err}")
            pass
        
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
    
    def __extract_data_loop__ (self, selectors:dict) -> dict:
        """ Try multiple times to extract data in loop, and validate integrity 
        
        Args:
            selectors (dict): Dictionary with selectors
            {
                "elem key": "selector",
                ...
            }
        
        Returns:
            dict: Dictionary with data
            
            {
                "elem key": ["value1", "value2", ...],
            }
        """
        
        self.__display_events__ ()
        
        for _ in range (3):
            
            data = {}
        
            lengths = []         
            for item, selector in selectors.items():
                
                # Get data
                texts = self.get_texts (selector)
                
                # Fix score
                if "score" in item and "" in texts: 
                    # Replace all empty scores with "-"
                    texts = list(map(lambda text: text if text != "" else "-", texts))
                    
                # Fix quotes
                if "c" in item:
                    # Clean quotes
                    texts = list(map(lambda text: text.lower().strip(), texts))
                
                # Save data
                data[item] = texts    
                lengths.append (len(texts))
                
            # Validate data integrit (all registers must have same length)
            avg = int(sum(lengths) / len(lengths))
            
            # Skip no data found
            if avg == 0:
                continue
            
            if all (length == avg for length in lengths) and avg:
                return data
            else:
                self.refresh_selenium ()
                continue
        
        # Logs error
        logger.error ("(basic) Data integrity lost. Restarting...")
        logger.debug (f"lengths: {lengths}")
        logger.debug (f"data: {data}")
        
        # Restart scraper
        Scraper.threads_status["basic"] = "kill"
        Scraper.threads_status["details"] = "kill"
        Scraper.threads_status["main"] = "restart"
        
        return {}
            
    def __is_restart_time__ (self):
        """ check if current time is after midnight """
        
        # Only restart one time per day
        today = datetime.now().day
        if Scraper.last_restart == today:
            return False
        
        # Only restart one time
        if self.restarted_today:
            return False
        
        # Get times
        now = datetime.now()
        midnight = now.replace(
            hour=RESTART_TIME.hour, 
            minute=RESTART_TIME.minute,
            second=RESTART_TIME.second,
            microsecond=0, 
            day=now.day
        )
        seconds = (midnight - now).total_seconds()
        
        # Validate if is after midnight
        if seconds < 0:
            self.restarted_today = True
            Scraper.last_restart = today
            return True
        else:
            return False

    def load_matches (self):
        """ Load matches and save country-ligue relation """
        
        logger.info ("\n* Reading matches...\n")
        
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
                
                # Validate if country and league already exists
                country_league_exist = list(filter(
                    lambda match_group: 
                        match_group["country"] == country and match_group["league"] == league, 
                    Scraper.matches_groups, 
                ))
                
                # Create new match group
                if country_league_exist:
                    
                    # Get current match group
                    current_match_group = country_league_exist[0]
                    
                else:
                
                    logger.info (f"Reading matches of {country} - {league}")
                    is_skipping = False       
                    
                    # Create new match group
                    Scraper.matches_groups.append ({
                        "country": country,
                        "league": league,
                        "matches_data": [],
                        "matches_indexes": [],
                    })
                
                    # Update current match group
                    current_match_group = Scraper.matches_groups[-1]   
                
            else: 
                
                # Ignore if country or league is not valid
                if is_skipping:
                    continue
                
                # Save match id if exists
                if index not in current_match_group["matches_indexes"]:
                    current_match_group["matches_indexes"].append (index)