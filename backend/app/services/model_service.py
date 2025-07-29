"""
Model service for managing AI model interactions
"""

import logging
from typing import Dict, Any, Optional
from ..core.config import config
from ..core.model_config import ModelManager, ModelProvider

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing AI model interactions"""
    
    def __init__(self):
        self.model_manager: Optional[ModelManager] = None
        self._initialize_manager()
    
    def _initialize_manager(self):
        """Initialize the model manager"""
        try:
            model_config = config.model_config
            self.model_manager = ModelManager(model_config)
            logger.info(f"Model service initialized with provider: {model_config.provider}")
        except Exception as e:
            logger.error(f"Failed to initialize model service: {e}")
            raise
    
    async def start(self):
        """Start the model service and health monitoring"""
        if self.model_manager:
            await self.model_manager.start_health_monitoring()
            logger.info("Model service started with health monitoring")
    
    async def stop(self):
        """Stop the model service and health monitoring"""
        if self.model_manager:
            await self.model_manager.stop_health_monitoring()
            logger.info("Model service stopped")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the active model"""
        if not self.model_manager:
            raise RuntimeError("Model service not initialized")
        
        try:
            return await self.model_manager.generate_text(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise
    
    async def generate_questions(self, content: str, num_questions: int = 5) -> list[str]:
        """Generate questions based on content"""
        prompt = f"""
基于以下内容生成 {num_questions} 个学习问题。问题应该：
1. 涵盖内容的关键知识点
2. 难度适中，适合学习者测试理解程度
3. 问题表述清晰明确
4. 每个问题独立成行

内容：
{content}

请生成问题：
"""
        
        try:
            response = await self.generate_text(prompt, temperature=0.7)
            # Parse questions from response
            questions = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove numbering if present
                    if line[0].isdigit() and '.' in line[:5]:
                        line = line.split('.', 1)[1].strip()
                    questions.append(line)
            
            return questions[:num_questions]
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            raise
    
    async def evaluate_answer(self, question: str, user_answer: str, reference_content: str) -> Dict[str, Any]:
        """Evaluate user answer against reference content"""
        prompt = f"""
请评估以下答案的质量。评估标准：
1. 准确性：答案是否正确
2. 完整性：答案是否完整
3. 清晰度：表达是否清晰

问题：{question}

用户答案：{user_answer}

参考内容：{reference_content}

请提供：
1. 评分（0-10分）
2. 详细反馈
3. 参考答案

格式：
评分：X分
反馈：[详细反馈]
参考答案：[标准答案]
"""
        
        try:
            response = await self.generate_text(prompt, temperature=0.3)
            
            # Parse evaluation response
            lines = response.strip().split('\n')
            score = 0
            feedback = ""
            reference_answer = ""
            
            current_section = None
            for line in lines:
                line = line.strip()
                if line.startswith('评分：'):
                    score_text = line.replace('评分：', '').replace('分', '').strip()
                    try:
                        score = float(score_text)
                    except ValueError:
                        score = 0
                elif line.startswith('反馈：'):
                    current_section = 'feedback'
                    feedback = line.replace('反馈：', '').strip()
                elif line.startswith('参考答案：'):
                    current_section = 'reference'
                    reference_answer = line.replace('参考答案：', '').strip()
                elif current_section == 'feedback' and line:
                    feedback += '\n' + line
                elif current_section == 'reference' and line:
                    reference_answer += '\n' + line
            
            return {
                'score': min(max(score, 0), 10),  # Ensure score is between 0-10
                'feedback': feedback.strip(),
                'reference_answer': reference_answer.strip()
            }
            
        except Exception as e:
            logger.error(f"Answer evaluation failed: {e}")
            raise
    
    async def extract_knowledge_points(self, content: str) -> list[Dict[str, Any]]:
        """Extract key knowledge points from content"""
        prompt = f"""
从以下内容中提取关键知识点。每个知识点应该包含：
1. 标题（简洁明确）
2. 内容（详细说明）
3. 重要性级别（1-5，5最重要）

内容：
{content}

请按以下格式输出：
标题：[知识点标题]
内容：[详细内容]
重要性：[1-5]
---
"""
        
        try:
            response = await self.generate_text(prompt, temperature=0.5)
            
            # Parse knowledge points
            knowledge_points = []
            sections = response.strip().split('---')
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                title = ""
                content = ""
                importance = 1
                
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('标题：'):
                        title = line.replace('标题：', '').strip()
                    elif line.startswith('内容：'):
                        content = line.replace('内容：', '').strip()
                    elif line.startswith('重要性：'):
                        importance_text = line.replace('重要性：', '').strip()
                        try:
                            importance = int(importance_text)
                        except ValueError:
                            importance = 1
                
                if title and content:
                    knowledge_points.append({
                        'title': title,
                        'content': content,
                        'importance_level': min(max(importance, 1), 5)
                    })
            
            return knowledge_points
            
        except Exception as e:
            logger.error(f"Knowledge point extraction failed: {e}")
            raise
    
    async def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        if not self.model_manager:
            return {"error": "Model service not initialized"}
        
        return self.model_manager.get_model_status()
    
    async def switch_provider(self, provider: str) -> bool:
        """Switch to a different model provider"""
        if not self.model_manager:
            raise RuntimeError("Model service not initialized")
        
        try:
            model_provider = ModelProvider(provider)
            return await self.model_manager.switch_provider(model_provider)
        except ValueError:
            logger.error(f"Invalid provider: {provider}")
            return False
    
    async def check_health(self) -> Dict[str, Any]:
        """Check health of all models"""
        if not self.model_manager:
            return {"error": "Model service not initialized"}
        
        return await self.model_manager.check_all_models_health()


# Global model service instance
model_service = ModelService()