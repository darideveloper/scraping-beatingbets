import os
from time import sleep
from threading import Thread
from scraper import Scraper
from scraper import THREADS_STATUS
from scraper_basic import ScraperBasic
from scraper_details import ScraperDetails
from logs import logger
from dotenv import load_dotenv

# Env variables
load_dotenv ()
MINUTES_REOPEN = int(os.getenv("MINUTES_REOPEN"))

if __name__ == "__main__":
    
    while True:
            
        # Load matches
        scraper = Scraper()
        scraper.load_matches ()
        scraper.kill ()
        
        # Instance browsers
        scraper_basic = ScraperBasic()
        scraper_details = ScraperDetails()
        
        # Scrape general data only one time
        scraper_basic.scrape_basic_general ()
        sleep (2)
        
        # Scraper basic odds in thread
        thread_basic_odds = Thread(target=scraper_basic.scrape_basic_oods)
        thread_basic_odds.start()
        
        # Scraper details odds in thread
        thread_details_odds = Thread(target=scraper_details.scrape_details_oods)
        thread_details_odds.start ()
        
        # End threads after reopen time
        sleep (MINUTES_REOPEN * 60)
        logger.info ("\nRestarting scraper...\n")
        THREADS_STATUS["basic"] = "ending"
        THREADS_STATUS["details"] = "ending"
        
        # Wait until threads end
        thread_basic_odds.join ()
        thread_details_odds.join ()
        print ()