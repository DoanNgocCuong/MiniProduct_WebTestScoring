import asyncio
import aiohttp
from datetime import datetime
import pandas as pd
import gradio as gr
import json
from openai import AsyncOpenAI, APIError, RateLimitError
import os
import random
import tempfile
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import threading
import logging
from functools import lru_cache
from circuitbreaker import circuit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_lock = threading.Lock()

def update_topic_selector():
    questions, checking_answers, explain_answers, topics, questions_mc, questions_essay, topics_mc, topics_essay = load_all_data(file_path, sheet_name_mc, sheet_name_essay)
    new_topics = list(set(topics_mc + topics_essay))
    return gr.update(choices=new_topics)

def load_quiz_data(file_path, sheet_name):
    logger.info(f"Loading data from file: {file_path}, sheet: {sheet_name}")
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        logger.error(f"Lỗi khi đọc tệp Excel: {e}")
        raise
    df = df[df['topic'].notna()]
    questions = df['question'].tolist()
    checking_answers = df['checking_answer'].tolist()
    explain_answers = df['explain_answer'].tolist() if 'explain_answer' in df.columns else [None] * len(questions)
    topics = df['topic'].tolist()
    logger.info(f"Loaded data from sheet {sheet_name}. Number of questions: {len(questions)}")
    return questions, checking_answers, explain_answers, topics

def load_all_data(file_path, sheet_name_mc, sheet_name_essay):
    logger.info("Loading all data from Excel file...")
    questions_mc, checking_answers_mc, explain_answers_mc, topics_mc = load_quiz_data(file_path, sheet_name_mc)
    questions_essay, checking_answers_essay, explain_answers_essay, topics_essay = load_quiz_data(file_path, sheet_name_essay)
   
    topics = list(set(topics_mc + topics_essay))
    questions = questions_mc + questions_essay
    checking_answers = checking_answers_mc + checking_answers_essay
    explain_answers = explain_answers_mc + explain_answers_essay
    
    logger.info(f"Total questions loaded: {len(questions)}")
    logger.info("Data đã được load lại")
    return questions, checking_answers, explain_answers, topics, questions_mc, questions_essay, topics_mc, topics_essay

def update_filtered_is_essay_list(questions_mc, questions_essay, filtered_questions):
    is_essay_list = [q in questions_essay for q in filtered_questions]
    return is_essay_list

@circuit(failure_threshold=5, recovery_timeout=60)
async def scoring_short_essay_questions(QUESTION, CHECKING_ANSWER, USER_ANSWER):
    async with AsyncOpenAI(api_key="") as client:
        prompt = f"""
                Act: You are an expert at scoring short essay questions. 
                You are provided with 1 QUESTION and 1 CHECKING ANSWER for that QUESTION.
                After USER enters the USER ANSWER, you will check USER ANSWER with CHECKING ANSWER. 

                Instructions: 
                - point: check USER ANSWER with CHECKING ANSWER to score on a 0-5 point scale 
                    +, Criteria: Detail level, Accuracy, Relevance to the question
                    0 = No correct or relevant answer.
                - comment: briefly in 2 sentences: the reason you gave such a score (in Vietnamese)

                Output: JSON format with 2 keys: point and comment
                QUESTION:
                {QUESTION}
                CHECKING ANSWER:
                {CHECKING_ANSWER}
                """


        try:
            async with asyncio.timeout(10):
                completion = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": USER_ANSWER},
                    ],
                    temperature=0,
                    max_tokens=6000,
                )
            
            logger.info("Đã gửi yêu cầu chấm điểm đến OpenAI")
            return json.loads(completion.choices[0].message.content)
        except RateLimitError:
            logger.warning("Rate limit exceeded. Retrying after a delay.")
            await asyncio.sleep(5)
            return await scoring_short_essay_questions(QUESTION, CHECKING_ANSWER, USER_ANSWER)
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in scoring: {str(e)}")
            raise

@lru_cache(maxsize=100)
def cached_scoring(question, answer):
    return asyncio.run(scoring_short_essay_questions(question, answer))

async def quiz_logic(questions, checking_answers, explain_answers, questions_mc, questions_essay, user_answer, filtered_questions, state):
    try: 
        current_question_index = state["current_question_index"]
        total_score = state["total_score"]
        results = state["results"]
        user_name = state["user_name"]
        is_essay = state["filtered_is_essay_list"][current_question_index]
        quiz_start_time = state["quiz_start_time"]
        output_path = state["output_path"]
        num_questions = state["num_questions"]
    except KeyError as e:
        logger.error(f"KeyError in quiz_logic: {str(e)}")
        logger.error(f"Current state: {state}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in quiz_logic: {str(e)}")
        raise

    logger.info(f"Current question index: {current_question_index}, Total questions: {num_questions}")

    if user_answer:
        if is_essay:
            try:
                response = await scoring_short_essay_questions(questions[current_question_index], checking_answers[current_question_index], user_answer)
                point = response['point']
                comment = response['comment']
                full_answer = explain_answers[current_question_index]
                total_score += point
                assistant_response = f"- Point: {point}/5. {comment}\n- Câu trả lời tham khảo: \n\"\"\"\n{full_answer}\n\"\"\" \n"
            except Exception as e:
                logger.error(f"Error in scoring essay question: {str(e)}")
                assistant_response = f"Có lỗi xảy ra khi chấm điểm: {str(e)}. Vui lòng thử lại."
                point = 0
        else:
            if user_answer.strip().upper() == checking_answers[current_question_index]:
                assistant_response = f"Đúng! \n{explain_answers[current_question_index]}" if explain_answers[current_question_index] else "Đúng! Get 1 point."
                point = 1
                total_score += 1
            else:
                assistant_response = f"Sai! \n{explain_answers[current_question_index]}" if explain_answers[current_question_index] else "Sai! Get 0 point."
                point = 0

        results.append({
            'user_name': user_name,
            'stt': current_question_index + 1,
            'question_type': 'essay' if is_essay else 'mc',
            'question': questions[current_question_index],
            'user_answer': user_answer,
            'point': point,
            'assistant_response': assistant_response,
        })

        logger.info(f"Câu hỏi {current_question_index + 1} đã được trả lời. Điểm: {point}")
        logger.info(f"Current results: {results}")
        
        current_question_index += 1
    else:
        assistant_response = ""

    if current_question_index >= num_questions:
        quiz_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for result in results:
            result['time_start'] = quiz_start_time
            result['time_end'] = quiz_end_time
            result['total_score'] = total_score
        
        df = pd.DataFrame(results)
        
        logger.info("DataFrame after quiz completion:")
        logger.info(df.to_string())
        
        with file_lock:
            df.to_excel(output_path, index=False)

        logger.info(f"File kết quả đã được lưu thành công tại: {output_path}")
        
        num_mc = sum(1 for q in filtered_questions if q in questions_mc)
        num_essay = sum(1 for q in filtered_questions if q in questions_essay)
        max_possible_score = state["num_mc"] * 1 + state["num_essay"] * 5

        assistant_response += f"\nTổng điểm của {user_name} là: {total_score}/{max_possible_score}"
        state["current_question_index"] = current_question_index
        state["total_score"] = total_score
        state["results"] = results
        return assistant_response, gr.update(visible=True), gr.update(visible=False), state, gr.update(visible=True, value=df)

    state["current_question_index"] = current_question_index
    state["total_score"] = total_score
    state["results"] = results
    return assistant_response, gr.update(visible=True), gr.update(visible=True), state, gr.update(visible=False)

def create_quiz_interface(file_path, sheet_name_mc, sheet_name_essay, output_dir):
    logger.info("Creating quiz interface")
    
    questions, checking_answers, explain_answers, topics, questions_mc, questions_essay, topics_mc, topics_essay = load_all_data(file_path, sheet_name_mc, sheet_name_essay)
    logger.info("Data loaded successfully on initial load")

    custom_css = """
    .total-score-top {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background-color: #f0f0f0;
        padding: 10px;
        z-index: 1000;
        text-align: center;
        font-weight: bold;
        border-bottom: 1px solid #ddd;
    }
    .quiz-content {
        margin-top: 50px;
    }
    """

    with gr.Blocks() as demo:
        gr.HTML(f"<style>{custom_css}</style>")
        
        total_score_display = gr.Textbox(
            label="Total Score", 
            value="0", 
            interactive=False, 
            visible=True,
            elem_classes="total-score-top"
        )
        
        with gr.Column(elem_classes="quiz-content"):
            state = gr.State({
                "current_question_index": 0,
                "total_score": 0,
                "results": [],
                "user_name": "",
                "selected_topic": "",
                "filtered_questions": [],
                "filtered_checking_answers": [],
                "filtered_explain_answers": [],
                "filtered_is_essay_list": [],
                "quiz_start_time": "",
                "output_path": "",
                "num_questions": 5,
                "num_mc": 0,
                "num_essay": 0
            })

            user_name_input = gr.Textbox(label="Enter Your Name")
            topic_selector = gr.Dropdown(label="Select Topic", choices=topics)
            num_questions = gr.Textbox(label="Enter Number of Questions", placeholder="Enter the number of questions you want")
            start_button = gr.Button("Start")

            question_box = gr.Textbox(label="Question", interactive=False, visible=False)
            user_input = gr.Textbox(label="Your Answer", visible=False)
            user_answer_display = gr.Textbox(label="Your Answer", interactive=False, visible=False)  # Thêm dòng này
            submit_button = gr.Button("Submit", visible=False)
            response_box = gr.Textbox(label="Response", interactive=False, visible=False)
            next_button = gr.Button("Next Question", visible=False)
            
            user_feedback = gr.Textbox(label="User feedback", visible=False)
            save_feedback_button = gr.Button("Save Feedback", visible=False)
            
            results_table = gr.DataFrame(
                label="Your results have been saved successfully",
                interactive=False,
                visible=False,
                wrap=True
            )
            download_button = gr.Button("Download Results", visible=False)

        demo.load(update_topic_selector, outputs=[topic_selector])

        def start_quiz(user_name_input, topic_selector_input, num_questions_input, state):
            logger.info("Quiz started. Reloading data.")
            questions, checking_answers, explain_answers, topics, questions_mc, questions_essay, topics_mc, topics_essay = load_all_data(file_path, sheet_name_mc, sheet_name_essay)
            logger.info("Data reloaded for new quiz")

            new_topics = list(set(topics_mc + topics_essay))
            
            if not user_name_input or not topic_selector_input or not num_questions_input:
                return (
                    gr.update(value="Vui lòng nhập tên, chọn chủ đề và số câu hỏi trước khi bắt đầu.", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True, choices=new_topics),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(value=f"{state['total_score']}", visible=True, label=f"Total Score - {user_name_input} - {topic_selector_input} - {len(state['filtered_questions'])} questions"),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    state
                )

            try:
                num_questions = int(num_questions_input)
                if num_questions <= 0:
                    return (
                        gr.update(value="Vui lòng nhập số câu hỏi lớn hơn 0.", visible=True),
                        gr.update(visible=False),
                        gr.update(visible=True),
                        gr.update(visible=True, choices=new_topics),
                        gr.update(visible=True),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(value=f"{state['total_score']}", visible=True, label=f"Total Score - {user_name_input} - {topic_selector_input} - {len(state['filtered_questions'])} questions"),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        state
                    )
            except ValueError:
                return (
                    gr.update(value="Vui lòng nhập một số hợp lệ cho số câu hỏi.", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True, choices=new_topics),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(value=f"{state['total_score']}", visible=True, label=f"Total Score - {user_name_input} - {topic_selector_input} - {len(state['filtered_questions'])} questions"),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    state
                )

            state.update({
                "user_name": user_name_input,
                "selected_topic": topic_selector_input,
                "num_questions": num_questions,
                "current_question_index": 0,
                "total_score": 0,
                "results": []
            })

            quiz_start_time = datetime.now()
            state["quiz_start_time"] = quiz_start_time.strftime("%Y-%m-%d %H:%M:%S")
            date_str = quiz_start_time.strftime("%d%m%Y")
            file_safe_user_name = user_name_input.replace(" ", "")
            file_safe_topic = topic_selector_input.replace(" ", "_")

            state["output_path"] = os.path.join(output_dir, f"{file_safe_user_name}_{file_safe_topic}_{date_str}_results.xlsx")

            logger.info(f"Chủ đề đã chọn: {topic_selector_input}")

            mc_questions = [q for q, t in zip(questions_mc, topics_mc) if t == topic_selector_input]
            essay_questions = [q for q, t in zip(questions_essay, topics_essay) if t == topic_selector_input]
            logger.info(f"Số câu trắc nghiệm: {len(mc_questions)}, Số câu tự luận: {len(essay_questions)}")

            total_questions = int(num_questions_input)
            
            if len(mc_questions) == 0:
                logger.warning(f"Không có câu hỏi trắc nghiệm cho chủ đề {topic_selector_input}")
                actual_essay = min(total_questions, len(essay_questions))
                actual_mc = 0
            elif len(essay_questions) == 0:
                logger.warning(f"Không có câu hỏi tự luận cho chủ đề {topic_selector_input}")
                actual_mc = min(total_questions, len(mc_questions))
                actual_essay = 0
            else:
                desired_essay = int(total_questions * 0.7)
                actual_essay = min(desired_essay, len(essay_questions))
                actual_mc = min(total_questions - actual_essay, len(mc_questions))

            state["num_mc"] = actual_mc
            state["num_essay"] = actual_essay

            logger.info(f"Chọn {actual_essay} câu tự luận và {actual_mc} câu trắc nghiệm")

            selected_essay = random.sample(essay_questions, actual_essay) if essay_questions else []
            selected_mc = random.sample(mc_questions, actual_mc) if mc_questions else []

            state["filtered_questions"] = selected_essay + selected_mc
            random.shuffle(state["filtered_questions"])

            if not state["filtered_questions"]:
                return (
                    gr.update(value="Không có câu hỏi nào cho chủ đề này. Vui lòng chọn chủ đề khác.", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True, choices=new_topics),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(value=f"{state['total_score']}", visible=True, label=f"Total Score - {user_name_input} - {topic_selector_input} - {len(state['filtered_questions'])} questions"),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    state
                )

            state["filtered_checking_answers"] = [checking_answers[questions.index(q)] for q in state["filtered_questions"]]
            state["filtered_explain_answers"] = [explain_answers[questions.index(q)] for q in state["filtered_questions"]]
            state["filtered_is_essay_list"] = [q in questions_essay for q in state["filtered_questions"]]

            state["filtered_questions"] = state["filtered_questions"][:num_questions]
            state["filtered_checking_answers"] = state["filtered_checking_answers"][:num_questions]
            state["filtered_explain_answers"] = state["filtered_explain_answers"][:num_questions]
            state["filtered_is_essay_list"] = state["filtered_is_essay_list"][:num_questions]

            logger.info(f"Final number of questions: {len(state['filtered_questions'])}")

            quiz_result, _, _, state, _ = asyncio.run(quiz_logic(
                state["filtered_questions"], state["filtered_checking_answers"], state["filtered_explain_answers"],
                questions_mc, questions_essay, "", state["filtered_questions"], state
            ))

            question = state["filtered_questions"][0]
            
            return (
                gr.update(value=question, visible=True),
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=f"{state['total_score']}", visible=True, label=f"Total Score - {user_name_input} - {topic_selector_input} - {len(state['filtered_questions'])} questions"),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                state
            )

        async def handle_user_input(user_answer, state):
            quiz_result, _, _, state, df_update = await quiz_logic(
                state["filtered_questions"], state["filtered_checking_answers"], state["filtered_explain_answers"],
                questions_mc, questions_essay, user_answer, state["filtered_questions"], state
            )
            
            current_question_index = state["current_question_index"]
            is_quiz_finished = current_question_index >= state["num_questions"]
            
            total_score_label = f"Total Score - {state['user_name']} - {state['selected_topic']} - {state['num_questions']} questions"
            
            if is_quiz_finished:
                # Add a placeholder for user_feedback in the results
                for result in state['results']:
                    result['user_feedback'] = ''
                df = pd.DataFrame(state['results'])
                return (
                    gr.update(value="Quiz finished!"),  # question_box
                    gr.update(visible=False),  # user_input
                    gr.update(visible=False),  # user_answer_display
                    gr.update(visible=False),  # submit_button
                    gr.update(visible=False),  # next_button
                    gr.update(value=quiz_result, visible=True),  # response_box
                    gr.update(value=f"{state['total_score']}", label=total_score_label),  # total_score_display
                    gr.update(visible=True),  # user_feedback
                    gr.update(visible=True),  # save_feedback_button
                    gr.update(visible=True, value=df),  # results_table
                    gr.update(visible=True),  # download_button
                    state  # state
                )
            else:
                return (
                    gr.update(value=state["filtered_questions"][current_question_index-1]),  # question_box
                    gr.update(visible=False),  # user_input
                    gr.update(visible=True, value=user_answer),  # user_answer_display
                    gr.update(visible=False),  # submit_button
                    gr.update(visible=True),  # next_button
                    gr.update(value=quiz_result, visible=True),  # response_box
                    gr.update(value=f"{state['total_score']}", label=total_score_label),  # total_score_display
                    gr.update(visible=False),  # user_feedback
                    gr.update(visible=False),  # save_feedback_button
                    gr.update(visible=False),  # results_table
                    gr.update(visible=False),  # download_button
                    state  # state
                )

        def next_question(state):
            current_question_index = state["current_question_index"]
            
            if current_question_index < state["num_questions"]:
                question = state["filtered_questions"][current_question_index]
                return (
                    gr.update(value=question),
                    gr.update(visible=True, value=""),  # Show and clear user input
                    gr.update(visible=False),  # Hide user answer display
                    gr.update(visible=True),  # Show submit button
                    gr.update(visible=False),  # Hide next button
                    gr.update(visible=False),  # Hide response box
                    state
                )
            else:
                return (
                    gr.update(value="Quiz finished!"),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=True),  # Show user feedback input
                    gr.update(visible=True),  # Show save feedback button
                    state
                )

        def save_feedback(feedback, state):
            # Add feedback to state or save to file if needed
            state['user_feedback'] = feedback
            
            # Add feedback to all rows in the results
            for result in state['results']:
                result['user_feedback'] = feedback
            # Create DataFrame from results
            df = pd.DataFrame(state['results'])
            
            # Update the Excel file with the new data including feedback
            with file_lock:
                df.to_excel(state['output_path'], index=False)
            
            logger.info(f"Updated DataFrame with feedback: {df.to_string()}")
            
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True, value=df),
                gr.update(visible=True),
                state
            )

        start_button.click(
            start_quiz,
            inputs=[user_name_input, topic_selector, num_questions, state],
            outputs=[
                question_box,
                user_input,
                submit_button,
                user_name_input,
                topic_selector,
                num_questions,
                start_button,
                total_score_display,
                response_box,
                next_button,
                user_feedback,
                save_feedback_button,
                state
            ],
            concurrency_limit=20
        )

        submit_button.click(
            handle_user_input,
            inputs=[user_input, state],
            outputs=[
                question_box,
                user_input,
                user_answer_display,  # Thêm dòng này
                submit_button,
                next_button,
                response_box,
                total_score_display,
                user_feedback,
                save_feedback_button,
                results_table,
                download_button,
                state
            ],
            concurrency_limit=20
        )

        next_button.click(
            next_question,
            inputs=[state],
            outputs=[question_box, user_input, user_answer_display, submit_button, next_button, response_box, state],
        )

        save_feedback_button.click(
            save_feedback,
            inputs=[user_feedback, state],
            outputs=[user_feedback, save_feedback_button, results_table, download_button, state]
        )

        def download_results(results):
            logger.info("DataFrame before creating temporary file:")
            logger.info(results.to_string())

            with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.xlsx') as temp_file:
                wb = Workbook()
                ws = wb.active
                for r in dataframe_to_rows(results, index=False, header=True):
                    ws.append([cell.encode('utf-8').decode('utf-8') if isinstance(cell, str) else cell for cell in r])
                wb.save(temp_file.name)
            
            logger.info(f"Data saved to temporary file: {temp_file.name}")
            return gr.File(value=temp_file.name, visible=True, label="Download Results")

        download_button.click(
            download_results,
            inputs=[results_table],
            outputs=[gr.File(label="Download Results", visible=False)]
        )

        demo.launch(server_name="0.0.0.0", server_port=25008)

if __name__ == "__main__":
    file_path = r'D:\OneDrive - Hanoi University of Science and Technology\ITE10-DS&AI-HUST\Learn&Task\PRODUCT_THECOACH\TASK5_GPTschatbot_TestingSale\deploy\QuizApp_deploy3_BuildAgainUI\Data_MarketingKit.xlsx'
    sheet_name_mc = 'TN_P1P2'
    sheet_name_essay = 'TL_P1P2'
    output_dir = r'D:\OneDrive - Hanoi University of Science and Technology\ITE10-DS&AI-HUST\Learn&Task\PRODUCT_THECOACH\TASK5_GPTschatbot_TestingSale\deploy\QuizApp_deploy3_BuildAgainUI\out'

    logger.info("Starting quiz application")
    create_quiz_interface(file_path, sheet_name_mc, sheet_name_essay, output_dir)