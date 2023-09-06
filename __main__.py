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

THREAD_BASIC = None
THREAD_DETAILS = None
THREAD_MAIN_STATUS = "running"

def main ():
    """ Start scraper with threads """
    
    global THREAD_MAIN_STATUS
    global THREAD_BASIC
    global THREAD_DETAILS
    
    while True:
        
        # Load matches
        scraper = Scraper()
        scraper.load_matches ()
        scraper.kill ()
        
        # Instance browsers
        scraper_basic = ScraperBasic()
        scraper_details = ScraperDetails()
        
        # Kill thread
        if THREAD_MAIN_STATUS == "kill":
            quit ()
        
        # Scrape general data only one time
        scraper_basic.scrape_basic_general ()
        sleep (2)
        
        # Kill thread
        if THREAD_MAIN_STATUS == "kill":
            quit ()
        
        # Scraper basic odds in thread
        THREAD_BASIC = Thread(target=scraper_basic.scrape_basic_oods)
        THREAD_BASIC.start()
        
        # Kill thread
        if THREAD_MAIN_STATUS == "kill":
            quit ()
        
        # Scraper details odds in thread
        THREAD_DETAILS = Thread(target=scraper_details.scrape_details_oods)
        THREAD_DETAILS.start ()
        
        # Kill thread
        if THREAD_MAIN_STATUS == "kill":
            quit ()
        
        # End threads after reopen time
        
        for _ in range (MINUTES_REOPEN*60):
            if THREAD_MAIN_STATUS == "kill":
                quit ()
            sleep (1)
        
        logger.info ("\nRestarting scraper...\n")
        THREADS_STATUS["basic"] = "ending"
        THREADS_STATUS["details"] = "ending"
        
        # Wait until threads end
        THREAD_BASIC.join ()
        THREAD_DETAILS.join ()
        print ()    
    
if __name__ == "__main__":
    
    # Start main thread
    THREAD_MAIN = Thread(target=main)
    THREAD_MAIN.start ()
    
    
    user_input = input("\nPress 'q' to stop scraper...\n")
    if user_input.lower().strip() == "q":
        THREADS_STATUS["basic"] = "kill"
        THREADS_STATUS["details"] = "kill"
        THREAD_MAIN_STATUS = "kill"
        print ("\nStopping scraper, wait a moment...\n")
        
        # Join threads
        try:
            THREAD_BASIC.join ()
        except:
            pass
        
        try:
            THREAD_DETAILS.join ()     
        except:
            pass
        
        try:
            THREAD_MAIN.join ()
        except:
            pass
        
        # Wait until all threads end
        print ("\nScraper stopped\n")   
