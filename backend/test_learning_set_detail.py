#!/usr/bin/env python3
"""
测试学习集详情API功能
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import User, KnowledgeBase, Document, KnowledgePoint, LearningSet, LearningSetItem, LearningRecord
from app.models.crud import learning_set_crud
from app.core.auth import AuthManager
import requests
import json

def test_learning_set_detail():
    """测试学习集详情功能"""
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 1. 获取或创建测试用户
        test_user = db.query(User).filter(User.username == "testuser").first()
        if not test_user:
            print("创建测试用户...")
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        print(f"测试用户ID: {test_user.id}")
        
        # 2. 获取或创建知识库
        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == test_user.id
        ).first()
        
        if not knowledge_base:
            print("创建测试知识库...")
            knowledge_base = KnowledgeBase(
                name="测试知识库",
                description="用于测试的知识库",
                user_id=test_user.id
            )
            db.add(knowledge_base)
            db.commit()
            db.refresh(knowledge_base)
        
        print(f"知识库ID: {knowledge_base.id}")
        
        # 3. 获取或创建文档
        document = db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base.id
        ).first()
        
        if not document:
            print("创建测试文档...")
            document = Document(
                knowledge_base_id=knowledge_base.id,
                filename="test_document.txt",
                file_path="/tmp/test_document.txt",
                file_type="txt",
                file_size=1024,
                processed=True
            )
            db.add(document)
            db.commit()
            db.refresh(document)
        
        print(f"文档ID: {document.id}")
        
        # 4. 创建知识点
        knowledge_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.document_id == document.id
        ).all()
        
        if not knowledge_points:
            print("创建测试知识点...")
            for i in range(3):
                kp = KnowledgePoint(
                    document_id=document.id,
                    title=f"测试知识点 {i+1}",
                    content=f"这是测试知识点 {i+1} 的内容，包含了重要的学习材料。",
                    question=f"关于测试知识点 {i+1} 的问题是什么？",
                    importance_level=i + 1
                )
                db.add(kp)
            db.commit()
            knowledge_points = db.query(KnowledgePoint).filter(
                KnowledgePoint.document_id == document.id
            ).all()
        
        print(f"知识点数量: {len(knowledge_points)}")
        
        # 5. 获取或创建学习集
        learning_set = db.query(LearningSet).filter(
            LearningSet.user_id == test_user.id
        ).first()
        
        if not learning_set:
            print("创建测试学习集...")
            learning_set = learning_set_crud.create_with_documents(
                db=db,
                user_id=test_user.id,
                knowledge_base_id=knowledge_base.id,
                name="测试学习集",
                description="用于测试的学习集",
                document_ids=[document.id]
            )
        
        print(f"学习集ID: {learning_set.id}")
        
        # 6. 创建一些学习记录
        for i, kp in enumerate(knowledge_points):
            existing_record = db.query(LearningRecord).filter(
                LearningRecord.user_id == test_user.id,
                LearningRecord.knowledge_point_id == kp.id,
                LearningRecord.learning_set_id == learning_set.id
            ).first()
            
            if not existing_record:
                record = LearningRecord(
                    user_id=test_user.id,
                    knowledge_point_id=kp.id,
                    learning_set_id=learning_set.id,
                    mastery_level=i % 3,  # 0, 1, 2
                    review_count=i,
                    ease_factor=2.5,
                    interval_days=1
                )
                db.add(record)
        
        db.commit()
        
        # 7. 生成访问token
        auth_manager = AuthManager()
        access_token = auth_manager.create_access_token(data={"sub": test_user.username})
        print(f"访问token: {access_token[:50]}...")
        
        # 8. 测试API
        base_url = "http://localhost:8800"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 测试获取学习集列表
        print("\n=== 测试获取学习集列表 ===")
        response = requests.get(f"{base_url}/api/learning-sets", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            learning_sets = response.json()
            print(f"学习集数量: {len(learning_sets)}")
            if learning_sets:
                print(f"第一个学习集: {learning_sets[0]['name']}")
                print(f"统计信息: 总计={learning_sets[0].get('total_items', 0)}, "
                      f"已掌握={learning_sets[0].get('mastered_items', 0)}, "
                      f"学习中={learning_sets[0].get('learning_items', 0)}, "
                      f"新学习={learning_sets[0].get('new_items', 0)}")
        else:
            print(f"错误: {response.text}")
        
        # 测试获取学习集详情
        print(f"\n=== 测试获取学习集详情 (ID: {learning_set.id}) ===")
        response = requests.get(f"{base_url}/api/learning-sets/{learning_set.id}", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            detail = response.json()
            print(f"学习集名称: {detail['name']}")
            print(f"知识库名称: {detail.get('knowledge_base_name', 'N/A')}")
            print(f"项目数量: {len(detail.get('items', []))}")
            print(f"统计信息: 总计={detail.get('total_items', 0)}, "
                  f"已掌握={detail.get('mastered_items', 0)}, "
                  f"学习中={detail.get('learning_items', 0)}, "
                  f"新学习={detail.get('new_items', 0)}")
            
            # 显示前几个项目
            items = detail.get('items', [])
            for i, item in enumerate(items[:3]):
                print(f"  项目 {i+1}: {item['knowledge_point_title']}")
                print(f"    问题: {item.get('knowledge_point_question', 'N/A')}")
                print(f"    掌握程度: {item.get('mastery_level', 0)}")
                print(f"    复习次数: {item.get('review_count', 0)}")
        else:
            print(f"错误: {response.text}")
        
        # 测试学习记录API
        print(f"\n=== 测试创建学习记录 ===")
        test_data = {
            "knowledge_point_id": knowledge_points[0].id,
            "learning_set_id": learning_set.id,
            "mastery_level": 2
        }
        response = requests.post(
            f"{base_url}/api/learning-sets/learning-records", 
            headers=headers,
            json=test_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            record = response.json()
            print(f"学习记录ID: {record['id']}")
            print(f"掌握程度: {record['mastery_level']}")
            print(f"下次复习: {record.get('next_review', 'N/A')}")
        else:
            print(f"错误: {response.text}")
        
        print("\n=== 测试完成 ===")
        print(f"可以使用以下信息测试前端:")
        print(f"- 用户名: testuser")
        print(f"- 学习集ID: {learning_set.id}")
        print(f"- 访问token: {access_token}")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_learning_set_detail()