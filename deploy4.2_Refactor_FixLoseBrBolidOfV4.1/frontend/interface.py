# frontend/interface.py

import gradio as gr
import os
import logging
from .callbacks import QuizCallbacks

logger = logging.getLogger(__name__)

class QuizInterface:
    def __init__(self, quiz_manager, data_loader):
        self.quiz_manager = quiz_manager
        self.data_loader = data_loader
        self.callbacks = QuizCallbacks(quiz_manager)
        self.build_interface()

    def build_interface(self):
        self.demo = gr.Blocks(css=self.get_custom_css())
        with self.demo:
            self.state = gr.State({})
            self.setup_components()
            self.setup_event_handlers()

    def get_custom_css(self):
        # Read the custom CSS from styles.css
        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(current_dir, 'styles.css')
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    def setup_components(self):
        self.total_score_display = gr.Textbox(
            label="Total Score",
            value="0",
            interactive=False,
            visible=True,
            elem_classes="total-score-top"
        )
        with gr.Column(elem_classes="quiz-content"):
            self.user_name_input = gr.Textbox(label="Enter Your Name")
            topics = self.data_loader.get_all_topics()
            self.topic_selector = gr.Dropdown(
                label="Select Topic(s)",
                choices=topics,
                multiselect=True
            )
            self.num_questions = gr.Number(label="Enter Number of Questions", value=5, precision=0)
            self.start_button = gr.Button("Start Quiz")

            self.question_box = gr.Textbox(label="Question", interactive=False, visible=False)
            self.user_input = gr.Textbox(label="Your Answer", visible=False)
            self.user_answer_display = gr.Textbox(label="Your Answer", interactive=False, visible=False)
            self.submit_button = gr.Button("Submit", visible=False)
            self.response_box = gr.HTML(label="Response", visible=False)
            self.next_button = gr.Button("Next Question", visible=False)
            
            self.user_feedback = gr.Textbox(label="User Feedback", visible=False)
            self.save_feedback_button = gr.Button("Save Feedback", visible=False)
            
            self.results_table = gr.DataFrame(
                label="Your results:",
                interactive=False,
                visible=False,
                wrap=False
            )
            self.download_button = gr.Button("Download Results", visible=False)
            self.download_file = gr.File(label="Download Results", visible=False)

    def setup_event_handlers(self):
        self.start_button.click(
            self.callbacks.start_quiz,
            inputs=[self.user_name_input, self.topic_selector, self.num_questions],
            outputs=[
                self.question_box, self.user_input, self.submit_button,
                self.user_name_input, self.topic_selector, self.num_questions,
                self.start_button, self.total_score_display,
                self.response_box, self.next_button, self.user_feedback,
                self.save_feedback_button, self.state
            ]
        )
        self.submit_button.click(
            self.callbacks.submit_answer,
            inputs=[self.user_input, self.state],
            outputs=[
                self.question_box, self.user_input, self.user_answer_display,
                self.submit_button, self.next_button, self.response_box,
                self.total_score_display, self.user_feedback, self.save_feedback_button,
                self.results_table, self.download_button, self.state
            ]
        )
        self.next_button.click(
            self.callbacks.next_question,
            inputs=[self.state],
            outputs=[
                self.question_box, self.user_input, self.user_answer_display,
                self.submit_button, self.next_button, self.response_box, self.state
            ]
        )
        self.save_feedback_button.click(
            self.callbacks.save_feedback,
            inputs=[self.user_feedback, self.state],
            outputs=[
                self.user_feedback, self.save_feedback_button,
                self.results_table, self.download_button, self.state
            ]
        )
        self.download_button.click(
            self.callbacks.download_results,
            inputs=[self.state],
            outputs=[self.download_file]
        )

    def launch(self):
        self.demo.launch(share=True,server_name="0.0.0.0", server_port=25008)
