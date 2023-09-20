from time import sleep
from logs import logger
from scraper import Scraper
from scraper import THREADS_STATUS

class ScraperDetails (Scraper): 
    
    def __init__ (self):
        
        # Start scraper
        print ("\n* Opening chrome for details scraper...\n")
        super().__init__()
        
        # Details page links
        self.link_dc = ""
        self.link_ou = ""
        self.link_bts = ""
        
    def __set_page_wait__ (self, link:str):
        self.set_page (link)
        sleep (4)
        self.refresh_selenium (back_tab=1)     

    def __get_over_under__ (self) -> tuple:
        """ Get over under data from details ods page 
        
        Returns: 
            over_15, over_25, under_25, under_35
        """
        
        # Load page
        self.__set_page_wait__ (self.link_ou)
        
        # Get data
        selectors_ou = self.selectors["over_under"]
        selector_bookmarker = selectors_ou["bookmarker"]
        bookmarkers = self.get_elems(selector_bookmarker)
        
        over_15 = ""
        over_25 = ""
        under_25 = ""
        under_35 = ""
        
        # Try to extract data 3 times
        for _ in range (3):
            
            for index in range (1, len(bookmarkers)): 
            
                selector_base = f"{selector_bookmarker}:nth-child({index}) {selectors_ou['base']}:nth-child(1)"
                                                
                selector_total = f"{selector_base} {selectors_ou['total']}"
                total = self.get_text (selector_total)
                                                
                selector_over = f"{selector_base} {selectors_ou['over']}"
                selector_under = f"{selector_base} {selectors_ou['under']}"
                                
                if total == "1.5": 
                    over_15 = self.get_text(selector_over)
                    
                if total == "2.5": 
                    over_25 = self.get_text(selector_over)
                    under_25 = self.get_text(selector_under)
                
                if total == "3.5": 
                    under_35 = self.get_text(selector_under)    
                    
                if over_15 and over_25 and under_25 and under_35:
                    break  
            
            if over_15 and over_25 and under_25 and under_35:
                break
        
            sleep (1)
            self.refresh_selenium (back_tab=-1)
        
        
        if not (over_15 and over_25 and under_25 and under_35):
            raise Exception ("Odds not found")
        
        return (over_15, over_25, under_25, under_35)
    
    def __get_double_chance__ (self) -> tuple:
        """ Get over under data from details ods page 
        
        Returns: 
            dc_x1, dc_12, dc_x2
        """
        
        # Load page
        self.__set_page_wait__ (self.link_dc)
        
        selectors_dc = self.selectors["double_chance"]
        
        selector_dc_x1 = f"{selectors_dc['base']}:nth-child(2) {selectors_dc['sufix']}"
        selector_dc_12 = f"{selectors_dc['base']}:nth-child(3) {selectors_dc['sufix']}"
        selector_dc_x2 = f"{selectors_dc['base']}:nth-child(4) {selectors_dc['sufix']}"
        
        # Try to extract data 3 times
        for _ in range (3):
            dc_x1 = self.get_text(selector_dc_x1)
            dc_12 = self.get_text(selector_dc_12)
            dc_x2 = self.get_text(selector_dc_x2)
            
            if dc_x1 and dc_12 and dc_x2:
                break
            
            self.driver.refresh ()          
            sleep (2)
            self.refresh_selenium (back_tab=-1)
            
        if not (dc_x1 and dc_12 and dc_x2):
            raise Exception ("Odds not found")
        
        return (dc_x1, dc_12, dc_x2)
    
    def __get_both_teams_to_score__ (self) -> tuple:
        """ Get over under data from details ods page 
        
        Returns: 
            aa, na
        """
        
        # Load page
        self.__set_page_wait__ (self.link_bts)
        
        selectors_bts = self.selectors["both_teams_to_score"]
        
        selector_aa = f"{selectors_bts['base']}:nth-child(2) {selectors_bts['sufix']}"
        selector_na = f"{selectors_bts['base']}:nth-child(3) {selectors_bts['sufix']}"                     
        
        # Try to extract data 3 times
        for _ in range (3):
            aa = self.get_text (selector_aa)
            na = self.get_text (selector_na)
            
            if aa and na:
                break
            
            sleep (1)
            self.refresh_selenium (back_tab=-1)
        
        if not (aa and na):
            raise Exception ("Odds not found")
        
        return (aa, na)

    def scrape_details_oods (self):
        """ Scraper odds data from details page in loop """
        
        # Update global status
        global THREADS_STATUS
        THREADS_STATUS["details"] = "running"
        
        while True:
            
            try:
                # End if status is ending and details already end
                if THREADS_STATUS["details"] == "ending":
                    THREADS_STATUS["details"] = "ended"
                    break
            
                logger.info ("(details) Scraping odds...")
                
                # Display events (again)
                self.__display_events__ ()
                
                # Loop groups
                for match_group in Scraper.matches_groups:
                                        
                    matches_indexes = match_group["matches_indexes"]
                    
                    matches_data = match_group["matches_data"][:]
                    matches_data_new = []
                    
                    # Loop matches
                    for index in matches_indexes: 
                        
                        # Force kill thread
                        if THREADS_STATUS["details"] == "kill":
                            quit ()
                        
                        # Selectors 
                        selector_row = f"{self.selectors['row']}:nth-child({index})"
                        selector_details_btn = f"{selector_row} {self.selectors['team_home']}"
                        
                        # Get current match data
                        match_id = self.get_attrib (selector_row, "id")
                        match_data = list(filter(lambda match: match["id"] == match_id, matches_data))
                        if len(match_data) == 0:
                            continue
                        match_data = match_data[0]
                        team1 = match_data["home_team"]
                        team2 = match_data["away_team"]
                        logger.info (f"(details) Scraping for {team1} - {team2}...")
                                            
                        # get details url
                        self.click_js (selector_details_btn)
                        self.switch_to_tab (1)
                        current_url = self.driver.current_url
                        url_end = str(current_url).find("/#/")
                        details_url = str(current_url)[:url_end]
                        
                        # Generate odds link
                        self.link_dc = f"{details_url}{self.odds_links['dc']}"
                        self.link_ou = f"{details_url}{self.odds_links['ou']}"
                        self.link_bts = f"{details_url}{self.odds_links['bts']}"
                        
                        # Close pop window
                        self.close_tab ()
                        self.switch_to_tab (0)
                        
                        # Create and twitch to new tab
                        self.open_tab ()
                        self.switch_to_tab (1)
                        
                        # Get odds data
                        error = False
                        try:
                            over_15, over_25, under_25, under_35 = self.__get_over_under__()
                            dc_x1, dc_12, dc_x2 = self.__get_double_chance__()
                            aa, na = self.__get_both_teams_to_score__()
                        except:
                            logger.error (f"(details) Odds not found in match {team1} - {team2}, skipped")
                            
                            # Delete from db
                            self.db.delete_match (match_id)
                            
                            error = True

                        # Return to home page
                        self.close_tab ()
                        self.switch_to_tab (0) 
                        
                        # Skip if error
                        if error:
                            continue
                        
                        # Save data in match group
                        match_data["over_15"] = over_15
                        match_data["over_25"] = over_25
                        match_data["under_25"] = under_25
                        match_data["under_35"] = under_35
                        match_data["dc_x1"] = dc_x1
                        match_data["dc_12"] = dc_12
                        match_data["dc_x2"] = dc_x2
                        match_data["aa"] = aa
                        match_data["na"] = na
                        
                        # Save new match data
                        matches_data_new.append (match_data)
                        
                        # Force kill thread
                        if THREADS_STATUS["basic"] == "kill":
                            quit ()                                   
                
                    # Save data in db
                    if matches_data_new:
                        match_group["matches_data"] = matches_data_new
                        self.db.save_details_odds ([match_group])
                        
                        # Restar match group
                        match_group["matches_data"] = matches_data
                        
                        print ()
                
                # refresh
                self.refresh_selenium ()    
                
            except Exception as e:
                logger.error (f"(details) Connection lost, restarting window... ")
                logger.debug (e)
                
                # Restar class
                self.__init__ ()
                            