# backend/utils.py

import threading
import logging

logger = logging.getLogger(__name__)

file_lock = threading.Lock()

def save_results_to_excel(df, output_path):
    with file_lock:
        df.to_excel(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
