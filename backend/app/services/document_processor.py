"""
Document processing service for async document handling
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
from dataclasses import dataclass
from enum import Enum
import os

from sqlalchemy.orm import Session
from ..models.database import get_db
from ..models.crud import document_crud
from ..models.models import Document
from .rag_service import rag_service

# Import text extraction libraries
try:
    import PyPDF2
    import pdfplumber
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False
    logger.warning("PDF support not available. Install PyPDF2 and pdfplumber for PDF processing.")

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    HAS_EPUB_SUPPORT = True
except ImportError:
    HAS_EPUB_SUPPORT = False
    logger.warning("EPUB support not available. Install ebooklib and beautifulsoup4 for EPUB processing.")

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingTask:
    """Document processing task"""
    document_id: int
    file_path: str
    knowledge_base_id: int
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    progress: float = 0.0


class DocumentProcessor:
    """Async document processor with queue management"""
    
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_queue: Queue = Queue()
        self.processing_tasks: Dict[int, ProcessingTask] = {}
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start the document processor"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            logger.info("Document processor started")
    
    def stop(self):
        """Stop the document processor"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        logger.info("Document processor stopped")
    
    def add_document(self, document_id: int, file_path: str, knowledge_base_id: int) -> bool:
        """Add a document to the processing queue"""
        try:
            task = ProcessingTask(
                document_id=document_id,
                file_path=file_path,
                knowledge_base_id=knowledge_base_id
            )
            
            with self._lock:
                self.processing_tasks[document_id] = task
                self.processing_queue.put(task)
            
            logger.info(f"Added document {document_id} to processing queue")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document {document_id} to queue: {e}")
            return False
    
    def get_processing_status(self, document_id: int) -> Optional[ProcessingTask]:
        """Get processing status for a document"""
        with self._lock:
            return self.processing_tasks.get(document_id)
    
    def _process_queue(self):
        """Process documents from the queue"""
        logger.info("Document processing worker started")
        
        while self.is_running:
            try:
                # Get task from queue with timeout
                try:
                    task = self.processing_queue.get(timeout=1.0)
                except:
                    continue
                
                # Process the document
                self._process_document(task)
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in processing queue: {e}")
    
    def _process_document(self, task: ProcessingTask):
        """Process a single document"""
        try:
            logger.info(f"Starting processing of document {task.document_id}")
            
            # Update status to processing
            with self._lock:
                task.status = ProcessingStatus.PROCESSING
                task.progress = 0.1
            
            # Check if file exists
            if not Path(task.file_path).exists():
                raise FileNotFoundError(f"Document file not found: {task.file_path}")
            
            # Update progress
            with self._lock:
                task.progress = 0.3
            
            # Process document with RAG service
            result = asyncio.run(self._process_with_rag(task))
            
            if result['success']:
                # Update progress
                with self._lock:
                    task.progress = 0.8
                
                # Mark document as processed in database
                self._mark_document_processed(task.document_id)
                
                # Update final status
                with self._lock:
                    task.status = ProcessingStatus.COMPLETED
                    task.progress = 1.0
                
                logger.info(f"Successfully processed document {task.document_id}")
                
            else:
                raise Exception(result.get('error', 'Unknown processing error'))
                
        except Exception as e:
            logger.error(f"Failed to process document {task.document_id}: {e}")
            
            # Update status to failed
            with self._lock:
                task.status = ProcessingStatus.FAILED
                task.error_message = str(e)
                task.progress = 0.0
    
    async def _process_with_rag(self, task: ProcessingTask) -> Dict[str, Any]:
        """Process document with RAG service"""
        try:
            # Load document into RAG system
            result = await rag_service.load_documents([task.file_path])
            
            if result['success']:
                logger.info(f"Document {task.document_id} added to vector store")
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"RAG processing failed: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"RAG processing exception: {str(e)}"
            }
    
    def _mark_document_processed(self, document_id: int):
        """Mark document as processed in database"""
        try:
            # Get database session
            db = next(get_db())
            
            try:
                # Update document status
                document = document_crud.get(db=db, id=document_id)
                if document:
                    document.processed = True
                    db.commit()
                    logger.info(f"Marked document {document_id} as processed in database")
                else:
                    logger.warning(f"Document {document_id} not found in database")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to mark document {document_id} as processed: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        with self._lock:
            pending_count = sum(1 for task in self.processing_tasks.values() 
                              if task.status == ProcessingStatus.PENDING)
            processing_count = sum(1 for task in self.processing_tasks.values() 
                                 if task.status == ProcessingStatus.PROCESSING)
            completed_count = sum(1 for task in self.processing_tasks.values() 
                                if task.status == ProcessingStatus.COMPLETED)
            failed_count = sum(1 for task in self.processing_tasks.values() 
                             if task.status == ProcessingStatus.FAILED)
            
            return {
                'is_running': self.is_running,
                'queue_size': self.processing_queue.qsize(),
                'total_tasks': len(self.processing_tasks),
                'pending': pending_count,
                'processing': processing_count,
                'completed': completed_count,
                'failed': failed_count
            }
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks"""
        import time
        current_time = time.time()
        
        with self._lock:
            tasks_to_remove = []
            for doc_id, task in self.processing_tasks.items():
                if task.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                    # For simplicity, remove all completed/failed tasks
                    # In production, you might want to add timestamps
                    tasks_to_remove.append(doc_id)
            
            for doc_id in tasks_to_remove:
                del self.processing_tasks[doc_id]
            
            if tasks_to_remove:
                logger.info(f"Cleaned up {len(tasks_to_remove)} completed/failed tasks")
    
    async def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text content from various file formats
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text content
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                return await self._extract_pdf_text(file_path)
            elif file_extension == '.epub':
                return await self._extract_epub_text(file_path)
            elif file_extension in ['.txt', '.md']:
                return await self._extract_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        if not HAS_PDF_SUPPORT:
            raise ImportError("PDF support not available. Install PyPDF2 and pdfplumber.")
        
        try:
            # Try pdfplumber first (better text extraction)
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return '\n\n'.join(text_parts)
        except Exception as e:
            logger.warning(f"pdfplumber failed for {file_path}, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_parts = []
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    return '\n\n'.join(text_parts)
            except Exception as e2:
                raise Exception(f"Both pdfplumber and PyPDF2 failed: {e}, {e2}")
    
    async def _extract_epub_text(self, file_path: str) -> str:
        """Extract text from EPUB file"""
        if not HAS_EPUB_SUPPORT:
            raise ImportError("EPUB support not available. Install ebooklib and beautifulsoup4.")
        
        try:
            book = epub.read_epub(file_path)
            text_parts = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()
                    if text.strip():
                        text_parts.append(text.strip())
            
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            raise Exception(f"Failed to extract EPUB text: {e}")
    
    async def _extract_text_file(self, file_path: str) -> str:
        """Extract text from plain text or markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            raise Exception("Could not decode file with any supported encoding")


# Global document processor instance
document_processor = DocumentProcessor()

# Auto-start the processor
document_processor.start()


def process_unprocessed_documents():
    """Process any unprocessed documents on startup"""
    try:
        db = next(get_db())
        try:
            unprocessed_docs = document_crud.get_unprocessed(db=db, limit=50)
            
            for doc in unprocessed_docs:
                document_processor.add_document(
                    document_id=doc.id,
                    file_path=doc.file_path,
                    knowledge_base_id=doc.knowledge_base_id
                )
            
            if unprocessed_docs:
                logger.info(f"Added {len(unprocessed_docs)} unprocessed documents to queue")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to process unprocessed documents: {e}")


# Process unprocessed documents on module import
process_unprocessed_documents()