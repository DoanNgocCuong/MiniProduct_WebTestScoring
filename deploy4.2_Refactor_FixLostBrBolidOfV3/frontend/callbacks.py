# frontend/callbacks.py

import asyncio
import logging
import pandas as pd
import tempfile
from gradio import update, File

logger = logging.getLogger(__name__)

class QuizCallbacks:
    def __init__(self, quiz_manager):
        self.quiz_manager = quiz_manager

    def start_quiz(self, user_name, selected_topics, num_questions):
        try:
            state = self.quiz_manager.initialize_quiz(user_name, selected_topics, int(num_questions))
            question = state['questions'][0]['question']
            total_score_text = f"Total Score - {state['user_name']} - {', '.join(state['selected_topics'])} - {state['num_questions']} questions"
            return (
                update(value=question, visible=True),
                update(visible=True, value=""),
                update(visible=True),
                state,
                update(value="0", label=total_score_text),
                update(visible=False),  # Hide name input
                update(visible=False),  # Hide topic selector
                update(visible=False),  # Hide number of questions input
                update(visible=False)   # Hide start button
            )
        except Exception as e:
            logger.error(f"Error starting quiz: {e}")
            return (
                update(value=str(e), visible=True),
                update(visible=False),
                update(visible=False),
                {},
                update(value="0", label="Total Score"),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                update(visible=False)
            )

    async def submit_answer(self, user_answer, state):
        feedback, state = await self.quiz_manager.process_answer(state, user_answer)
        total_score_text = f"Total Score - {state['user_name']} - {', '.join(state['selected_topics'])} - {state['num_questions']} questions"
        is_quiz_finished = state['current_question_index'] >= state['num_questions']

        if is_quiz_finished:
            df = pd.DataFrame(state['results'])
            return (
                update(value=feedback, visible=True),
                update(visible=False),
                update(value=state['total_score'], label=total_score_text),
                state,
                update(visible=True),  # Show feedback input
                update(visible=True),  # Show save feedback button
                update(visible=False),
                update(visible=False)
            )
        else:
            return (
                update(value=feedback, visible=True),
                update(visible=True),
                update(value=state['total_score'], label=total_score_text),
                state,
                update(visible=False),
                update(visible=False),
                update(visible=False),
                update(visible=False)
            )

    def next_question(self, state):
        if state['current_question_index'] < state['num_questions']:
            question = self.quiz_manager.get_next_question(state)
            return (
                update(value=question, visible=True),
                update(visible=True, value=""),
                update(visible=True),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                update(visible=False),
                state
            )
        else:
            return (
                update(value="Quiz finished!", visible=True),
                update(visible=False),
                update(visible=True),
                update(visible=False),
                update(visible=True),
                update(visible=False),
                update(visible=False),
                state
            )

    def save_feedback(self, feedback, state):
        try:
            for result in state['results']:
                result['user_feedback'] = feedback
            df = pd.DataFrame(state['results'])
            self.quiz_manager.finalize_quiz(state)
            return (
                update(visible=False),
                update(visible=False),
                update(value=df, visible=True),
                update(visible=True),
                state
            )
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
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
            logger.info(f"Results ready for download: {temp_file.name}")
            return File(temp_file.name, label="Download Results")
        except Exception as e:
            logger.error(f"Error preparing download: {e}")
            return File("", label="Download Results")
