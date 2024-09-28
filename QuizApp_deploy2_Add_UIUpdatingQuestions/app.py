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
    logger.info("Data đã được load lại")  # Thêm dòng này
    return questions, checking_answers, explain_answers, topics, questions_mc, questions_essay, topics_mc, topics_essay

def update_filtered_is_essay_list(questions_mc, questions_essay, filtered_questions):
    is_essay_list = [q in questions_essay for q in filtered_questions]
    return is_essay_list



@circuit(failure_threshold=5, recovery_timeout=60)
async def scoring_short_essay_questions(QUESTION, CHECKING_ANSWER, USER_ANSWER):
    async with AsyncOpenAI(api_key="") as client:
        prompt = f"""
        Act: You are an expert at scoring short essay questions. 
        You are provided with 1 QUESTION and 1 CHECKING ANSWER for that QUESTION. After USER enters the answer, you will check USER ANSWER with CHECKING ANSWER. 

        Instructions: 
        - point: check USER ANSWER with CHECKING ANSWER to score on a 5-point scale 
        - comment: briefly in 2 sentences: the reason you gave such a score (in Vietnamese)

        Output: JSON format with 2 keys: `point` and `comment`
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
        
        current_question_index += 1
    else:
        assistant_response = ""

    if current_question_index < len(questions) and not pd.isna(questions[current_question_index]):
        assistant_response += "\n \n ---------------------------CÂU HỎI---------------------------"
        assistant_response += f"\n{questions[current_question_index]}"
        state["current_question_index"] = current_question_index
        state["total_score"] = total_score
        state["results"] = results
        return assistant_response, gr.update(visible=True), gr.update(visible=True), state, gr.update(visible=False)
    else:
        quiz_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for result in results:
            result['time_start'] = quiz_start_time
            result['time_end'] = quiz_end_time
            result['total_score'] = total_score
        
        df = pd.DataFrame(results)
        
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



# ... (previous code remains unchanged)

def create_quiz_interface(file_path, sheet_name_mc, sheet_name_essay, output_dir):
    logger.info("Creating quiz interface")
    
    # Initial load of data
    questions, checking_answers, explain_answers, topics, questions_mc, questions_essay, topics_mc, topics_essay = load_all_data(file_path, sheet_name_mc, sheet_name_essay)
    logger.info("Data loaded successfully on initial load")

    custom_css = """
    .total-score-right {
        position: absolute;
        top: 10px;
        right: 10px;
        width: auto !important;
    }
    """

    with gr.Blocks() as demo:
        gr.HTML(f"<style>{custom_css}</style>")
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

        
        response_box = gr.Textbox(label="Response", interactive=False, visible=False)
        question_box = gr.Textbox(label="Question", interactive=False, visible=False)
        
        user_input = gr.Textbox(label=f"Your Answer", visible=False)
        results_table = gr.DataFrame(
            label="Your results have been saved successfully",
            interactive=False,
            visible=False,
            wrap=False
        )
        total_score_display = gr.Textbox(label=f"Total Score", value="0", interactive=False, visible=False, elem_classes="total-score-right")

        save_status = gr.Textbox(label="Save Status", visible=False)
        download_button = gr.Button("Download Results", visible=False)
        demo.load(update_topic_selector, outputs=[topic_selector])
        print("Đã load update_topic_selector with new dataset")

        def split_response_and_question(quiz_result):
            parts = quiz_result.split("---------------------------CÂU HỎI---------------------------")
            response = parts[0].strip() if len(parts) > 1 else ""
            question = parts[1].strip() if len(parts) > 1 else quiz_result.strip()
            return response, question

            
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
                    gr.update(visible=False),
                    gr.update(visible=True),
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
                        gr.update(visible=False),
                        gr.update(visible=True),
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
                    gr.update(visible=False),
                    gr.update(visible=True),
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

    # ... rest of the existing function ...
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

            # Bước 3: Tính toán số câu hỏi cần chọn
            total_questions = int(num_questions_input)
            desired_essay = int(total_questions * 0.7)
            desired_mc = total_questions - desired_essay

            actual_essay = min(desired_essay, len(essay_questions))
            actual_mc = min(total_questions - actual_essay, len(mc_questions))

            state["num_mc"] = actual_mc
            state["num_essay"] = actual_essay

            logger.info(f"Chọn {actual_essay} câu tự luận và {actual_mc} câu trắc nghiệm")

            # Bước 4: Chọn câu hỏi
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
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    state
                )

            state["filtered_checking_answers"] = [checking_answers[questions.index(q)] for q in state["filtered_questions"]]
            state["filtered_explain_answers"] = [explain_answers[questions.index(q)] for q in state["filtered_questions"]]
            state["filtered_is_essay_list"] = [q in questions_essay for q in state["filtered_questions"]]

            quiz_result, response_visibility, user_input_visibility, state, results_visibility = asyncio.run(quiz_logic(
                state["filtered_questions"], state["filtered_checking_answers"], state["filtered_explain_answers"],
                questions_mc, questions_essay, "", state["filtered_questions"], state
            ))

            response, question = split_response_and_question(quiz_result)
            
            logger.info(f"Quiz bắt đầu cho người dùng {user_name_input} với chủ đề {topic_selector_input}")
            
            quiz_finished = state["current_question_index"] >= len(state["filtered_questions"])
            
            return (
                gr.update(value=response, visible=True),
                gr.update(value=question, visible=True),
                gr.update(visible=False),
                gr.update(visible=False, choices=new_topics),
                gr.update(visible=False),
                gr.update(visible=not quiz_finished, label=f"Your Answer"),
                gr.update(visible=False),
                gr.update(value=f"{state['total_score']}", visible=True, label=f"Total Score - {user_name_input} - {topic_selector_input} - {len(state['filtered_questions'])} questions"),
                gr.update(visible=False),
                gr.update(visible=quiz_finished, value=f"File kết quả đã được lưu thành công tại: {state['output_path']}" if quiz_finished else ""),
                gr.update(visible=quiz_finished),
                state
            )


        async def handle_user_input(user_answer, state):
            try:
                quiz_result, response_visibility, user_input_visibility, state, results_visibility = await quiz_logic(
                    state["filtered_questions"], state["filtered_checking_answers"], state["filtered_explain_answers"],
                    questions_mc, questions_essay, user_answer, state["filtered_questions"], state
                )
                response, question = split_response_and_question(quiz_result)
                
                is_quiz_finished = state["current_question_index"] >= len(state["filtered_questions"])
                if is_quiz_finished:
                    return gr.update(value=quiz_result), gr.update(value=""), user_input_visibility, "", results_visibility, gr.update(value=f"{state['total_score']}"), gr.update(visible=is_quiz_finished), state
                else:
                    return gr.update(value=response), gr.update(value=question), user_input_visibility, "", results_visibility, gr.update(value=f"{state['total_score']}", label=f"Total Score - {state['user_name']} - {state['selected_topic']} - {state['num_questions']} questions"), gr.update(visible=state["current_question_index"] >= len(state["filtered_questions"])), state

            except IndexError:
                logger.error("IndexError occurred. This may be due to server restart.")
                error_message = "Lỗi: Server vừa được khởi động lại. Tiến trình làm bài của bạn đã bị gián đoạn. Vui lòng bắt đầu lại bài kiểm tra. Chúng tôi xin lỗi vì sự bất tiện này."
                return gr.update(value=error_message), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), state
            except Exception as e:
                logger.error(f"An unexpected error occurred: {str(e)}")
                error_message = f"Đã xảy ra lỗi không mong đợi: {str(e)}. Vui lòng thử lại hoặc liên hệ hỗ trợ."
                return gr.update(value=error_message), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), state



        start_button.click(
            start_quiz,
            inputs=[user_name_input, topic_selector, num_questions, state],
            outputs=[
                response_box,
                question_box,
                user_name_input,
                topic_selector,  # Đảm bảo topic_selector nằm trong danh sách outputs
                num_questions,
                user_input,
                results_table,
                total_score_display,
                start_button,
                save_status,
                download_button,
                state
            ],
            concurrency_limit=40
        )

        user_input.submit(
            handle_user_input,
            inputs=[user_input, state],
            outputs=[response_box, question_box, user_input, user_input, results_table, total_score_display, download_button, state],
            concurrency_limit=40
        )

        def download_results(results):
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


# Main execution
# Main execution
if __name__ == "__main__":
    file_path = r'Data_MarketingKit.xlsx'
    sheet_name_mc = 'TN_P1P2'
    sheet_name_essay = 'TL_P1P2'
    output_dir = r'./out'

    logger.info("Starting quiz application")
    create_quiz_interface(file_path, sheet_name_mc, sheet_name_essay, output_dir)