"""
Question generation service for intelligent question creation and management
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import asyncio
import re

from ..models.models import Question, Document, KnowledgeBase
from ..models.database import get_db
from ..services.model_service import model_service
from ..services.rag_service import rag_service

logger = logging.getLogger(__name__)


class QuestionQualityEvaluator:
    """Evaluates the quality of generated questions"""
    
    @staticmethod
    def evaluate_question_quality(question: str, context: str) -> Dict[str, Any]:
        """
        Evaluate question quality based on various criteria
        
        Returns:
            Dict containing quality score and analysis
        """
        quality_score = 0.0
        issues = []
        strengths = []
        
        # Check question length (optimal: 10-100 characters)
        question_length = len(question.strip())
        if 10 <= question_length <= 100:
            quality_score += 2.0
            strengths.append("适当的问题长度")
        elif question_length < 10:
            issues.append("问题过短")
        else:
            issues.append("问题过长")
            quality_score += 1.0
        
        # Check if question ends with question mark
        if question.strip().endswith('?') or question.strip().endswith('？'):
            quality_score += 1.0
            strengths.append("正确的问句格式")
        else:
            issues.append("缺少问号")
        
        # Check for question words (what, how, why, when, where, who)
        question_words = ['什么', '如何', '怎样', '为什么', '何时', '哪里', '谁', '哪个', '多少']
        has_question_word = any(word in question for word in question_words)
        if has_question_word:
            quality_score += 2.0
            strengths.append("包含疑问词")
        else:
            issues.append("缺少疑问词")
        
        # Check if question is related to context (simple keyword matching)
        context_words = set(re.findall(r'\w+', context.lower()))
        question_words_set = set(re.findall(r'\w+', question.lower()))
        overlap = len(context_words.intersection(question_words_set))
        
        if overlap >= 3:
            quality_score += 2.0
            strengths.append("与内容高度相关")
        elif overlap >= 1:
            quality_score += 1.0
            strengths.append("与内容相关")
        else:
            issues.append("与内容相关性低")
        
        # Check for complexity (avoid yes/no questions)
        simple_starters = ['是否', '是不是', '有没有', '能不能', '会不会']
        is_simple = any(question.startswith(starter) for starter in simple_starters)
        if not is_simple:
            quality_score += 1.5
            strengths.append("非简单是非题")
        else:
            issues.append("可能是简单是非题")
        
        # Normalize score to 0-10 scale
        max_possible_score = 8.5
        normalized_score = min(10.0, (quality_score / max_possible_score) * 10)
        
        return {
            'score': round(normalized_score, 1),
            'issues': issues,
            'strengths': strengths,
            'raw_score': quality_score
        }


class QuestionDifficultyClassifier:
    """Classifies question difficulty levels"""
    
    @staticmethod
    def classify_difficulty(question: str, context: str) -> int:
        """
        Classify question difficulty on a scale of 1-5
        
        1: Basic recall/recognition
        2: Simple comprehension
        3: Application/analysis
        4: Synthesis/evaluation
        5: Complex reasoning/creation
        """
        difficulty_score = 1
        
        # Keywords that indicate different difficulty levels
        recall_keywords = ['什么是', '定义', '列举', '说出', '指出']
        comprehension_keywords = ['解释', '说明', '描述', '总结', '概括']
        application_keywords = ['如何', '怎样', '应用', '使用', '实现']
        analysis_keywords = ['分析', '比较', '区别', '原因', '为什么', '影响']
        synthesis_keywords = ['设计', '创建', '制定', '提出', '构建', '评价']
        
        question_lower = question.lower()
        
        # Check for synthesis/evaluation keywords (highest difficulty)
        if any(keyword in question_lower for keyword in synthesis_keywords):
            difficulty_score = 5
        # Check for analysis keywords
        elif any(keyword in question_lower for keyword in analysis_keywords):
            difficulty_score = 4
        # Check for application keywords
        elif any(keyword in question_lower for keyword in application_keywords):
            difficulty_score = 3
        # Check for comprehension keywords
        elif any(keyword in question_lower for keyword in comprehension_keywords):
            difficulty_score = 2
        # Default to recall level
        else:
            difficulty_score = 1
        
        # Adjust based on question complexity
        question_length = len(question)
        if question_length > 50:
            difficulty_score = min(5, difficulty_score + 1)
        
        # Check for multiple concepts (increases difficulty)
        concept_indicators = ['和', '与', '以及', '同时', '另外', '此外']
        if any(indicator in question for indicator in concept_indicators):
            difficulty_score = min(5, difficulty_score + 1)
        
        return difficulty_score


class QuestionGenerationService:
    """Service for generating and managing questions"""
    
    def __init__(self):
        self.quality_evaluator = QuestionQualityEvaluator()
        self.difficulty_classifier = QuestionDifficultyClassifier()
    
    async def generate_questions_for_document(
        self, 
        db: Session,
        document_id: int,
        num_questions: int = 5,
        min_quality_score: float = 6.0
    ) -> Dict[str, Any]:
        """
        Generate questions for a specific document
        
        Args:
            db: Database session
            document_id: ID of the document
            num_questions: Number of questions to generate
            min_quality_score: Minimum quality score for questions
            
        Returns:
            Dict containing generated questions and metadata
        """
        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {
                    'success': False,
                    'error': f'Document with ID {document_id} not found'
                }
            
            # Get document content from vector store
            similar_docs = await rag_service.get_similar_documents(
                document.filename, 
                top_k=10
            )
            
            if not similar_docs:
                return {
                    'success': False,
                    'error': 'No content found for document in vector store'
                }
            
            # Combine document content
            full_content = "\n\n".join([doc["content"] for doc in similar_docs])
            
            # Generate questions using model service
            raw_questions = await model_service.generate_questions(
                full_content, 
                num_questions * 2  # Generate more to filter for quality
            )
            
            # Evaluate and filter questions
            quality_questions = []
            for question_text in raw_questions:
                if not question_text.strip():
                    continue
                
                # Find best matching context for this question
                best_context = self._find_best_context(question_text, similar_docs)
                
                # Evaluate quality
                quality_eval = self.quality_evaluator.evaluate_question_quality(
                    question_text, 
                    best_context
                )
                
                # Classify difficulty
                difficulty = self.difficulty_classifier.classify_difficulty(
                    question_text, 
                    best_context
                )
                
                if quality_eval['score'] >= min_quality_score:
                    quality_questions.append({
                        'question_text': question_text.strip(),
                        'context': best_context[:500] + "..." if len(best_context) > 500 else best_context,
                        'difficulty_level': difficulty,
                        'quality_score': quality_eval['score'],
                        'quality_analysis': quality_eval
                    })
            
            # Sort by quality score and take the best ones
            quality_questions.sort(key=lambda x: x['quality_score'], reverse=True)
            selected_questions = quality_questions[:num_questions]
            
            # Save questions to database
            saved_questions = []
            for q_data in selected_questions:
                try:
                    question = Question(
                        document_id=document_id,
                        question_text=q_data['question_text'],
                        context=q_data['context'],
                        difficulty_level=q_data['difficulty_level']
                    )
                    db.add(question)
                    db.commit()
                    db.refresh(question)
                    
                    saved_questions.append({
                        'id': question.id,
                        'question_text': question.question_text,
                        'context': question.context,
                        'difficulty_level': question.difficulty_level,
                        'quality_score': q_data['quality_score'],
                        'created_at': question.created_at.isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to save question: {e}")
                    db.rollback()
                    continue
            
            return {
                'success': True,
                'document_id': document_id,
                'document_name': document.filename,
                'generated_questions': len(raw_questions),
                'quality_questions': len(quality_questions),
                'saved_questions': len(saved_questions),
                'questions': saved_questions,
                'quality_threshold': min_quality_score
            }
            
        except Exception as e:
            logger.error(f"Failed to generate questions for document {document_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_questions_for_knowledge_base(
        self,
        db: Session,
        knowledge_base_id: int,
        num_questions_per_document: int = 3,
        min_quality_score: float = 6.0
    ) -> Dict[str, Any]:
        """
        Generate questions for all documents in a knowledge base
        
        Args:
            db: Database session
            knowledge_base_id: ID of the knowledge base
            num_questions_per_document: Number of questions per document
            min_quality_score: Minimum quality score for questions
            
        Returns:
            Dict containing generation results for all documents
        """
        try:
            # Get knowledge base and its documents
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
            if not kb:
                return {
                    'success': False,
                    'error': f'Knowledge base with ID {knowledge_base_id} not found'
                }
            
            documents = db.query(Document).filter(
                Document.knowledge_base_id == knowledge_base_id,
                Document.processed == True
            ).all()
            
            if not documents:
                return {
                    'success': False,
                    'error': 'No processed documents found in knowledge base'
                }
            
            # Generate questions for each document
            results = []
            total_questions = 0
            
            for document in documents:
                doc_result = await self.generate_questions_for_document(
                    db,
                    document.id,
                    num_questions_per_document,
                    min_quality_score
                )
                
                results.append(doc_result)
                if doc_result['success']:
                    total_questions += doc_result['saved_questions']
            
            successful_docs = sum(1 for r in results if r['success'])
            
            return {
                'success': True,
                'knowledge_base_id': knowledge_base_id,
                'knowledge_base_name': kb.name,
                'total_documents': len(documents),
                'successful_documents': successful_docs,
                'total_questions_generated': total_questions,
                'document_results': results,
                'quality_threshold': min_quality_score
            }
            
        except Exception as e:
            logger.error(f"Failed to generate questions for knowledge base {knowledge_base_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_best_context(self, question: str, document_chunks: List[Dict[str, Any]]) -> str:
        """
        Find the best matching context for a question from document chunks
        
        Args:
            question: The question text
            document_chunks: List of document chunks with content
            
        Returns:
            Best matching context string
        """
        if not document_chunks:
            return ""
        
        question_words = set(re.findall(r'\w+', question.lower()))
        best_chunk = document_chunks[0]
        best_score = 0
        
        for chunk in document_chunks:
            chunk_words = set(re.findall(r'\w+', chunk['content'].lower()))
            overlap = len(question_words.intersection(chunk_words))
            
            if overlap > best_score:
                best_score = overlap
                best_chunk = chunk
        
        return best_chunk['content']
    
    async def get_questions_by_document(
        self,
        db: Session,
        document_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get questions for a specific document"""
        try:
            questions = (
                db.query(Question)
                .filter(Question.document_id == document_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
            
            return [
                {
                    'id': q.id,
                    'question_text': q.question_text,
                    'context': q.context,
                    'difficulty_level': q.difficulty_level,
                    'created_at': q.created_at.isoformat()
                }
                for q in questions
            ]
            
        except Exception as e:
            logger.error(f"Failed to get questions for document {document_id}: {e}")
            return []
    
    async def get_questions_by_knowledge_base(
        self,
        db: Session,
        knowledge_base_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get questions for a specific knowledge base"""
        try:
            questions = (
                db.query(Question)
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
            
            return [
                {
                    'id': q.id,
                    'question_text': q.question_text,
                    'context': q.context,
                    'difficulty_level': q.difficulty_level,
                    'document_id': q.document_id,
                    'document_name': q.document.filename,
                    'created_at': q.created_at.isoformat()
                }
                for q in questions
            ]
            
        except Exception as e:
            logger.error(f"Failed to get questions for knowledge base {knowledge_base_id}: {e}")
            return []
    
    async def update_question(
        self,
        db: Session,
        question_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a question"""
        try:
            question = db.query(Question).filter(Question.id == question_id).first()
            if not question:
                return None
            
            # Update allowed fields
            allowed_fields = ['question_text', 'context', 'difficulty_level']
            for field, value in updates.items():
                if field in allowed_fields and hasattr(question, field):
                    setattr(question, field, value)
            
            db.commit()
            db.refresh(question)
            
            return {
                'id': question.id,
                'question_text': question.question_text,
                'context': question.context,
                'difficulty_level': question.difficulty_level,
                'document_id': question.document_id,
                'created_at': question.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update question {question_id}: {e}")
            db.rollback()
            return None
    
    async def delete_question(self, db: Session, question_id: int) -> bool:
        """Delete a question"""
        try:
            question = db.query(Question).filter(Question.id == question_id).first()
            if not question:
                return False
            
            db.delete(question)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete question {question_id}: {e}")
            db.rollback()
            return False


# Global question service instance
question_service = QuestionGenerationService()