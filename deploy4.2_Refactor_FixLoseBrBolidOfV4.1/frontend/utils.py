# frontend/utils.py

import threading
import logging

logger = logging.getLogger(__name__)

file_lock = threading.Lock()
