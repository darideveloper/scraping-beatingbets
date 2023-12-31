import os
from time import sleep
from threading import Thread
from datetime import datetime
from scraper import Scraper
from scraper_basic import ScraperBasic
from scraper_details import ScraperDetails
from logs import logger
from dotenv import load_dotenv

# Env variables
load_dotenv ()
MINUTES_REOPEN = int(os.getenv("MINUTES_REOPEN"))

THREAD_BASIC = None
THREAD_DETAILS = None

def main ():
    """ Start scraper with threads """
    
    global THREAD_BASIC
    global THREAD_DETAILS

    
    while True:
        
        Scraper.threads_status["main"] = "running"
        
        try:
        
            # Load matches
            scraper = Scraper()
            scraper.load_matches ()
            scraper.kill ()
            
            # Instance browsers
            scraper_basic = ScraperBasic()
            scraper_details = ScraperDetails()
            
            # Kill thread
            if Scraper.threads_status["main"] == "kill":
                quit ()
            
            # Scrape general data only one time
            is_done = scraper_basic.scrape_basic_general ()
            if not is_done:
                continue
            sleep (2)
            
            # Kill thread
            if Scraper.threads_status["main"] == "kill":
                quit ()
            
            # Scraper basic odds in thread
            THREAD_BASIC = Thread(target=scraper_basic.scrape_basic_oods)
            THREAD_BASIC.start()
            
            # Kill thread
            if Scraper.threads_status["main"] == "kill":
                quit ()
            
            # Scraper details odds in thread
            THREAD_DETAILS = Thread(target=scraper_details.scrape_details_oods)
            THREAD_DETAILS.start ()
            
            # Kill thread
            if Scraper.threads_status["main"] == "kill":
                quit ()
        
        except Exception as e:
            logger.error (f"Can't starting scraper. Restarting scraper...")
            logger.error (e)
            continue    
        
        # End threads after reopen time
        restarted = False
        for _ in range (MINUTES_REOPEN*60):
            
            # Detect killed by user
            if Scraper.threads_status["main"] == "kill":
                quit ()
            
            # Detect restart from threads
            if Scraper.threads_status["main"] == "restart":
                restarted = True
                break
            
            # Validte if threads keep running
            if not (THREAD_BASIC.is_alive() and THREAD_DETAILS.is_alive()):
                break
            
            sleep (1)
        
        # Regular rnd thread after time
        if not restarted:
            logger.info ("\nRestarting scraper...\n")
            Scraper.threads_status["basic"] = "ending"
            Scraper.threads_status["details"] = "ending"
        
        # Wait until threads end
        THREAD_BASIC.join ()
        THREAD_DETAILS.join ()
        
        # Kill all chrome process for windows
        sleep (120)
        os.system("taskkill /f /im chrome.exe")

if __name__ == "__main__":
    
    # Start main thread
    THREAD_MAIN = Thread(target=main)
    THREAD_MAIN.start ()
    
    user_input = input("\nPress 'q' to stop scraper...\n")
    if user_input.lower().strip() == "q":
        Scraper.threads_status["basic"] = "kill"
        Scraper.threads_status["details"] = "kill"
        Scraper.threads_status["main"] = "kill"
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
