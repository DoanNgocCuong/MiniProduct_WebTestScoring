# backend/data_loader.py

import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, file_path, sheet_name_mc, sheet_name_essay):
        self.file_path = file_path
        self.sheet_name_mc = sheet_name_mc
        self.sheet_name_essay = sheet_name_essay

    def load_quiz_data(self, sheet_name):
        logger.info(f"Loading data from file: {self.file_path}, sheet: {sheet_name}")
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name, engine='openpyxl')
            df = df[df['topic'].notna()]
        except Exception as e:
            logger.error(f"Lỗi khi đọc tệp Excel: {e}")
            raise
        questions = df['question'].tolist()
        checking_answers = df['checking_answer'].tolist()
        explain_answers = df['explain_answer'].tolist() if 'explain_answer' in df.columns else [None] * len(questions)
        topics = df['topic'].tolist()
        logger.info(f"Loaded {len(questions)} questions from sheet {sheet_name}")
        return questions, checking_answers, explain_answers, topics

    def load_all_data(self):
        logger.info("Loading all data from Excel file...")
        mc_data = self.load_quiz_data(self.sheet_name_mc)
        essay_data = self.load_quiz_data(self.sheet_name_essay)
        return mc_data, essay_data

    def get_all_topics(self):
        mc_data, essay_data = self.load_all_data()
        topics_mc = mc_data[3]
        topics_essay = essay_data[3]
        all_topics = list(set(topics_mc + topics_essay))
        return all_topics

    def get_questions_by_topic(self, selected_topics):
        mc_data, essay_data = self.load_all_data()
        mc_questions = [
            {'question': q, 'checking_answer': ca, 'explain_answer': ea, 'topic': t, 'is_essay': False}
            for q, ca, ea, t in zip(*mc_data) if t in selected_topics
        ]
        essay_questions = [
            {'question': q, 'checking_answer': ca, 'explain_answer': ea, 'topic': t, 'is_essay': True}
            for q, ca, ea, t in zip(*essay_data) if t in selected_topics
        ]
        return mc_questions, essay_questions
