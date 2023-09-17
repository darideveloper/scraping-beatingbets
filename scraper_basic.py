import os
from time import sleep 
from logs import logger
from scraper import Scraper
from scraper import THREADS_STATUS
from dotenv import load_dotenv

load_dotenv () 
WAIT_TIME_BASIC = int(os.getenv("WAIT_TIME_BASIC"))

class ScraperBasic (Scraper): 
    
    # DEBUG
    original_matches_groups = []
    
    def __init__ (self):
        
        # Start scraper
        print ("\n* Opening chrome for basic scraper...\n")
        super().__init__()
    
    def scrape_basic_general (self) -> bool:
        """ Scrape general data (teams and ids), and save in db 
        
        Returns
            bool: True if success, False if error
        """
        
        logger.info ("(basic) Scraping teams and ids...")
        
        # Loop each match group
        for match_group in Scraper.matches_groups:
            
            # Indexes
            page_indexes = match_group["matches_indexes"]
            
            if not page_indexes:
                continue
            
            first_index = page_indexes[0]
            last_index = page_indexes[-1]
            
            # Validate if there are missing matches
            if len(match_group["matches_data"]) == len(page_indexes):
                continue
            
            # Delete old matches_data (if exists)
            elif len(match_group["matches_data"]) < len(page_indexes):
                match_group["matches_data"] = []
            
            # Get all matches data
            selector_matches = f"{self.selectors['row']}:nth-child(n+{first_index}):nth-child(-n+{last_index})"
            selector_home_teams = f"{selector_matches} {self.selectors['team_home']}"
            selector_away_teams = f"{selector_matches} {self.selectors['team_away']}"
            
            
            # Get and clean ids
            ids = self.get_attribs (selector_matches, "id")
            ids = list(filter(lambda id: id != "", ids))
            
            # Get data
            data = self.__extract_data_loop__ ({
                "home_teams": selector_home_teams,
                "away_teams": selector_away_teams,
            })
            
            if not data:
                break               
            
            # Format and save data
            for index, id in enumerate (ids):               
                match_group["matches_data"].append ({
                    "home_team": data["home_teams"][index],
                    "away_team": data["away_teams"][index],
                    "id": id,
                    "index": page_indexes[index],
                })
                    
        # Save data in db 
        self.db.save_basic_general (Scraper.matches_groups) 
        
        return True       
    
    def scrape_basic_oods (self):
        """ Scraper odds data (time, c1, c2, c3), in loop """
        
        script = """
            const svgs = document.querySelectorAll ('.preview-ico.icon--preview')
            svgs.forEach (svg => {
                const parent = svg.parentElement
                parent.removeChild (svg)
                parent.innerHTML += '<div class="event__score event__score--home">-</div>'
                parent.innerHTML += '<div class="event__score event__score--away">-</div>'
            })
        """
        
        # Update global status
        global THREADS_STATUS
        THREADS_STATUS["basic"] = "running"
        
        running = True
        while running:
                        
            try:
                
                # Refresh page
                self.driver.execute_script (script)
                
                # End if status is ending and details already end
                if THREADS_STATUS["basic"] == "ending" and THREADS_STATUS["details"] == "ended":
                    THREADS_STATUS["basic"] = "ended"
                    break
            
                logger.info ("(basic) Scraping odds...")
                
                # Loop each match group
                for match_group_data in Scraper.matches_groups:
                    
                    match_group = match_group_data.copy ()
                    
                    # Force kill thread
                    if THREADS_STATUS["basic"] == "kill":
                        quit ()
                    
                    # Get indexes
                    page_indexes = match_group["matches_indexes"]
                    
                    if not page_indexes:
                        continue
                    
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
                    
                    ids = self.get_attribs (selector_matches, "id")
                    
                    # Clean ids
                    ids = list(filter(lambda id: id != "", ids))
                    
                    # Try 3 times to get data
                    data = self.__extract_data_loop__ ({
                        "time": selector_time,
                        "c1": selector_c1,
                        "c2": selector_c2,
                        "c3": selector_c3,
                        "score_home": selector_score_home,
                        "score_away": selector_score_away,
                    })
                        
                    # Catch no extracted data
                    if not data:
                        running = False
                        break
                    
                    # Format and save each match data
                    for index, id in enumerate (ids):
                        
                        # Format score
                        score_home = data["score_home"][index]
                        score_away = data["score_away"][index]
                        if score_home != "-" and score_away != "-":
                            score = f"{score_home} - {score_away}"
                        else: 
                            score = "none"
                    
                        # Get current match by id
                        match_data = list(filter(lambda match: match["id"] == id, match_group["matches_data"]))
                        if len(match_data) == 0:
                            continue
                        match_data = match_data[0]
                        
                        # Update match data
                        match_data["time"] = data["time"][index]
                        match_data["c1"] = data["c1"][index]
                        match_data["c2"] = data["c2"][index]
                        match_data["c3"] = data["c3"][index]
                        match_data["score"] = score
                    
                    # Force kill thread
                    if THREADS_STATUS["basic"] == "kill":
                        quit ()
                
                    # Save data in db
                    if running:
                        self.db.save_basic_odds ([match_group])
                        
                        # Wait before next scrape
                        sleep (WAIT_TIME_BASIC)
                        
                        # refresh
                        self.refresh_selenium ()    
                        
                        
            except Exception as e:
                logger.error (f"(basic) ERROR: connection error, restarting window... ")
                logger.debug (e)
                
                # Try to kill chrome
                try:
                    self.kill ()
                except:
                    pass
                
                # Restar class
                self.__init__ ()                
            
        # Kill chrome instances when ends
        self.kill ()