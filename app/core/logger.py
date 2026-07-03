import logging 
import sys 

def steup_logging():
  """Configuring the root logger for the entire application"""
  logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] -%(funcName)s() -%(levelName)s - %(message)s"
    handlers=[logging.StreamHandler(sys.stdout)]
  )
