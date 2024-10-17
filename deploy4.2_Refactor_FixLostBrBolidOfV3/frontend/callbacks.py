# frontend/callbacks.py

import asyncio
import logging
import pandas as pd
import tempfile
from gradio import update
import gradio as gr

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
                state,
                update(value="0", label=total_score_text)
            )
        except Exception as e:
            logger.error(f"Error starting quiz: {e}")
            return (
                update(value=str(e), visible=True),
                update(visible=False),
                update(visible=False),
                {},
                update(value="0")
            )

    async def submit_answer(self, user_answer, state):
        feedback, state = await self.quiz_manager.process_answer(state, user_answer)
        total_score_text = f"Total Score - {state['user_name']} - {', '.join(state['selected_topics'])} - {state['num_questions']} questions"
        is_quiz_finished = state['current_question_index'] >= state['num_questions']
        if is_quiz_finished:
            df = pd.DataFrame(state['results'])
            return (
                update(value="Quiz finished!", visible=True),
                update(visible=False),
                update(value=user_answer, visible=True),
                update(visible=False),
                update(visible=False),
                update(value=feedback, visible=True),
                update(value=f"{state['total_score']}", label=total_score_text),
                state,
                update(value=df, visible=True),
                update(visible=True)
            )
        else:
            return (
                update(value=state['questions'][state['current_question_index'] - 1]['question'], visible=True),
                update(visible=False),
                update(value=user_answer, visible=True),
                update(visible=False),
                update(visible=True),
                update(value=feedback, visible=True),
                update(value=f"{state['total_score']}", label=total_score_text),
                state,
                update(visible=False),
                update(visible=False)
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
                update(visible=True, value=""),
                update(visible=False),
                update(visible=True),
                update(visible=False),
                update(visible=False),
                state
            )

    def save_feedback(self, feedback, state):
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

    def download_results(self, state):
        df = pd.DataFrame(state['results'])
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.xlsx') as temp_file:
            df.to_excel(temp_file.name, index=False)
        return gr.File(value=temp_file.name, visible=True, label="Download Results")
