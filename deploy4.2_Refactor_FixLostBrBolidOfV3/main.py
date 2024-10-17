# main.py

import logging
from backend.data_loader import DataLoader
from backend.scorer import Scorer
from backend.quiz_manager import QuizManager
from frontend.interface import QuizInterface
import os
from dotenv import load_dotenv
load_dotenv()

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize backend components
    file_path = 'Data_MarketingKit.xlsx'
    sheet_name_mc = 'TN_P1P2'
    sheet_name_essay = 'TL_P1P2'
    data_loader = DataLoader(file_path, sheet_name_mc, sheet_name_essay)

    api_key = os.getenv('OPENAI_API_KEY')  
    scorer = Scorer(api_key=api_key)

    output_dir = './out'
    os.makedirs(output_dir, exist_ok=True)

    quiz_manager = QuizManager(data_loader, scorer, output_dir=output_dir)

    # Initialize frontend interface
    quiz_interface = QuizInterface(quiz_manager, data_loader)
    quiz_interface.launch()

if __name__ == "__main__":
    main()
