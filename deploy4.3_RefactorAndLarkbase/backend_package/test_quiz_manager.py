import pytest
from unittest.mock import Mock, patch
from .quiz_manager import QuizManager
from .data_loader import DataLoader
from .scorer import Scorer

@pytest.fixture
def mock_data_loader():
    mock = Mock(spec=DataLoader)
    mock.get_questions_by_topic.return_value = (
        [{'question': 'MC Q1', 'checking_answer': 'A', 'explain_answer': 'Explanation 1', 'is_essay': False}],
        [{'question': 'Essay Q1', 'checking_answer': 'Answer 1', 'explain_answer': 'Explanation 2', 'is_essay': True}]
    )
    return mock

@pytest.fixture
def mock_scorer():
    mock = Mock(spec=Scorer)
    mock.score_essay.return_value = {
        'accuracy': {'score': 4, 'reason': 'Good accuracy'},
        'completeness': {'score': 2, 'reason': 'Somewhat complete'},
        'clarity': {'score': 2, 'reason': 'Clear explanation'}
    }
    return mock

@pytest.mark.asyncio
async def test_quiz_manager(mock_data_loader, mock_scorer):
    quiz_manager = QuizManager(mock_data_loader, mock_scorer)

    # Test initialize_quiz
    state = quiz_manager.initialize_quiz('Test User', ['Python'], 2)
    assert state['user_name'] == 'Test User'
    assert state['selected_topic'] == ['Python']
    assert state['num_questions'] == 2
    assert len(state['questions']) == 2

    # Test process_answer for MC question
    feedback, state = await quiz_manager.process_answer(state, 'A')
    assert state['total_score'] == 10
    assert len(state['results']) == 1
    assert 'Đúng!' in feedback

    # Test process_answer for Essay question
    with patch('asyncio.create_task') as mock_create_task:
        mock_create_task.return_value = mock_scorer.score_essay.return_value
        feedback, state = await quiz_manager.process_answer(state, 'Essay answer')
    assert state['total_score'] == 18
    assert len(state['results']) == 2
    assert 'Điểm nhận được: 8/10' in feedback

    # Test get_next_question
    next_question = quiz_manager.get_next_question(state)
    assert next_question == 'Quiz finished!'

    # Test finalize_quiz
    with patch('backend.quiz_manager.save_results_to_excel') as mock_save:
        quiz_manager.finalize_quiz(state)
        mock_save.assert_called_once()

    # Test send_results_to_larkbase
    with patch('backend.quiz_manager.create_many_records_with_checkTenantAccessToken') as mock_create:
        quiz_manager.send_results_to_larkbase(state['results'])
        mock_create.assert_called_once()

    # Test get_initial_state
    initial_state = quiz_manager.get_initial_state(state)
    assert initial_state == state
