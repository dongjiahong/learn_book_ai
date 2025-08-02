"""
Anki card generation service using genanki library
"""
import genanki
import os
import tempfile
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.models import AnswerRecord, KnowledgePoint, Question, Document, KnowledgeBase
from ..models.database import get_db


class AnkiService:
    """Service for generating Anki cards and decks"""
    
    def _generate_deck_id(self, identifier: str) -> int:
        """Generate a unique integer deck ID from a string identifier"""
        return abs(hash(identifier)) % (10**9)
    
    def __init__(self):
        # Create a basic note model for Q&A cards
        self.qa_model = genanki.Model(
            1607392319,  # Unique model ID
            'RAG Learning Q&A',
            fields=[
                {'name': 'Question'},
                {'name': 'Answer'},
                {'name': 'Reference'},
                {'name': 'Context'},
                {'name': 'Source'},
                {'name': 'Score'},
                {'name': 'Feedback'}
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''
                        <div class="question">{{Question}}</div>
                        {{#Context}}
                        <div class="context">
                            <strong>Context:</strong><br>
                            {{Context}}
                        </div>
                        {{/Context}}
                        <div class="source">
                            <small><strong>Source:</strong> {{Source}}</small>
                        </div>
                    ''',
                    'afmt': '''
                        <div class="question">{{Question}}</div>
                        <hr>
                        <div class="answer">
                            <strong>Reference Answer:</strong><br>
                            {{Reference}}
                        </div>
                        {{#Answer}}
                        <div class="user-answer">
                            <strong>Your Answer:</strong><br>
                            {{Answer}}
                        </div>
                        {{/Answer}}
                        {{#Score}}
                        <div class="score">
                            <strong>Score:</strong> {{Score}}/10
                        </div>
                        {{/Score}}
                        {{#Feedback}}
                        <div class="feedback">
                            <strong>Feedback:</strong><br>
                            {{Feedback}}
                        </div>
                        {{/Feedback}}
                        <div class="source">
                            <small><strong>Source:</strong> {{Source}}</small>
                        </div>
                    '''
                }
            ],
            css='''
                .card {
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    line-height: 1.5;
                    color: #333;
                    background-color: #fff;
                    padding: 20px;
                }
                .question {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: #2c3e50;
                }
                .context {
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-left: 4px solid #007bff;
                    margin: 10px 0;
                    font-style: italic;
                }
                .answer, .user-answer {
                    margin: 15px 0;
                    padding: 10px;
                    background-color: #f1f3f4;
                    border-radius: 5px;
                }
                .score {
                    font-weight: bold;
                    color: #28a745;
                    margin: 10px 0;
                }
                .feedback {
                    background-color: #fff3cd;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                .source {
                    margin-top: 15px;
                    color: #6c757d;
                    font-size: 14px;
                }
            '''
        )
        
        # Create a note model for knowledge points
        self.kp_model = genanki.Model(
            1607392320,  # Unique model ID
            'RAG Learning Knowledge Points',
            fields=[
                {'name': 'Question'},
                {'name': 'Answer'},
                {'name': 'Title'},
                {'name': 'Source'},
                {'name': 'Importance'},
                {'name': 'CreatedAt'}
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''
                        <div class="question">{{Question}}</div>
                        <div class="source">
                            <small><strong>Source:</strong> {{Source}}</small>
                        </div>
                        {{#Importance}}
                        <div class="importance">
                            <small><strong>Importance:</strong> {{Importance}}/5</small>
                        </div>
                        {{/Importance}}
                    ''',
                    'afmt': '''
                        <div class="question">{{Question}}</div>
                        <hr>
                        <div class="answer">
                            <strong>{{Title}}</strong><br>
                            {{Answer}}
                        </div>
                        <div class="source">
                            <small><strong>Source:</strong> {{Source}}</small>
                        </div>
                        {{#Importance}}
                        <div class="importance">
                            <small><strong>Importance:</strong> {{Importance}}/5</small>
                        </div>
                        {{/Importance}}
                        <div class="created">
                            <small><strong>Created:</strong> {{CreatedAt}}</small>
                        </div>
                    '''
                }
            ],
            css='''
                .card {
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    line-height: 1.5;
                    color: #333;
                    background-color: #fff;
                    padding: 20px;
                }
                .question {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: #2c3e50;
                }
                .answer {
                    margin: 15px 0;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    border-left: 4px solid #28a745;
                }
                .source, .importance, .created {
                    margin-top: 10px;
                    color: #6c757d;
                    font-size: 14px;
                }
                .importance {
                    color: #ffc107;
                    font-weight: bold;
                }
            '''
        )

    def create_qa_cards_from_records(self, answer_records: List[AnswerRecord]) -> List[genanki.Note]:
        """Create Anki cards from answer records"""
        cards = []
        
        for record in answer_records:
            # Get source information
            source = f"{record.question.document.knowledge_base.name} - {record.question.document.filename}"
            
            # Create note
            note = genanki.Note(
                model=self.qa_model,
                fields=[
                    record.question.question_text,  # Question
                    record.user_answer or "",       # Answer
                    record.reference_answer or "",  # Reference
                    record.question.context or "",  # Context
                    source,                         # Source
                    str(record.score) if record.score else "",  # Score
                    record.feedback or ""           # Feedback
                ]
            )
            cards.append(note)
        
        return cards

    def create_kp_cards_from_points(self, knowledge_points: List[KnowledgePoint]) -> List[genanki.Note]:
        """Create Anki cards from knowledge points"""
        cards = []
        
        for kp in knowledge_points:
            # Skip knowledge points without questions
            if not kp.question or not kp.question.strip():
                continue
                
            # Get source information
            source = f"{kp.document.knowledge_base.name} - {kp.document.filename}"
            
            # Format created date
            created_at = kp.created_at.strftime("%Y-%m-%d") if kp.created_at else ""
            
            # Create note
            note = genanki.Note(
                model=self.kp_model,
                fields=[
                    kp.question,                        # Question
                    kp.content,                         # Answer
                    kp.title,                           # Title
                    source,                             # Source
                    str(kp.importance_level),           # Importance
                    created_at                          # CreatedAt
                ]
            )
            cards.append(note)
        
        return cards

    def count_cards_from_records(
        self, 
        user_id: int, 
        knowledge_base_ids: Optional[List[int]] = None,
        db: Session = None
    ) -> int:
        """Count cards that would be generated from knowledge points"""
        if not db:
            db = next(get_db())
        
        # Only count knowledge points (removed Q&A records functionality)
        kp_query = db.query(KnowledgePoint).join(Document)
        
        if knowledge_base_ids:
            kp_query = kp_query.filter(Document.knowledge_base_id.in_(knowledge_base_ids))
        
        # Only count knowledge points that have questions
        knowledge_points = kp_query.filter(
            KnowledgePoint.question.isnot(None),
            KnowledgePoint.question != ""
        ).all()
        
        return len(knowledge_points)

    def count_cards_from_knowledge_base(
        self, 
        user_id: int, 
        knowledge_base_id: int,
        db: Session = None
    ) -> int:
        """Count cards that would be generated from a specific knowledge base"""
        return self.count_cards_from_records(
            user_id=user_id,
            knowledge_base_ids=[knowledge_base_id],
            db=db
        )

    def count_cards_from_custom(
        self,
        user_id: int,
        knowledge_point_ids: Optional[List[int]] = None,
        db: Session = None
    ) -> int:
        """Count cards that would be generated from specific knowledge points"""
        if not db:
            db = next(get_db())
        
        if not knowledge_point_ids:
            return 0
        
        # Count specific knowledge points that have questions
        knowledge_points = db.query(KnowledgePoint).join(Document).join(KnowledgeBase).filter(
            KnowledgePoint.id.in_(knowledge_point_ids),
            KnowledgeBase.user_id == user_id,
            KnowledgePoint.question.isnot(None),
            KnowledgePoint.question != ""
        ).all()
        
        return len(knowledge_points)

    def generate_deck_from_records(
        self, 
        user_id: int, 
        deck_name: str,
        knowledge_base_ids: Optional[List[int]] = None,
        db: Session = None
    ) -> str:
        """
        Generate Anki deck from knowledge points only (removed Q&A records)
        Returns the path to the generated .apkg file
        """
        if not db:
            db = next(get_db())
        
        # Create deck
        deck_id = self._generate_deck_id(f"{user_id}_{deck_name}_{datetime.now().isoformat()}")
        deck = genanki.Deck(deck_id, deck_name)
        
        all_cards = []
        
        # Only get knowledge points (removed Q&A records functionality)
        kp_query = db.query(KnowledgePoint).join(Document)
        
        if knowledge_base_ids:
            kp_query = kp_query.filter(Document.knowledge_base_id.in_(knowledge_base_ids))
        
        knowledge_points = kp_query.all()
        kp_cards = self.create_kp_cards_from_points(knowledge_points)
        all_cards.extend(kp_cards)
        
        # Add cards to deck
        for card in all_cards:
            deck.add_note(card)
        
        # Generate package
        package = genanki.Package(deck)
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"{deck_name.replace(' ', '_')}.apkg")
        
        package.write_to_file(file_path)
        
        return file_path

    def generate_deck_from_knowledge_base(
        self, 
        user_id: int, 
        knowledge_base_id: int,
        db: Session = None
    ) -> str:
        """Generate Anki deck from a specific knowledge base (knowledge points only)"""
        if not db:
            db = next(get_db())
        
        # Get knowledge base info
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == user_id
        ).first()
        
        if not kb:
            raise ValueError(f"Knowledge base {knowledge_base_id} not found for user {user_id}")
        
        deck_name = f"RAG Learning - {kb.name}"
        
        return self.generate_deck_from_records(
            user_id=user_id,
            deck_name=deck_name,
            knowledge_base_ids=[knowledge_base_id],
            db=db
        )

    def generate_custom_deck(
        self,
        user_id: int,
        deck_name: str,
        knowledge_point_ids: Optional[List[int]] = None,
        db: Session = None
    ) -> str:
        """Generate custom Anki deck from specific knowledge points only"""
        if not db:
            db = next(get_db())
        
        # Create deck
        deck_id = self._generate_deck_id(f"{user_id}_{deck_name}_{datetime.now().isoformat()}")
        deck = genanki.Deck(deck_id, deck_name)
        
        all_cards = []
        
        # Add specific knowledge points only (removed answer records)
        if knowledge_point_ids:
            knowledge_points = db.query(KnowledgePoint).join(Document).join(KnowledgeBase).filter(
                KnowledgePoint.id.in_(knowledge_point_ids),
                KnowledgeBase.user_id == user_id
            ).all()
            kp_cards = self.create_kp_cards_from_points(knowledge_points)
            all_cards.extend(kp_cards)
        
        # Add cards to deck
        for card in all_cards:
            deck.add_note(card)
        
        # Generate package
        package = genanki.Package(deck)
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"{deck_name.replace(' ', '_')}.apkg")
        
        package.write_to_file(file_path)
        
        return file_path


# Global instance
anki_service = AnkiService()