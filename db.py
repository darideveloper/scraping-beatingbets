import os
from datetime import datetime
from database.mysql import MySQL
from logs import logger
from dotenv import load_dotenv

# DB credentials
load_dotenv ()
DB_HOST = os.getenv ("DB_HOST")
DB_USER = os.getenv ("DB_USER")
DB_PASSWORD = os.getenv ("DB_PASSWORD")
DB_NAME = os.getenv ("DB_NAME")
DB_TABLE = os.getenv ("DB_TABLE")

class Database (MySQL): 
    
    def __init__ (self): 
        """" Send credentials to MySQL class """
        super().__init__ (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD)
        
    def __clean_string__ (self, string:str):
        
        replace_chars = {
            "'": "\\'",
        }
        for char, replace in replace_chars.items():
            string = string.replace (char, replace)
            
        return string
        
    def save_basic_general (self, matches_groups:list): 
        """ Save general data (ids, dates, countries, leagues, teams)

        Args:
            matches_groups (list): list of dicts with matches data
        """
        
        today = datetime.now()
        today_fommated = today.strftime ("%Y-%m-%d")
        new_matches_saved = 0
        
        # Loop groups
        for match_group in matches_groups:
            country = match_group["country"]
            league = match_group["league"]
            matches_data = match_group["matches_data"]
            
            # ignore already saved matches
            ids = list(map (lambda match: f"'{match['id']}'", matches_data))
            query = f"SELECT id_web FROM {DB_TABLE} WHERE id_web IN ({','.join(ids)})"
            matches_saved = self.run_sql (query)
            matches_saved_ids = list(map (lambda match: match["id_web"], matches_saved))
            matches_to_save = list(filter (lambda match: match["id"] not in matches_saved_ids, matches_data))            
            
            # Loop match
            for match_data in matches_to_save:
                
                id_web = match_data["id"]
                team1 = match_data["home_team"]
                team2 = match_data["away_team"]
                
                # Clean data
                country = self.__clean_string__ (country)
                league = self.__clean_string__ (league)
                team1 = self.__clean_string__ (team1)
                team2 = self.__clean_string__ (team2)               
                
                # Insert new match
                query = f"""INSERT INTO {DB_TABLE} (id_web, date, country, liga, team1, team2)
                    VALUES ('{id_web}', '{today_fommated}', '{country}', '{league}', '{team1}', '{team2}')                
                """
                self.run_sql (query)
                
                new_matches_saved += 1
        
        if new_matches_saved:
            logger.info (f"\t{new_matches_saved} new matches saved in basic general")
        else: 
            logger.info ("\tNo new matches saved in basic general")