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
    
    async def extract_knowledge_points(self, content: str, target_count: Optional[int] = None) -> list[Dict[str, Any]]:
        """Extract key knowledge points from content"""
        
        # If no target count specified, use default behavior
        if target_count is None:
            return await self._extract_knowledge_points_default(content)
        
        # For large target counts, use staged extraction
        if target_count > 15:
            return await self._extract_knowledge_points_staged(content, target_count)
        else:
            return await self._extract_knowledge_points_single(content, target_count)
    
    async def _extract_knowledge_points_default(self, content: str) -> list[Dict[str, Any]]:
        """Default knowledge point extraction (3-8 points)"""
        prompt = f"""请从以下内容中提取关键知识点。

内容：
{content}

要求：
1. 提取3-8个最重要的知识点，确保覆盖内容的核心概念
2. 每个知识点包含标题、详细内容说明、重要性级别(1-5)
3. 内容说明要丰富详细，包括：
   - 概念的定义和解释
   - 相关的背景信息
   - 实际应用场景或例子
   - 与其他概念的关联
   - 学习要点和注意事项
4. 直接输出结果，不要包含思考过程或<think>标签
5. 严格按照以下格式输出：

标题：知识点的简洁标题
内容：知识点的详细说明，包含定义、背景、应用场景、学习要点等丰富内容。可以分段描述，确保内容充实完整。
重要性：3
---
标题：另一个知识点标题
内容：另一个知识点的详细说明，同样要求内容丰富完整，包含多个方面的信息。
重要性：4
---

请直接开始提取，确保每个知识点的内容都足够丰富详细："""
        
        return await self._parse_knowledge_points_response(prompt)
    
    async def _extract_knowledge_points_single(self, content: str, target_count: int) -> list[Dict[str, Any]]:
        """Extract specified number of knowledge points in single request"""
        prompt = f"""请从以下内容中提取关键知识点。

内容：
{content}

要求：
1. 提取恰好{target_count}个知识点，确保覆盖内容的核心概念
2. 每个知识点包含标题、详细内容说明、重要性级别(1-5)
3. 内容说明要丰富详细，包括：
   - 概念的定义和解释
   - 相关的背景信息
   - 实际应用场景或例子
   - 与其他概念的关联
   - 学习要点和注意事项
4. 直接输出结果，不要包含思考过程或<think>标签
5. 严格按照以下格式输出：

标题：知识点的简洁标题
内容：知识点的详细说明，包含定义、背景、应用场景、学习要点等丰富内容。可以分段描述，确保内容充实完整。
重要性：3
---

请提取恰好{target_count}个知识点，确保每个知识点的内容都足够丰富详细："""
        
        return await self._parse_knowledge_points_response(prompt)
    
    async def _extract_knowledge_points_staged(self, content: str, target_count: int) -> list[Dict[str, Any]]:
        """Extract knowledge points in multiple stages to handle large counts"""
        all_knowledge_points = []
        
        # Calculate how many stages we need (max 15 points per stage)
        points_per_stage = 15
        stages = (target_count + points_per_stage - 1) // points_per_stage
        
        logger.info(f"Extracting {target_count} knowledge points in {stages} stages")
        
        for stage in range(stages):
            # Calculate how many points to extract in this stage
            remaining_points = target_count - len(all_knowledge_points)
            current_stage_count = min(points_per_stage, remaining_points)
            
            if current_stage_count <= 0:
                break
            
            # Create prompt for this stage
            stage_prompt = f"""请从以下内容中提取关键知识点。

内容：
{content}

要求：
1. 这是第{stage + 1}阶段提取，请提取{current_stage_count}个知识点
2. 重点关注内容的不同方面，避免与之前提取的知识点重复
3. 每个知识点包含标题、详细内容说明、重要性级别(1-5)
4. 内容说明要丰富详细，包括：
   - 概念的定义和解释
   - 相关的背景信息
   - 实际应用场景或例子
   - 与其他概念的关联
   - 学习要点和注意事项
5. 直接输出结果，不要包含思考过程或<think>标签
6. 严格按照以下格式输出：

标题：知识点的简洁标题
内容：知识点的详细说明，包含定义、背景、应用场景、学习要点等丰富内容。可以分段描述，确保内容充实完整。
重要性：3
---

请提取{current_stage_count}个知识点："""
            
            try:
                stage_points = await self._parse_knowledge_points_response(stage_prompt)
                all_knowledge_points.extend(stage_points)
                
                logger.info(f"Stage {stage + 1} completed: extracted {len(stage_points)} points")
                
                # If we have enough points, break early
                if len(all_knowledge_points) >= target_count:
                    break
                    
            except Exception as e:
                logger.error(f"Stage {stage + 1} failed: {e}")
                # Continue with next stage even if one fails
                continue
        
        # Trim to exact target count if we extracted too many
        if len(all_knowledge_points) > target_count:
            all_knowledge_points = all_knowledge_points[:target_count]
        
        logger.info(f"Staged extraction completed: {len(all_knowledge_points)} points extracted")
        return all_knowledge_points
    
    async def _parse_knowledge_points_response(self, prompt: str) -> list[Dict[str, Any]]:
        """Parse knowledge points from model response"""
        try:
            response = await self.generate_text(prompt, temperature=0.5)
            
            # Remove <think> tags if present
            if '<think>' in response:
                think_end = response.find('</think>')
                if think_end != -1:
                    response = response[think_end + 8:].strip()
            
            # Parse knowledge points using regex
            knowledge_points = []
            
            # Use regex to match knowledge points
            import re
            pattern = r'标题：([^\n]+)\s*\n内容：(.*?)\s*重要性：(\d+)'
            matches = re.findall(pattern, response, re.DOTALL)
            
            for title, content, importance in matches:
                title = title.strip()
                content = content.strip()
                try:
                    importance_level = int(importance)
                except ValueError:
                    importance_level = 1
                
                # Only add if we have both title and content
                if title and content:
                    knowledge_points.append({
                        'title': title,
                        'content': content,
                        'importance_level': min(max(importance_level, 1), 5)
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