# backend/quiz_manager.py

import asyncio
import logging
import random
import pandas as pd
from datetime import datetime
from .scorer import Scorer
from .utils import save_results_to_excel

logger = logging.getLogger(__name__)

class QuizManager:
    def __init__(self, data_loader, scorer, output_dir='./out'):
        self.data_loader = data_loader
        self.scorer = scorer
        self.output_dir = output_dir

    def initialize_quiz(self, user_name, selected_topics, num_questions):
        mc_questions, essay_questions = self.data_loader.get_questions_by_topic(selected_topics)
        total_available_questions = len(mc_questions) + len(essay_questions)

        if total_available_questions == 0:
            raise ValueError("Không có câu hỏi nào cho chủ đề đã chọn.")

        num_questions = min(num_questions, total_available_questions)
        desired_essay = int(num_questions * 0.7)
        actual_essay = min(desired_essay, len(essay_questions))
        actual_mc = min(num_questions - actual_essay, len(mc_questions))

        selected_essay = random.sample(essay_questions, actual_essay) if essay_questions else []
        selected_mc = random.sample(mc_questions, actual_mc) if mc_questions else []

        questions = selected_essay + selected_mc
        random.shuffle(questions)

        quiz_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_safe_user_name = user_name.replace(" ", "")
        file_safe_topic = "_".join(selected_topics).replace(" ", "_")
        date_str = datetime.now().strftime("%d%m%Y")
        output_path = f"{self.output_dir}/{file_safe_user_name}_{file_safe_topic}_{date_str}_results.xlsx"

        state = {
            'user_name': user_name,
            'selected_topic': selected_topics,
            'num_questions': num_questions,
            'questions': questions,
            'current_question_index': 0,
            'total_score': 0,
            'results': [],
            'quiz_start_time': quiz_start_time,
            'output_path': output_path,
            'num_mc': actual_mc,
            'num_essay': actual_essay,
            'user_feedback': ''
        }

        logger.info(f"Khởi tạo quiz cho người dùng: {user_name}")
        logger.info(f"Chọn {actual_essay} câu tự luận và {actual_mc} câu trắc nghiệm.")

        return state

    async def process_answer(self, state, user_answer):
        index = state['current_question_index']
        question_data = state['questions'][index]
        question = question_data['question']
        checking_answer = question_data['checking_answer']
        explain_answer = question_data['explain_answer']
        is_essay = question_data['is_essay']

        if user_answer:
            if is_essay:
                try:
                    response = await self.scorer.score_essay(question, checking_answer, user_answer)
                    point = sum(criterion['score'] for criterion in response.values())
                    feedback = self.format_essay_feedback(response, explain_answer)
                except Exception as e:
                    logger.error(f"Lỗi khi chấm điểm câu tự luận: {str(e)}")
                    point = 0
                    feedback = f"Có lỗi xảy ra khi chấm điểm: {str(e)}. Vui lòng thử lại."
            else:
                is_correct = user_answer.strip().upper() == checking_answer.strip().upper()
                point = 10 if is_correct else 0
                feedback = self.format_mc_feedback(is_correct, explain_answer)

            state['total_score'] += point
            state['results'].append({
                'user_name': state['user_name'],
                'stt': index + 1,
                'question_type': 'essay' if is_essay else 'mc',
                'question': question,
                'user_answer': user_answer,
                'point': point,
                'assistant_response': feedback.replace('<br>', '\n').replace('<b>', '').replace('</b>', ''),
                'topics': state["selected_topic"] if isinstance(state["selected_topic"], list) else [state["selected_topic"]]
            })

            logger.info(f"Câu hỏi {index + 1} đã được trả lời. Điểm: {point}")
        else:
            feedback = ""

        state['current_question_index'] += 1

        if state['current_question_index'] >= state['num_questions']:
            self.finalize_quiz(state)

        return feedback, state

    def format_essay_feedback(self, response, explain_answer):
        criterion_names = {
            "accuracy": "Tính chính xác của câu trả lời",
            "completeness": "Độ chi tiết của câu trả lời",
            "clarity": "Tính mạch lạc, rõ ràng"
        }
        max_scores = {
            "accuracy": 5,
            "completeness": 3,
            "clarity": 2
        }
        comments = [f"+ <b>{criterion_names[criterion]}</b>: {response[criterion]['score']}/{max_scores[criterion]}.<br>  Comment: {response[criterion]['reason']}"
                    for criterion in response]
        total_score = sum(response[criterion]['score'] for criterion in response)
        feedback = f"<b>Điểm nhận được:</b> {total_score}/10.<br>" + "<br>".join(comments)
        full_answer = explain_answer.replace('\n', '<br>') if explain_answer else ""
        feedback += f"<br>------<br><b>Câu trả lời tham khảo</b>:<br>{full_answer}"
        return feedback

    def format_mc_feedback(self, is_correct, explain_answer):
        result = "Đúng!" if is_correct else "Sai!"
        full_answer = explain_answer.replace('\n', '<br>') if explain_answer else ""
        feedback = f"{result}<br>{full_answer}"
        return feedback

    def finalize_quiz(self, state):
        quiz_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for result in state['results']:
            result['time_start'] = state['quiz_start_time']
            result['time_end'] = quiz_end_time
            result['total_score'] = state['total_score']
            result['user_feedback'] = state.get('user_feedback', '')

        df = pd.DataFrame(state['results'])
        try:
            save_results_to_excel(df, state['output_path'])
            logger.info("Quiz finalized và kết quả đã được lưu.")
        except Exception as e:
            logger.error(f"Lỗi khi lưu kết quả quiz: {e}")

    def get_next_question(self, state):
        if state['current_question_index'] < state['num_questions']:
            question_data = state['questions'][state['current_question_index']]
            return question_data['question']
        else:
            return "Quiz finished!"
        
    def finalize_quiz(self, state):
        quiz_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for result in state['results']:
            result['time_start'] = state['quiz_start_time']
            result['time_end'] = quiz_end_time
            result['total_score'] = state['total_score']
            result['user_feedback'] = state.get('user_feedback', '')
        df = pd.DataFrame(state['results'])
        try:
            save_results_to_excel(df, state['output_path'])
            logger.info("Quiz finalized và kết quả đã được lưu.")
        except Exception as e:
            logger.error(f"Lỗi khi lưu kết quả quiz: {e}")
    
    def get_initial_state(self, state):
        # Trả về state ban đầu để lưu trữ
        return state