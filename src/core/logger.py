import logging
import os

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(__file__), '../../logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'pipeline.log')),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    return logging.getLogger(name)
