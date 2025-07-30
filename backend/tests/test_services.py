"""
Unit tests for service layer components
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.question_service import QuestionService, QuestionQualityEvaluator, QuestionDifficultyClassifier
from app.services.evaluation_service import EvaluationService
from app.services.knowledge_point_service import KnowledgePointService
from app.services.spaced_repetition_service import SpacedRepetitionService
from app.services.anki_service import AnkiService
from app.models.models import Question, AnswerRecord, KnowledgePoint, ReviewRecord


class TestQuestionQualityEvaluator:
    """Test question quality evaluation"""
    
    def test_evaluate_high_quality_question(self):
        """Test evaluation of a high-quality question"""
        question = "什么是机器学习的主要应用领域？"
        context = "机器学习在医疗、金融、自动驾驶等领域有广泛应用"
        
        result = QuestionQualityEvaluator.evaluate_question_quality(question, context)
        
        assert result['score'] >= 7.0
        assert "适当的问题长度" in result['strengths']
        assert "正确的问句格式" in result['strengths']
        assert "包含疑问词" in result['strengths']
    
    def test_evaluate_low_quality_question(self):
        """Test evaluation of a low-quality question"""
        question = "是吗"
        context = "机器学习是人工智能的一个分支"
        
        result = QuestionQualityEvaluator.evaluate_question_quality(question, context)
        
        assert result['score'] < 5.0
        assert "问题过短" in result['issues']
        assert "可能是简单是非题" in result['issues']
    
    def test_evaluate_question_without_question_mark(self):
        """Test evaluation of question without question mark"""
        question = "机器学习的定义是什么"
        context = "机器学习是一种人工智能技术"
        
        result = QuestionQualityEvaluator.evaluate_question_quality(question, context)
        
        assert "缺少问号" in result['issues']
    
    def test_evaluate_question_context_relevance(self):
        """Test evaluation of question-context relevance"""
        question = "什么是深度学习？"
        context = "深度学习是机器学习的一个子领域，使用神经网络"
        
        result = QuestionQualityEvaluator.evaluate_question_quality(question, context)
        
        assert result['score'] >= 6.0
        assert any("相关" in strength for strength in result['strengths'])


class TestQuestionDifficultyClassifier:
    """Test question difficulty classification"""
    
    def test_classify_easy_question(self):
        """Test classification of easy question"""
        question = "什么是机器学习？"
        context = "机器学习是人工智能的一个分支"
        
        difficulty = QuestionDifficultyClassifier.classify_difficulty(question, context)
        
        assert difficulty == 1
    
    def test_classify_medium_question(self):
        """Test classification of medium difficulty question"""
        question = "机器学习算法如何选择合适的特征？"
        context = "特征选择是机器学习中的重要步骤，涉及多种技术"
        
        difficulty = QuestionDifficultyClassifier.classify_difficulty(question, context)
        
        assert difficulty == 2
    
    def test_classify_hard_question(self):
        """Test classification of hard question"""
        question = "如何在高维数据中避免维度诅咒并优化模型性能？"
        context = "高维数据处理涉及复杂的数学理论和优化技术"
        
        difficulty = QuestionDifficultyClassifier.classify_difficulty(question, context)
        
        assert difficulty == 3


class TestQuestionService:
    """Test question generation service"""
    
    @pytest.fixture
    def question_service(self, mock_model_service, mock_rag_service):
        """Create question service with mocked dependencies"""
        with patch('app.services.question_service.model_service', mock_model_service), \
             patch('app.services.question_service.rag_service', mock_rag_service):
            return QuestionService()
    
    @pytest.mark.asyncio
    async def test_generate_questions_from_document(self, question_service, db_session: Session, test_document):
        """Test generating questions from document"""
        # Mock the model service response
        mock_questions = [
            {
                "question": "什么是机器学习？",
                "context": "机器学习基础概念",
                "difficulty": 1
            },
            {
                "question": "如何评估模型性能？",
                "context": "模型评估方法",
                "difficulty": 2
            }
        ]
        
        with patch.object(question_service, '_extract_document_content', return_value="Document content"), \
             patch.object(question_service, '_generate_questions_with_ai', return_value=mock_questions):
            
            questions = await question_service.generate_questions_from_document(
                db_session, test_document.id, num_questions=2
            )
            
            assert len(questions) == 2
            assert all(q.document_id == test_document.id for q in questions)
            assert questions[0].question_text == "什么是机器学习？"
    
    @pytest.mark.asyncio
    async def test_generate_questions_with_quality_filter(self, question_service, db_session: Session, test_document):
        """Test question generation with quality filtering"""
        # Mock low and high quality questions
        mock_questions = [
            {
                "question": "是吗？",  # Low quality
                "context": "Context",
                "difficulty": 1
            },
            {
                "question": "什么是深度学习的核心原理？",  # High quality
                "context": "深度学习原理",
                "difficulty": 2
            }
        ]
        
        with patch.object(question_service, '_extract_document_content', return_value="Content"), \
             patch.object(question_service, '_generate_questions_with_ai', return_value=mock_questions):
            
            questions = await question_service.generate_questions_from_document(
                db_session, test_document.id, num_questions=2, min_quality_score=6.0
            )
            
            # Should only return high-quality questions
            assert len(questions) == 1
            assert "深度学习" in questions[0].question_text
    
    def test_validate_question_format(self, question_service):
        """Test question format validation"""
        valid_question = "什么是机器学习？"
        invalid_question = ""
        
        assert question_service._validate_question_format(valid_question) is True
        assert question_service._validate_question_format(invalid_question) is False
    
    def test_deduplicate_questions(self, question_service):
        """Test question deduplication"""
        questions = [
            {"question": "什么是机器学习？", "context": "Context1"},
            {"question": "什么是机器学习？", "context": "Context2"},  # Duplicate
            {"question": "什么是深度学习？", "context": "Context3"}
        ]
        
        unique_questions = question_service._deduplicate_questions(questions)
        
        assert len(unique_questions) == 2
        question_texts = [q["question"] for q in unique_questions]
        assert "什么是机器学习？" in question_texts
        assert "什么是深度学习？" in question_texts


class TestEvaluationService:
    """Test answer evaluation service"""
    
    @pytest.fixture
    def evaluation_service(self, mock_model_service, mock_rag_service):
        """Create evaluation service with mocked dependencies"""
        with patch('app.services.evaluation_service.model_service', mock_model_service), \
             patch('app.services.evaluation_service.rag_service', mock_rag_service):
            return EvaluationService()
    
    @pytest.mark.asyncio
    async def test_evaluate_answer_success(self, evaluation_service, db_session: Session, test_user, test_question):
        """Test successful answer evaluation"""
        user_answer = "机器学习是人工智能的一个分支"
        
        # Mock the evaluation response
        mock_evaluation = {
            "score": 8.5,
            "feedback": "答案准确，理解正确",
            "reference_answer": "机器学习是人工智能的子领域"
        }
        
        with patch.object(evaluation_service, '_get_reference_content', return_value="Reference content"), \
             patch.object(evaluation_service, '_generate_reference_answer', return_value="Reference answer"), \
             patch.object(evaluation_service, '_generate_detailed_analysis', return_value="Detailed analysis"), \
             patch.object(evaluation_service, '_save_answer_record', return_value=Mock(id=1)):
            
            evaluation_service.model_service.evaluate_answer.return_value = mock_evaluation
            
            result = await evaluation_service.evaluate_answer(
                db_session, test_user.id, test_question.id, user_answer
            )
            
            assert result['success'] is True
            assert result['question_id'] == test_question.id
            assert 'record_id' in result
    
    @pytest.mark.asyncio
    async def test_evaluate_answer_question_not_found(self, evaluation_service, db_session: Session, test_user):
        """Test evaluation with non-existent question"""
        result = await evaluation_service.evaluate_answer(
            db_session, test_user.id, 99999, "Some answer"
        )
        
        assert result['success'] is False
        assert result['error'] == 'Question not found'
    
    @pytest.mark.asyncio
    async def test_generate_reference_answer(self, evaluation_service):
        """Test reference answer generation"""
        question = "什么是机器学习？"
        context = "机器学习是人工智能的分支"
        
        evaluation_service.model_service.generate_text.return_value = "机器学习是AI的子领域"
        
        reference = await evaluation_service._generate_reference_answer(question, context)
        
        assert reference == "机器学习是AI的子领域"
        evaluation_service.model_service.generate_text.assert_called_once()
    
    def test_calculate_score_adjustment(self, evaluation_service):
        """Test score adjustment based on answer characteristics"""
        # Test comprehensive answer
        comprehensive_answer = "机器学习是人工智能的一个重要分支，它通过算法让计算机从数据中学习模式"
        adjustment = evaluation_service._calculate_score_adjustment(comprehensive_answer)
        assert adjustment >= 0
        
        # Test very short answer
        short_answer = "是AI"
        adjustment = evaluation_service._calculate_score_adjustment(short_answer)
        assert adjustment <= 0

class TestKnowledgePointService:
    """Test knowledge point extraction service"""
    
    @pytest.fixture
    def knowledge_point_service(self, mock_model_service, mock_rag_service):
        """Create knowledge point service with mocked dependencies"""
        with patch('app.services.knowledge_point_service.model_service', mock_model_service), \
             patch('app.services.knowledge_point_service.rag_service', mock_rag_service):
            return KnowledgePointService()
    
    @pytest.mark.asyncio
    async def test_extract_knowledge_points_from_document(self, knowledge_point_service, db_session: Session, test_document):
        """Test extracting knowledge points from document"""
        mock_knowledge_points = [
            {
                "title": "机器学习定义",
                "content": "机器学习是人工智能的一个分支",
                "importance": 3
            },
            {
                "title": "深度学习概念",
                "content": "深度学习使用神经网络",
                "importance": 2
            }
        ]
        
        with patch.object(knowledge_point_service, '_extract_document_content', return_value="Document content"), \
             patch.object(knowledge_point_service, '_extract_knowledge_points_with_ai', return_value=mock_knowledge_points):
            
            knowledge_points = await knowledge_point_service.extract_knowledge_points_from_document(
                db_session, test_document.id
            )
            
            assert len(knowledge_points) == 2
            assert all(kp.document_id == test_document.id for kp in knowledge_points)
            assert knowledge_points[0].title == "机器学习定义"
    
    def test_classify_importance_level(self, knowledge_point_service):
        """Test knowledge point importance classification"""
        # High importance - contains key concepts
        high_importance_content = "机器学习是人工智能的核心技术，广泛应用于各个领域"
        importance = knowledge_point_service._classify_importance_level(high_importance_content)
        assert importance >= 3
        
        # Low importance - general information
        low_importance_content = "这是一个简单的例子"
        importance = knowledge_point_service._classify_importance_level(low_importance_content)
        assert importance <= 2
    
    def test_merge_similar_knowledge_points(self, knowledge_point_service):
        """Test merging similar knowledge points"""
        knowledge_points = [
            {"title": "机器学习", "content": "机器学习是AI分支", "importance": 3},
            {"title": "机器学习概念", "content": "机器学习的基本概念", "importance": 2},
            {"title": "深度学习", "content": "深度学习使用神经网络", "importance": 3}
        ]
        
        merged = knowledge_point_service._merge_similar_knowledge_points(knowledge_points)
        
        # Should merge similar titles
        assert len(merged) == 2
        titles = [kp["title"] for kp in merged]
        assert "深度学习" in titles


class TestSpacedRepetitionService:
    """Test spaced repetition service"""
    
    @pytest.fixture
    def spaced_repetition_service(self):
        """Create spaced repetition service"""
        return SpacedRepetitionService()
    
    def test_calculate_next_review_good_performance(self, spaced_repetition_service):
        """Test calculating next review for good performance"""
        review_record = Mock()
        review_record.interval_days = 1
        review_record.ease_factor = 2.5
        review_record.review_count = 0
        
        next_review, new_interval, new_ease = spaced_repetition_service.calculate_next_review(
            review_record, quality=4
        )
        
        assert new_interval > 1
        assert new_ease >= 2.5
        assert next_review > datetime.now()
    
    def test_calculate_next_review_poor_performance(self, spaced_repetition_service):
        """Test calculating next review for poor performance"""
        review_record = Mock()
        review_record.interval_days = 7
        review_record.ease_factor = 2.5
        review_record.review_count = 3
        
        next_review, new_interval, new_ease = spaced_repetition_service.calculate_next_review(
            review_record, quality=1
        )
        
        # Should reset interval and reduce ease factor
        assert new_interval == 1
        assert new_ease < 2.5
    
    @pytest.mark.asyncio
    async def test_get_due_reviews(self, spaced_repetition_service, db_session: Session, test_user):
        """Test getting due reviews"""
        # Create overdue review record
        overdue_review = ReviewRecord(
            user_id=test_user.id,
            content_id=1,
            content_type="question",
            next_review=datetime.now() - timedelta(hours=1)
        )
        db_session.add(overdue_review)
        db_session.commit()
        
        due_reviews = await spaced_repetition_service.get_due_reviews(db_session, test_user.id)
        
        assert len(due_reviews) >= 1
        assert any(review.id == overdue_review.id for review in due_reviews)
    
    def test_update_review_record(self, spaced_repetition_service, db_session: Session, test_review_record):
        """Test updating review record after review"""
        original_interval = test_review_record.interval_days
        
        updated_record = spaced_repetition_service.update_review_record(
            db_session, test_review_record, quality=4
        )
        
        assert updated_record.interval_days >= original_interval
        assert updated_record.review_count == test_review_record.review_count + 1
        assert updated_record.last_reviewed is not None


class TestAnkiService:
    """Test Anki export service"""
    
    @pytest.fixture
    def anki_service(self):
        """Create Anki service"""
        return AnkiService()
    
    def test_create_anki_deck(self, anki_service):
        """Test creating Anki deck"""
        deck_name = "Test Deck"
        deck = anki_service._create_deck(deck_name)
        
        assert deck.name == deck_name
        assert deck.deck_id is not None
    
    def test_create_question_card(self, anki_service, test_question, test_answer_record):
        """Test creating Anki card from question and answer"""
        card = anki_service._create_question_card(test_question, test_answer_record)
        
        assert test_question.question_text in card.fields[0]
        assert test_answer_record.reference_answer in card.fields[1]
    
    def test_create_knowledge_point_card(self, anki_service, test_knowledge_point):
        """Test creating Anki card from knowledge point"""
        card = anki_service._create_knowledge_point_card(test_knowledge_point)
        
        assert test_knowledge_point.title in card.fields[0]
        assert test_knowledge_point.content in card.fields[1]
    
    @pytest.mark.asyncio
    async def test_export_questions_to_anki(self, anki_service, db_session: Session, test_user, test_question):
        """Test exporting questions to Anki format"""
        # Create answer record for the question
        answer_record = AnswerRecord(
            user_id=test_user.id,
            question_id=test_question.id,
            user_answer="Test answer",
            reference_answer="Reference answer",
            score=8.0
        )
        db_session.add(answer_record)
        db_session.commit()
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.apkg"
            
            result = await anki_service.export_questions_to_anki(
                db_session, test_user.id, [test_question.id]
            )
            
            assert result['success'] is True
            assert 'file_path' in result
            assert result['cards_exported'] == 1
    
    @pytest.mark.asyncio
    async def test_export_knowledge_points_to_anki(self, anki_service, db_session: Session, test_knowledge_point):
        """Test exporting knowledge points to Anki format"""
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.apkg"
            
            result = await anki_service.export_knowledge_points_to_anki(
                db_session, [test_knowledge_point.id]
            )
            
            assert result['success'] is True
            assert 'file_path' in result
            assert result['cards_exported'] == 1
    
    def test_validate_export_data(self, anki_service):
        """Test validation of export data"""
        # Valid data
        valid_questions = [Mock(id=1, question_text="Question?")]
        assert anki_service._validate_export_data(valid_questions) is True
        
        # Invalid data
        invalid_questions = []
        assert anki_service._validate_export_data(invalid_questions) is False
    
    def test_sanitize_anki_content(self, anki_service):
        """Test sanitizing content for Anki"""
        content_with_html = "<p>Test content with <b>HTML</b></p>"
        sanitized = anki_service._sanitize_content(content_with_html)
        
        assert "<p>" not in sanitized
        assert "<b>" not in sanitized
        assert "Test content with HTML" in sanitized


class TestServiceIntegration:
    """Test integration between services"""
    
    @pytest.mark.asyncio
    async def test_question_to_evaluation_flow(self, db_session: Session, test_user, test_document):
        """Test complete flow from question generation to evaluation"""
        with patch('app.services.question_service.model_service') as mock_model, \
             patch('app.services.evaluation_service.model_service') as mock_eval_model, \
             patch('app.services.question_service.rag_service'), \
             patch('app.services.evaluation_service.rag_service'):
            
            # Mock question generation
            mock_model.generate_questions.return_value = [{
                "question": "什么是机器学习？",
                "context": "机器学习基础",
                "difficulty": 1
            }]
            
            # Mock evaluation
            mock_eval_model.evaluate_answer.return_value = {
                "score": 8.5,
                "feedback": "Good answer",
                "reference_answer": "Reference"
            }
            
            # Generate question
            question_service = QuestionService()
            questions = await question_service.generate_questions_from_document(
                db_session, test_document.id, num_questions=1
            )
            
            assert len(questions) == 1
            question = questions[0]
            
            # Evaluate answer
            evaluation_service = EvaluationService()
            result = await evaluation_service.evaluate_answer(
                db_session, test_user.id, question.id, "机器学习是AI的分支"
            )
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_knowledge_point_to_anki_flow(self, db_session: Session, test_document):
        """Test flow from knowledge point extraction to Anki export"""
        with patch('app.services.knowledge_point_service.model_service') as mock_model, \
             patch('app.services.knowledge_point_service.rag_service'):
            
            # Mock knowledge point extraction
            mock_model.extract_knowledge_points.return_value = [{
                "title": "机器学习",
                "content": "机器学习是AI分支",
                "importance": 3
            }]
            
            # Extract knowledge points
            kp_service = KnowledgePointService()
            knowledge_points = await kp_service.extract_knowledge_points_from_document(
                db_session, test_document.id
            )
            
            assert len(knowledge_points) == 1
            kp = knowledge_points[0]
            
            # Export to Anki
            anki_service = AnkiService()
            with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
                mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.apkg"
                
                result = await anki_service.export_knowledge_points_to_anki(
                    db_session, [kp.id]
                )
                
                assert result['success'] is True


class TestServiceErrorHandling:
    """Test error handling in services"""
    
    @pytest.mark.asyncio
    async def test_question_service_model_failure(self, db_session: Session, test_document):
        """Test question service handling model failures"""
        with patch('app.services.question_service.model_service') as mock_model:
            mock_model.generate_questions.side_effect = Exception("Model error")
            
            question_service = QuestionService()
            
            with pytest.raises(Exception):
                await question_service.generate_questions_from_document(
                    db_session, test_document.id
                )
    
    @pytest.mark.asyncio
    async def test_evaluation_service_database_error(self, db_session: Session, test_user):
        """Test evaluation service handling database errors"""
        evaluation_service = EvaluationService()
        
        # Test with non-existent question
        result = await evaluation_service.evaluate_answer(
            db_session, test_user.id, 99999, "Some answer"
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_anki_service_invalid_data(self):
        """Test Anki service handling invalid data"""
        anki_service = AnkiService()
        
        # Test with empty data
        result = anki_service._validate_export_data([])
        assert result is False
        
        # Test with invalid objects
        invalid_data = [Mock(id=None)]
        result = anki_service._validate_export_data(invalid_data)
        assert result is False