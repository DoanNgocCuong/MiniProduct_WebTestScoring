# main.py

import logging
from backend.data_loader import DataLoader
from backend.scorer import Scorer
from backend.quiz_manager import QuizManager
from frontend.interface import QuizInterface
import os
import sys
from dotenv import load_dotenv

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    # Load environment variables
    load_dotenv()
    # Initialize backend components
    file_path = 'Data_MarketingKit.xlsx'  # Ensure this file exists in the project directory
    sheet_name_mc = 'TN_P1P2'
    sheet_name_essay = 'TL_P1P2'
    output_dir = './out'
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory set to {output_dir}")

    data_loader = DataLoader(file_path, sheet_name_mc, sheet_name_essay)

    # Load OpenAI API key from environment variable for security
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key not found. Please set the 'OPENAI_API_KEY' environment variable.")
        sys.exit(1)
    scorer = Scorer(api_key=api_key)
    quiz_manager = QuizManager(data_loader, scorer, output_dir=output_dir)

    # Initialize frontend interface
    quiz_interface = QuizInterface(quiz_manager, data_loader)
    logger.info("Launching Quiz Interface...")
    quiz_interface.launch()

if __name__ == "__main__":
    main()
