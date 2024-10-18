# backend/utils.py

import threading
import logging

logger = logging.getLogger(__name__)

file_lock = threading.Lock()

def save_results_to_excel(df, output_path):
    with file_lock:
        try:
            df.to_excel(output_path, index=False)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving results to Excel: {e}")
            raise
