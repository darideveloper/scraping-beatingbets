import os
import logging
from dotenv import load_dotenv
load_dotenv ()

DEBUG = os.getenv ("DEBUG") == "true"

# logs to file
logging.basicConfig(filename='.log', format='%(asctime)s - %(filename)s (%(lineno)s) - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
