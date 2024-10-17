# MiniTask_WebTestScoring

# Interactive Quiz Application

## Overview

This interactive quiz application is designed to provide a user-friendly platform for conducting quizzes with both multiple-choice and essay questions. It features an intuitive interface, real-time scoring, and administrative tools for managing quiz content.

## Features

- Dynamic quiz generation based on user-selected topics
- Support for both multiple-choice and essay questions
- Real-time scoring with detailed feedback
- User-friendly interface with intuitive navigation
- Admin interface for updating quiz questions
- Results download functionality
- User feedback collection at the end of each quiz

## Technology Stack

- Python
- Gradio (for building the web interface)
- Pandas (for data handling)
- OpenAI API (for essay scoring)
- Asyncio (for asynchronous processing)

## Installation

1. Clone the repository:
   ```
   https://github.com/DoanNgocCuong/MiniProduct_WebTestScoring/
   ```

2. Navigate to the project directory:
   ```
   cd MiniProduct_WebTestScoring
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key in the environment variables or directly in the code (ensure it's kept secret in production).

## Usage

### Running the Application

1. Start the application:
   ```
   python app.py
   ```

2. Open a web browser and navigate to the URL provided in the console (typically http://localhost:25008).

### Taking a Quiz

1. Enter your name and select a topic.
2. Choose the number of questions you want to answer.
3. Click "Start" to begin the quiz.
4. Answer each question and click "Submit".
5. Review your score and feedback after each question.
6. Proceed to the next question by clicking "Next Question".
7. After completing the quiz, provide feedback and download your results.

### Updating Quiz Questions (Admin)

1. Run the admin interface:
   ```
   python UI_data.py
   ```

2. Use the provided Google Sheets link to update questions.
3. Click "Sync Data" to update the local database with new questions.

## File Structure

- `app.py`: Main application file
- `UI_data.py`: Admin interface for data management
- `Data_MarketingKit.xlsx`: Excel file containing quiz questions
- `requirements.txt`: List of Python dependencies

## Contributing

Contributions to improve the application are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes and commit (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Create a new Pull Request

## License

[MIT License](LICENSE)

## Contact

For any queries or support, please contact DoanNgocCuong at `cuongmkmtpgoldfinch@gmail.com`.
