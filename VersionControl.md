# Version Control

This document outlines the changes and improvements made across the three released versions of our quiz application.

## Version 1 (@app.py, @BuildCode_deploy1.ipynb)

Initial release of the quiz application.

### Features:
- Basic quiz functionality
- Single file structure (@app.py)
- Simple user interface

## Version 2 (@app.py, @UI_data.py, @BuildCode_deploy2_BuildUIAdmin_.ipynb)

### Major Changes:
1. Separated data handling into a new file (@UI_data.py)
2. Improved user interface
3. Added admin functionality for data management

### New Features:
- Admin interface for updating quiz questions
- Improved error handling
- Enhanced data loading and management

### Improvements:
- Better code organization with separate files for app logic and data handling
- Increased concurrency limit from 20 to 40

## version 2.1 (@app.py, @UI_data.py, @BuildCode_deploy3_ChangeUIUX.ipynb)

### Major Changes:
1. Significant UI/UX improvements
2. Enhanced quiz flow and user experience

### New Features:
- Redesigned quiz interface with clearer question and answer display
- Added user feedback collection at the end of the quiz
- Improved results display and download functionality

### Improvements:
- More intuitive quiz progression (Submit -> Next Question flow)
- Better handling of different question types (multiple choice vs. essay)
- Enhanced error handling and bug fixes (e.g., handling topics with no questions)
- Improved asynchronous processing and concurrency handling

### UI/UX Enhancements:
- Added a fixed total score display at the top of the interface
- Implemented a clearer separation between question display and user input
- Added user feedback collection before showing final results
- Improved visibility and flow of quiz components (question, answer input, response, next button)

## Overall Progress

1. Code Structure:
   - Version 1: Single file
   - Version 2: Separated app logic and data handling
   - version 2.1: Maintained separation with focus on UI/UX improvements

2. User Experience:
   - Version 1: Basic functionality
   - Version 2: Improved with admin features
   - version 2.1: Significantly enhanced with intuitive quiz flow and feedback collection

3. Performance:
   - Version 1: Basic concurrency
   - Version 2: Improved concurrency and error handling
   - version 2.1: Further optimized with better asynchronous processing

4. Maintainability:
   - Version 1: Limited
   - Version 2: Improved with separate files
   - version 2.1: Enhanced with clearer code structure and improved error handling

5. Scalability:
   - Version 1: Limited
   - Version 2: Improved with better data management
   - version 2.1: Further enhanced with optimized processing and UI improvements

Each version has built upon the previous, with version 2.1 representing a significant leap in terms of user experience and overall application robustness.
---------------------------
## 3. Với nhiều cập nhật - vào cuối tháng 9/2024
- 3.1 app_update1UIUX_EnterSubmitEachQ.py   (Chuyển từ việc Enter 1 cái là sang câu mới => Thành làm xong 1 câu ấn submit mới sang câu mới. 1 cuộc cải cách mạnh về UI vì nó chưa được tách thành Back và Front nên khá căng) 
- 3.2 app_update2NewScoringPrompt.py với kiểu chấm Make-sensing hơn. Chuyển từ AI chấm dựa trên 3 tiêu chí và đưa ra feedback => Chuyển thành AI đưa ra cách nó chấm dựa vào 3 tiêu chí và feedback. 
(Cách chấm vẫn thế, khác ở chỗ nó Make-Sensing hơn với User). 
- 3.3 app_update3MultipleChoicesTopics.py     

## 4. Giai đoạn giữa tháng 10 - cập nhật chính: Log data vào Larkbase. 
- 4.1 Log 2 Larkbase <mất bản css của ver 3 gồm br và bolid>
- 4.2 Refactor lại toàn bộ code, chia ra làm Backend, Frontend, main.  <Bug: F5 ko load lại câu hỏi>
- 4.3 Bổ sung Larkbase vào code sau khi đã được Refactor => cập nhật đầy đủ như 4.1  <Bug: F5 ko load lại câu hỏi>
- 4.4: Fix từ 4.2 => Fix F5 để load lại câu hỏi. 
- 4.5: Tương tự 4.2 lên 4.4, tui fix từ 4.3 lên 4.5 để load được câu hỏi. 

Ngoài ra: Khi bạn làm xong bài sẽ log kết quả, feedback lại log lại 1 lần nữa vào Larkbase. 
