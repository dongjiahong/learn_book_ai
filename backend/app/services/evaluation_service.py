"""
Answer evaluation service for the RAG Learning Platform
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.models import Question, AnswerRecord, Document, User, KnowledgeBase
from ..services.model_service import model_service
from ..services.rag_service import rag_service

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for evaluating user answers and managing evaluation records"""
    
    async def evaluate_answer(
        self,
        db: Session,
        user_id: int,
        question_id: int,
        user_answer: str,
        save_record: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate a user's answer to a question
        
        Args:
            db: Database session
            user_id: ID of the user submitting the answer
            question_id: ID of the question being answered
            user_answer: The user's answer text
            save_record: Whether to save the evaluation record to database
            
        Returns:
            Dictionary containing evaluation results
        """
        try:
            # Get question with document context
            question = (
                db.query(Question)
                .join(Document)
                .filter(Question.id == question_id)
                .first()
            )
            
            if not question:
                return {
                    'success': False,
                    'error': 'Question not found'
                }
            
            # Get relevant context from RAG system
            reference_content = await self._get_reference_content(
                question.question_text,
                question.document_id
            )
            
            # Evaluate answer using AI model
            evaluation_result = await model_service.evaluate_answer(
                question=question.question_text,
                user_answer=user_answer,
                reference_content=reference_content
            )
            
            # Generate reference answer if not provided
            if not evaluation_result.get('reference_answer'):
                reference_answer = await self._generate_reference_answer(
                    question.question_text,
                    reference_content
                )
                evaluation_result['reference_answer'] = reference_answer
            
            # Enhance evaluation with detailed analysis
            detailed_analysis = await self._generate_detailed_analysis(
                question.question_text,
                user_answer,
                evaluation_result['reference_answer'],
                evaluation_result['score']
            )
            
            evaluation_result['detailed_analysis'] = detailed_analysis
            
            # Save evaluation record if requested
            if save_record:
                answer_record = await self._save_answer_record(
                    db=db,
                    user_id=user_id,
                    question_id=question_id,
                    user_answer=user_answer,
                    evaluation_result=evaluation_result
                )
                evaluation_result['record_id'] = answer_record.id
            
            return {
                'success': True,
                'question_id': question_id,
                'user_answer': user_answer,
                'evaluation': evaluation_result
            }
            
        except Exception as e:
            logger.error(f"Answer evaluation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_reference_content(self, question: str, document_id: int) -> str:
        """Get relevant reference content for the question"""
        try:
            # Use RAG service to find relevant content
            search_results = await rag_service.get_similar_documents(
                query_text=question,
                top_k=3
            )
            
            if search_results:
                # Combine relevant chunks
                content_chunks = []
                for result in search_results:
                    content_chunks.append(result.get('content', ''))
                
                return '\n\n'.join(content_chunks)
            
            return ""
            
        except Exception as e:
            logger.error(f"Failed to get reference content: {e}")
            return ""
    
    async def _generate_reference_answer(self, question: str, reference_content: str) -> str:
        """Generate a reference answer for the question"""
        try:
            prompt = f"""
基于以下参考内容，为问题生成一个标准的参考答案。答案应该：
1. 准确回答问题的核心要点
2. 结构清晰，逻辑合理
3. 包含必要的细节和解释
4. 语言简洁明了

问题：{question}

参考内容：
{reference_content}

请生成参考答案：
"""
            
            reference_answer = await model_service.generate_text(
                prompt=prompt,
                temperature=0.3
            )
            
            return reference_answer.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate reference answer: {e}")
            return ""
    
    async def _generate_detailed_analysis(
        self,
        question: str,
        user_answer: str,
        reference_answer: str,
        score: float
    ) -> Dict[str, Any]:
        """Generate detailed analysis of the answer"""
        try:
            prompt = f"""
请对以下答案进行详细分析，提供具体的改进建议。分析应包括：

1. 准确性分析：答案在事实和概念上是否正确
2. 完整性分析：答案是否涵盖了问题的所有要点
3. 清晰度分析：表达是否清晰，逻辑是否合理
4. 改进建议：具体的改进方向和建议
5. 优点总结：答案中的亮点和优势

问题：{question}

用户答案：{user_answer}

参考答案：{reference_answer}

当前评分：{score}/10

请提供详细分析：
"""
            
            analysis_text = await model_service.generate_text(
                prompt=prompt,
                temperature=0.5
            )
            
            # Parse analysis into structured format
            analysis_sections = self._parse_analysis_text(analysis_text)
            
            return {
                'overall_analysis': analysis_text,
                'structured_analysis': analysis_sections,
                'improvement_suggestions': analysis_sections.get('改进建议', []),
                'strengths': analysis_sections.get('优点总结', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to generate detailed analysis: {e}")
            return {
                'overall_analysis': '',
                'structured_analysis': {},
                'improvement_suggestions': [],
                'strengths': []
            }
    
    def _parse_analysis_text(self, analysis_text: str) -> Dict[str, List[str]]:
        """Parse analysis text into structured sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in analysis_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header
            if any(keyword in line for keyword in ['准确性分析', '完整性分析', '清晰度分析', '改进建议', '优点总结']):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = current_content
                
                # Start new section
                current_section = line.rstrip('：:')
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = current_content
        
        return sections
    
    async def _save_answer_record(
        self,
        db: Session,
        user_id: int,
        question_id: int,
        user_answer: str,
        evaluation_result: Dict[str, Any]
    ) -> AnswerRecord:
        """Save answer evaluation record to database"""
        try:
            answer_record = AnswerRecord(
                user_id=user_id,
                question_id=question_id,
                user_answer=user_answer,
                reference_answer=evaluation_result.get('reference_answer', ''),
                score=evaluation_result.get('score', 0.0),
                feedback=evaluation_result.get('feedback', ''),
                answered_at=datetime.utcnow()
            )
            
            db.add(answer_record)
            db.commit()
            db.refresh(answer_record)
            
            return answer_record
            
        except Exception as e:
            logger.error(f"Failed to save answer record: {e}")
            db.rollback()
            raise
    
    async def get_answer_records(
        self,
        db: Session,
        user_id: int,
        question_id: Optional[int] = None,
        knowledge_base_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get answer records for a user with optional filters"""
        try:
            query = (
                db.query(AnswerRecord)
                .join(Question)
                .join(Document)
                .join(KnowledgeBase)
                .filter(AnswerRecord.user_id == user_id)
            )
            
            if question_id:
                query = query.filter(AnswerRecord.question_id == question_id)
            
            if knowledge_base_id:
                query = query.filter(Document.knowledge_base_id == knowledge_base_id)
            
            records = query.offset(skip).limit(limit).all()
            
            result = []
            for record in records:
                result.append({
                    'id': record.id,
                    'question_id': record.question_id,
                    'question_text': record.question.question_text,
                    'user_answer': record.user_answer,
                    'reference_answer': record.reference_answer,
                    'score': record.score,
                    'feedback': record.feedback,
                    'answered_at': record.answered_at.isoformat(),
                    'document_name': record.question.document.filename,
                    'knowledge_base_id': record.question.document.knowledge_base_id
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get answer records: {e}")
            return []
    
    async def get_evaluation_statistics(
        self,
        db: Session,
        user_id: int,
        knowledge_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get evaluation statistics for a user"""
        try:
            from sqlalchemy import func
            
            query = (
                db.query(AnswerRecord)
                .join(Question)
                .join(Document)
                .join(KnowledgeBase)
                .filter(AnswerRecord.user_id == user_id)
            )
            
            if knowledge_base_id:
                query = query.filter(Document.knowledge_base_id == knowledge_base_id)
            
            records = query.all()
            
            if not records:
                return {
                    'total_answers': 0,
                    'average_score': 0.0,
                    'score_distribution': {},
                    'recent_performance': []
                }
            
            # Calculate statistics
            total_answers = len(records)
            scores = [record.score for record in records if record.score is not None]
            average_score = sum(scores) / len(scores) if scores else 0.0
            
            # Score distribution
            score_ranges = {
                '0-2': 0, '2-4': 0, '4-6': 0, '6-8': 0, '8-10': 0
            }
            
            for score in scores:
                if score < 2:
                    score_ranges['0-2'] += 1
                elif score < 4:
                    score_ranges['2-4'] += 1
                elif score < 6:
                    score_ranges['4-6'] += 1
                elif score < 8:
                    score_ranges['6-8'] += 1
                else:
                    score_ranges['8-10'] += 1
            
            # Recent performance (last 10 answers)
            recent_records = sorted(records, key=lambda x: x.answered_at, reverse=True)[:10]
            recent_performance = [
                {
                    'date': record.answered_at.isoformat(),
                    'score': record.score,
                    'question_text': record.question.question_text[:100] + '...' if len(record.question.question_text) > 100 else record.question.question_text
                }
                for record in recent_records
            ]
            
            return {
                'total_answers': total_answers,
                'average_score': round(average_score, 2),
                'score_distribution': score_ranges,
                'recent_performance': recent_performance
            }
            
        except Exception as e:
            logger.error(f"Failed to get evaluation statistics: {e}")
            return {
                'total_answers': 0,
                'average_score': 0.0,
                'score_distribution': {},
                'recent_performance': []
            }
    
    async def batch_evaluate_answers(
        self,
        db: Session,
        user_id: int,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Batch evaluate multiple answers"""
        try:
            results = []
            successful_evaluations = 0
            failed_evaluations = 0
            
            for answer_data in answers:
                question_id = answer_data.get('question_id')
                user_answer = answer_data.get('user_answer')
                
                if not question_id or not user_answer:
                    failed_evaluations += 1
                    continue
                
                evaluation_result = await self.evaluate_answer(
                    db=db,
                    user_id=user_id,
                    question_id=question_id,
                    user_answer=user_answer,
                    save_record=True
                )
                
                if evaluation_result.get('success'):
                    successful_evaluations += 1
                else:
                    failed_evaluations += 1
                
                results.append(evaluation_result)
            
            return {
                'success': True,
                'total_processed': len(answers),
                'successful_evaluations': successful_evaluations,
                'failed_evaluations': failed_evaluations,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Batch evaluation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global evaluation service instance
evaluation_service = EvaluationService()