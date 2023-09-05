from logs import logger
from scraper import Scraper
from scraper import THREADS_STATUS

class ScraperBasic (Scraper): 
    
    def __init__ (self):
        
        # Start scraper
        print ("\nOpening chrome for basic scraper...")
        super().__init__()
    
    def scrape_basic_general (self):
        """ Scrape general data (teams and ids), and save in db """
        
        logger.info ("\n(basic) Scraping teams and ids...")
        
        # Loop each match group
        for match_group in Scraper.matches_groups:
            
            # Indexes
            page_indexes = match_group["matches_indexes"]
            first_index = page_indexes[0]
            last_index = page_indexes[-1]
            
            # Validate if there are missing matches
            if len(match_group["matches_data"]) == len(page_indexes):
                continue
            # Delete matches_data (if exists)
            elif len(match_group["matches_data"]) < len(page_indexes):
                match_group["matches_data"] = []
            
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
                
        # Save data in db 
        logger.info ("\t(basic) Saving in db...")
        self.db.save_basic_general (Scraper.matches_groups)            
    
    def scrape_basic_oods (self):
        """ Scraper odds data (time, c1, c2, c3), in loop """
        
        # Update global status
        global THREADS_STATUS
        THREADS_STATUS["basic"] = "running"
        
        while True:
            
            # End if status is ending and details already end
            if THREADS_STATUS["basic"] == "ending" and THREADS_STATUS["details"] == "ended":
                THREADS_STATUS["basic"] = "ended"
                break
        
            logger.info ("\n(basic) Scraping odds...")
            
            # Loop each match group
            for match_group in Scraper.matches_groups:
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
            
            # Save data in db
            logger.info ("\t(basic) Saving in db...")
            self.db.save_basic_odds (Scraper.matches_groups)
            
            # refresh
            self.refresh_selenium ()    
            
        # Kill chrome instances when ends
        self.kill ()