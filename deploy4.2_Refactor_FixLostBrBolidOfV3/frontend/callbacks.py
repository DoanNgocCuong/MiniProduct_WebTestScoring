# frontend/callbacks.py

import asyncio
import logging
import pandas as pd
import tempfile
from gradio import update
import gradio as gr
from .utils import file_lock
from backend.utils import save_results_to_excel

logger = logging.getLogger(__name__)

class QuizCallbacks:
    def __init__(self, quiz_manager):
        self.quiz_manager = quiz_manager

    def start_quiz(self, user_name, selected_topics, num_questions):
        try:
            state = self.quiz_manager.initialize_quiz(user_name, selected_topics, int(num_questions))
            question = state['questions'][0]['question']
            total_score_text = f"Total Score - {user_name} - {', '.join(selected_topics)} - {state['num_questions']} questions"
            return (
                update(value=question, visible=True),
                update(visible=True, value=""),
                update(visible=True),
                update(visible=False),  # Hide user_name_input
                update(visible=False),  # Hide topic_selector
                update(visible=False),  # Hide num_questions
                update(visible=False),  # Hide start_button
                update(value="0", label=total_score_text),  # total_score_display
                update(visible=False),  # Hide response_box
                update(visible=False),  # Hide next_button
                update(visible=False),  # Hide user_feedback
                update(visible=False),  # Hide save_feedback_button
                state
            )
        except Exception as e:
            logger.error(f"Error starting quiz: {e}")
            return (
                update(value=str(e), visible=True),
                update(visible=False),
                update(visible=False),
                update(visible=True),
                update(visible=True),
                update(visible=True),
                update(visible=True),
                update(value="0"),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                {}
            )

    async def submit_answer(self, user_answer, state):
        feedback, state = await self.quiz_manager.process_answer(state, user_answer)
        total_score_text = f"Total Score - {state['user_name']} - {', '.join(state['selected_topic'])} - {state['num_questions']} questions"
        is_quiz_finished = state['current_question_index'] >= state['num_questions']
        max_possible_score = state['num_mc'] * 10 + state['num_essay'] * 10
        if is_quiz_finished:
            df = pd.DataFrame(state['results'])
            return (
                update(value="Quiz finished!", visible=True),   # question_box
                update(visible=False),                          # user_input
                update(value=user_answer, visible=False),       # user_answer_display
                update(visible=False),                          # submit_button
                update(visible=False),                          # next_button
                update(value=feedback, visible=True),           # response_box
                update(value=f"{state['total_score']}/{max_possible_score}", label=total_score_text),  # total_score_display
                update(visible=True),                           # user_feedback
                update(visible=True),                           # save_feedback_button
                update(visible=False),                          # results_table
                update(visible=False),                          # download_button
                state
            )
        else:
            return (
                update(value=state['questions'][state['current_question_index'] - 1]['question'], visible=True),  # question_box
                update(visible=False),                          # user_input
                update(value=user_answer, visible=True),        # user_answer_display
                update(visible=False),                          # submit_button
                update(visible=True),                           # next_button
                update(value=feedback, visible=True),           # response_box
                update(value=f"{state['total_score']}/{max_possible_score}", label=total_score_text),  # total_score_display
                update(visible=False),                          # user_feedback
                update(visible=False),                          # save_feedback_button
                update(visible=False),                          # results_table
                update(visible=False),                          # download_button
                state
            )

    def next_question(self, state):
        question = self.quiz_manager.get_next_question(state)
        if question == "Quiz finished!":
            return (
                update(value=question, visible=True),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                state
            )
        else:
            return (
                update(value=question, visible=True),
                update(visible=True, value=""),  # user_input
                update(visible=False),           # user_answer_display
                update(visible=True),            # submit_button
                update(visible=False),           # next_button
                update(visible=False),           # response_box
                state
            )

    def save_feedback(self, feedback, state):
        try:
            state['user_feedback'] = feedback
            self.quiz_manager.finalize_quiz(state)
            df = pd.DataFrame(state['results'])
            return (
                update(visible=False),           # user_feedback
                update(visible=False),           # save_feedback_button
                update(value=df, visible=False),  # Hide results_table initially
                update(visible=True),            # download_button
                state
            )
        except Exception as e:
            logger.error(f"Lỗi khi lưu feedback: {e}")
            return (
                update(value=f"Lỗi khi lưu feedback: {e}", visible=True),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                state
            )

    def download_results(self, state):
        try:
            df = pd.DataFrame(state['results'])
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.xlsx') as temp_file:
                df.to_excel(temp_file.name, index=False)
            logger.info(f"Data saved to temporary file: {temp_file.name}")
            return gr.File(value=temp_file.name, visible=True, label="Download Results")
        except Exception as e:
            logger.error(f"Lỗi khi tạo file download: {e}")
            return (
                gr.update(value=f"Lỗi khi tạo file download: {e}", visible=True),
            )
