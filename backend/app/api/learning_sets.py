"""
API endpoints for learning set management and learning records
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..core.middleware import get_current_user
from ..models.database import get_db
from ..models.models import User
from ..models.crud import (
    learning_set_crud, learning_record_crud, knowledge_base_crud, 
    document_crud, knowledge_point_crud
)
from ..schemas.learning import (
    LearningSetCreate, LearningSetUpdate, LearningSetResponse,
    LearningSetDetailResponse, LearningSetItemResponse,
    NewLearningRecordCreate, NewLearningRecordUpdate, NewLearningRecordResponse,
    LearningSessionStart, LearningSessionAnswer, LearningSessionResponse,
    LearningSetStatistics, MasteryLevel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning-sets", tags=["learning-sets"])


@router.post("", response_model=LearningSetResponse)
async def create_learning_set(
    learning_set: LearningSetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建学习集"""
    try:
        # 验证知识库存在且用户拥有
        knowledge_base = knowledge_base_crud.get(db=db, id=learning_set.knowledge_base_id)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        if knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此知识库")
        
        # 验证所有文档都属于该知识库
        for doc_id in learning_set.document_ids:
            doc = document_crud.get(db=db, id=doc_id)
            if not doc or doc.knowledge_base_id != learning_set.knowledge_base_id:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文档 {doc_id} 不存在或不属于指定知识库"
                )
        
        # 创建学习集
        db_learning_set = learning_set_crud.create_with_documents(
            db=db,
            user_id=current_user.id,
            knowledge_base_id=learning_set.knowledge_base_id,
            name=learning_set.name,
            description=learning_set.description,
            document_ids=learning_set.document_ids
        )
        
        # 获取统计信息
        stats = learning_set_crud.get_with_statistics(
            db=db, user_id=current_user.id, skip=0, limit=1000
        )
        
        # 找到刚创建的学习集的统计信息
        for ls, total, mastered, learning, new, kb_name in stats:
            if ls.id == db_learning_set.id:
                response_data = {
                    **db_learning_set.__dict__,
                    'total_items': total or 0,
                    'mastered_items': mastered or 0,
                    'learning_items': learning or 0,
                    'new_items': new or 0,
                    'knowledge_base_name': kb_name
                }
                return LearningSetResponse(**response_data)
        
        # 如果没有找到统计信息，返回基本信息
        response_data = {
            **db_learning_set.__dict__,
            'total_items': 0,
            'mastered_items': 0,
            'learning_items': 0,
            'new_items': 0,
            'knowledge_base_name': knowledge_base.name
        }
        return LearningSetResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建学习集时出错: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建学习集失败: {str(e)}")


@router.get("", response_model=List[LearningSetResponse])
async def get_learning_sets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    knowledge_base_id: Optional[int] = Query(None, description="按知识库筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的学习集列表"""
    try:
        # 获取带统计信息的学习集
        learning_sets_with_stats = learning_set_crud.get_with_statistics(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
        
        learning_sets = []
        for ls, total, mastered, learning, new, kb_name in learning_sets_with_stats:
            # 如果指定了知识库筛选
            if knowledge_base_id and ls.knowledge_base_id != knowledge_base_id:
                continue
                
            response_data = {
                **ls.__dict__,
                'total_items': total or 0,
                'mastered_items': mastered or 0,
                'learning_items': learning or 0,
                'new_items': new or 0,
                'knowledge_base_name': kb_name
            }
            learning_sets.append(LearningSetResponse(**response_data))
        
        return learning_sets
        
    except Exception as e:
        logger.error(f"获取学习集列表时出错: {e}")
        raise HTTPException(status_code=500, detail="获取学习集列表失败")


@router.get("/{learning_set_id}", response_model=LearningSetDetailResponse)
async def get_learning_set(
    learning_set_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学习集详情"""
    try:
        # 获取学习集
        learning_set = learning_set_crud.get(db=db, id=learning_set_id)
        if not learning_set:
            raise HTTPException(status_code=404, detail="学习集不存在")
        
        # 验证所有权
        if learning_set.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此学习集")
        
        # 获取知识库名称
        knowledge_base = knowledge_base_crud.get(db=db, id=learning_set.knowledge_base_id)
        kb_name = knowledge_base.name if knowledge_base else "未知知识库"
        
        # 获取学习集项目和进度
        items_with_progress = learning_set_crud.get_items_with_progress(
            db=db, learning_set_id=learning_set_id, user_id=current_user.id
        )
        
        # 构建响应数据
        items = []
        total_items = 0
        mastered_items = 0
        learning_items = 0
        new_items = 0
        
        for item, kp, mastery_level, review_count, next_review, last_reviewed in items_with_progress:
            total_items += 1
            
            # 统计掌握程度
            if mastery_level == 2:
                mastered_items += 1
            elif mastery_level == 1:
                learning_items += 1
            else:
                new_items += 1
            
            item_data = {
                'id': item.id,
                'knowledge_point_id': kp.id,
                'added_at': item.added_at,
                'knowledge_point_title': kp.title,
                'knowledge_point_content': kp.content,
                'knowledge_point_question': kp.question,
                'knowledge_point_importance': kp.importance_level,
                'mastery_level': mastery_level,
                'review_count': review_count,
                'next_review': next_review
            }
            items.append(LearningSetItemResponse(**item_data))
        
        # 构建详细响应
        response_data = {
            **learning_set.__dict__,
            'total_items': total_items,
            'mastered_items': mastered_items,
            'learning_items': learning_items,
            'new_items': new_items,
            'knowledge_base_name': kb_name,
            'items': items
        }
        
        return LearningSetDetailResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习集详情时出错: {e}")
        raise HTTPException(status_code=500, detail="获取学习集详情失败")


@router.put("/{learning_set_id}", response_model=LearningSetResponse)
async def update_learning_set(
    learning_set_id: int,
    learning_set_update: LearningSetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新学习集"""
    try:
        # 获取学习集
        learning_set = learning_set_crud.get(db=db, id=learning_set_id)
        if not learning_set:
            raise HTTPException(status_code=404, detail="学习集不存在")
        
        # 验证所有权
        if learning_set.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此学习集")
        
        # 更新学习集
        updated_learning_set = learning_set_crud.update(
            db=db, db_obj=learning_set, obj_in=learning_set_update
        )
        
        # 获取知识库名称
        knowledge_base = knowledge_base_crud.get(db=db, id=updated_learning_set.knowledge_base_id)
        kb_name = knowledge_base.name if knowledge_base else "未知知识库"
        
        # 获取统计信息
        stats = learning_set_crud.get_with_statistics(
            db=db, user_id=current_user.id, skip=0, limit=1000
        )
        
        # 找到对应的统计信息
        for ls, total, mastered, learning, new, _ in stats:
            if ls.id == learning_set_id:
                response_data = {
                    **updated_learning_set.__dict__,
                    'total_items': total or 0,
                    'mastered_items': mastered or 0,
                    'learning_items': learning or 0,
                    'new_items': new or 0,
                    'knowledge_base_name': kb_name
                }
                return LearningSetResponse(**response_data)
        
        # 如果没有找到统计信息，返回基本信息
        response_data = {
            **updated_learning_set.__dict__,
            'total_items': 0,
            'mastered_items': 0,
            'learning_items': 0,
            'new_items': 0,
            'knowledge_base_name': kb_name
        }
        return LearningSetResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学习集时出错: {e}")
        raise HTTPException(status_code=500, detail="更新学习集失败")


@router.delete("/{learning_set_id}")
async def delete_learning_set(
    learning_set_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除学习集"""
    try:
        # 删除学习集及其相关数据
        success = learning_set_crud.delete_with_items(
            db=db, learning_set_id=learning_set_id, user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="学习集不存在或无权删除")
        
        return {"message": "学习集删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除学习集时出错: {e}")
        raise HTTPException(status_code=500, detail="删除学习集失败")


@router.get("/{learning_set_id}/items", response_model=List[LearningSetItemResponse])
async def get_learning_set_items(
    learning_set_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学习集中的知识点项目"""
    try:
        # 验证学习集存在且用户拥有
        learning_set = learning_set_crud.get(db=db, id=learning_set_id)
        if not learning_set:
            raise HTTPException(status_code=404, detail="学习集不存在")
        
        if learning_set.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此学习集")
        
        # 获取学习集项目和进度
        items_with_progress = learning_set_crud.get_items_with_progress(
            db=db, learning_set_id=learning_set_id, user_id=current_user.id,
            skip=skip, limit=limit
        )
        
        items = []
        for item, kp, mastery_level, review_count, next_review, last_reviewed in items_with_progress:
            item_data = {
                'id': item.id,
                'knowledge_point_id': kp.id,
                'added_at': item.added_at,
                'knowledge_point_title': kp.title,
                'knowledge_point_content': kp.content,
                'knowledge_point_question': kp.question,
                'knowledge_point_importance': kp.importance_level,
                'mastery_level': mastery_level,
                'review_count': review_count,
                'next_review': next_review
            }
            items.append(LearningSetItemResponse(**item_data))
        
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习集项目时出错: {e}")
        raise HTTPException(status_code=500, detail="获取学习集项目失败")


@router.get("/{learning_set_id}/due-reviews", response_model=List[LearningSetItemResponse])
async def get_due_reviews(
    learning_set_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学习集中需要复习的知识点"""
    try:
        # 验证学习集存在且用户拥有
        learning_set = learning_set_crud.get(db=db, id=learning_set_id)
        if not learning_set:
            raise HTTPException(status_code=404, detail="学习集不存在")
        
        if learning_set.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此学习集")
        
        # 获取需要复习的项目
        due_items = learning_set_crud.get_due_items(
            db=db, learning_set_id=learning_set_id, user_id=current_user.id
        )
        
        items = []
        for kp, record in due_items:
            item_data = {
                'id': record.id,  # 使用学习记录的ID
                'knowledge_point_id': kp.id,
                'added_at': record.created_at,
                'knowledge_point_title': kp.title,
                'knowledge_point_content': kp.content,
                'knowledge_point_question': kp.question,
                'knowledge_point_importance': kp.importance_level,
                'mastery_level': record.mastery_level,
                'review_count': record.review_count,
                'next_review': record.next_review
            }
            items.append(LearningSetItemResponse(**item_data))
        
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取待复习项目时出错: {e}")
        raise HTTPException(status_code=500, detail="获取待复习项目失败")


@router.post("/{learning_set_id}/study", response_model=Dict[str, Any])
async def start_learning_session(
    learning_set_id: int,
    session_data: LearningSessionStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """开始学习会话"""
    try:
        # 验证学习集存在且用户拥有
        learning_set = learning_set_crud.get(db=db, id=learning_set_id)
        if not learning_set:
            raise HTTPException(status_code=404, detail="学习集不存在")
        
        if learning_set.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此学习集")
        
        # 根据复习类型获取项目
        if session_data.review_type == "due":
            items = learning_set_crud.get_due_items(
                db=db, learning_set_id=learning_set_id, user_id=current_user.id
            )
            items_data = []
            for kp, record in items:
                items_data.append({
                    'knowledge_point_id': kp.id,
                    'title': kp.title,
                    'question': kp.question,
                    'content': kp.content,
                    'importance_level': kp.importance_level,
                    'mastery_level': record.mastery_level,
                    'next_review': record.next_review
                })
        else:
            # 获取所有项目
            items_with_progress = learning_set_crud.get_items_with_progress(
                db=db, learning_set_id=learning_set_id, user_id=current_user.id
            )
            items_data = []
            for item, kp, mastery_level, review_count, next_review, last_reviewed in items_with_progress:
                if session_data.review_type == "new" and mastery_level != 0:
                    continue
                items_data.append({
                    'knowledge_point_id': kp.id,
                    'title': kp.title,
                    'question': kp.question,
                    'content': kp.content,
                    'importance_level': kp.importance_level,
                    'mastery_level': mastery_level,
                    'next_review': next_review
                })
        
        return {
            "learning_set_id": learning_set_id,
            "learning_set_name": learning_set.name,
            "review_type": session_data.review_type,
            "total_items": len(items_data),
            "items": items_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始学习会话时出错: {e}")
        raise HTTPException(status_code=500, detail="开始学习会话失败")


@router.post("/learning-records", response_model=NewLearningRecordResponse)
async def create_or_update_learning_record(
    answer: LearningSessionAnswer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建或更新学习记录"""
    try:
        # 验证学习集存在且用户拥有
        learning_set = learning_set_crud.get(db=db, id=answer.learning_set_id)
        if not learning_set:
            raise HTTPException(status_code=404, detail="学习集不存在")
        
        if learning_set.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此学习集")
        
        # 验证知识点存在
        knowledge_point = knowledge_point_crud.get(db=db, id=answer.knowledge_point_id)
        if not knowledge_point:
            raise HTTPException(status_code=404, detail="知识点不存在")
        
        # 更新学习记录
        record = learning_record_crud.update_mastery(
            db=db,
            user_id=current_user.id,
            knowledge_point_id=answer.knowledge_point_id,
            learning_set_id=answer.learning_set_id,
            mastery_level=answer.mastery_level.value
        )
        
        # 构建响应数据
        response_data = {
            **record.__dict__,
            'knowledge_point_title': knowledge_point.title,
            'knowledge_point_question': knowledge_point.question,
            'knowledge_point_content': knowledge_point.content,
            'learning_set_name': learning_set.name
        }
        
        return NewLearningRecordResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建或更新学习记录时出错: {e}")
        raise HTTPException(status_code=500, detail="创建或更新学习记录失败")


@router.get("/{learning_set_id}/statistics", response_model=LearningSetStatistics)
async def get_learning_set_statistics(
    learning_set_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学习集统计信息"""
    try:
        # 验证学习集存在且用户拥有
        learning_set = learning_set_crud.get(db=db, id=learning_set_id)
        if not learning_set:
            raise HTTPException(status_code=404, detail="学习集不存在")
        
        if learning_set.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此学习集")
        
        # 获取统计信息
        stats = learning_set_crud.get_with_statistics(
            db=db, user_id=current_user.id, skip=0, limit=1000
        )
        
        # 找到对应的统计信息
        for ls, total, mastered, learning, new, _ in stats:
            if ls.id == learning_set_id:
                # 计算待复习项目数量
                due_items = learning_set_crud.get_due_items(
                    db=db, learning_set_id=learning_set_id, user_id=current_user.id
                )
                
                return LearningSetStatistics(
                    learning_set_id=learning_set_id,
                    total_items=total or 0,
                    mastered_items=mastered or 0,
                    learning_items=learning or 0,
                    new_items=new or 0,
                    due_items=len(due_items),
                    mastery_distribution={
                        "not_learned": new or 0,
                        "learning": learning or 0,
                        "mastered": mastered or 0
                    }
                )
        
        # 如果没有找到统计信息，返回空统计
        return LearningSetStatistics(
            learning_set_id=learning_set_id,
            total_items=0,
            mastered_items=0,
            learning_items=0,
            new_items=0,
            due_items=0,
            mastery_distribution={"not_learned": 0, "learning": 0, "mastered": 0}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习集统计信息时出错: {e}")
        raise HTTPException(status_code=500, detail="获取学习集统计信息失败")