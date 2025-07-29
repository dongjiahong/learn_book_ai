"""
File upload and management service
"""
import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException
import magic
import logging

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling file uploads and storage"""
    
    # Supported file types and their MIME types
    SUPPORTED_TYPES = {
        'pdf': ['application/pdf'],
        'epub': ['application/epub+zip'],
        'txt': ['text/plain'],
        'md': ['text/markdown', 'text/x-markdown', 'text/plain']
    }
    
    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(self, upload_dir: str = "uploads"):
        """Initialize file service with upload directory"""
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different file types
        for file_type in self.SUPPORTED_TYPES.keys():
            (self.upload_dir / file_type).mkdir(exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        validation_result = {
            'valid': True,
            'errors': [],
            'file_type': None,
            'file_size': 0
        }
        
        # Check file size
        if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            validation_result['file_size'] = file_size
            
            if file_size > self.MAX_FILE_SIZE:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"File size ({file_size} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)"
                )
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower().lstrip('.')
            if file_ext not in self.SUPPORTED_TYPES:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"File type '{file_ext}' is not supported. Supported types: {list(self.SUPPORTED_TYPES.keys())}"
                )
            else:
                validation_result['file_type'] = file_ext
        else:
            validation_result['valid'] = False
            validation_result['errors'].append("Filename is required")
        
        return validation_result
    
    def validate_mime_type(self, file_path: str, expected_type: str) -> bool:
        """Validate file MIME type using python-magic"""
        try:
            mime_type = magic.from_file(file_path, mime=True)
            return mime_type in self.SUPPORTED_TYPES.get(expected_type, [])
        except Exception as e:
            logger.warning(f"Could not determine MIME type for {file_path}: {e}")
            return True  # Allow if we can't determine MIME type
    
    def generate_unique_filename(self, original_filename: str, content: bytes = None) -> str:
        """Generate a unique filename to avoid conflicts"""
        file_path = Path(original_filename)
        name = file_path.stem
        ext = file_path.suffix
        
        # Create hash from content if available, otherwise use timestamp
        if content:
            hash_obj = hashlib.md5(content)
            hash_str = hash_obj.hexdigest()[:8]
        else:
            import time
            hash_str = str(int(time.time()))
        
        return f"{name}_{hash_str}{ext}"
    
    async def save_file(
        self, 
        file: UploadFile, 
        knowledge_base_id: int,
        validate_mime: bool = True
    ) -> Dict[str, Any]:
        """Save uploaded file to disk"""
        try:
            # Validate file
            validation = self.validate_file(file)
            if not validation['valid']:
                raise HTTPException(status_code=400, detail=validation['errors'])
            
            file_type = validation['file_type']
            file_size = validation['file_size']
            
            # Read file content
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Generate unique filename
            unique_filename = self.generate_unique_filename(file.filename, content)
            
            # Create directory structure: uploads/{file_type}/{knowledge_base_id}/
            kb_dir = self.upload_dir / file_type / str(knowledge_base_id)
            kb_dir.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = kb_dir / unique_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Validate MIME type after saving
            if validate_mime and not self.validate_mime_type(str(file_path), file_type):
                # Remove the file if MIME type validation fails
                os.remove(file_path)
                raise HTTPException(
                    status_code=400, 
                    detail=f"File content does not match expected type '{file_type}'"
                )
            
            return {
                'success': True,
                'file_path': str(file_path.relative_to(self.upload_dir.parent)),
                'filename': unique_filename,
                'original_filename': file.filename,
                'file_type': file_type,
                'file_size': file_size
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from disk"""
        try:
            full_path = Path(file_path)
            if full_path.exists():
                os.remove(full_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file"""
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            return {
                'path': str(full_path),
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def list_files_in_directory(self, directory: str) -> List[Dict[str, Any]]:
        """List all files in a directory"""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return []
            
            files = []
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    if file_info:
                        file_info['name'] = file_path.name
                        files.append(file_info)
            
            return files
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            return []
    
    def cleanup_empty_directories(self):
        """Remove empty directories in upload folder"""
        try:
            for root, dirs, files in os.walk(self.upload_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            logger.info(f"Removed empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty or other error
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Create global instance
file_service = FileService()