// 测试知识库修改和删除操作
const API_BASE_URL = 'http://172.18.3.1:8800';

// 你需要先登录获取实际的token
const TEST_TOKEN = 'your_actual_token_here';

// 测试创建知识库
async function testCreateKnowledgeBase() {
  console.log('=== 测试创建知识库 ===');
  
  const data = {
    name: '测试知识库_' + Date.now(),
    description: '这是一个用于测试修改和删除的知识库'
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/knowledge-bases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TEST_TOKEN}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('创建失败:', errorText);
      return null;
    }

    const result = await response.json();
    console.log('创建成功:', result);
    return result;
  } catch (error) {
    console.error('创建请求失败:', error);
    return null;
  }
}

// 测试更新知识库
async function testUpdateKnowledgeBase(knowledgeBaseId) {
  console.log(`=== 测试更新知识库 ID: ${knowledgeBaseId} ===`);
  
  const updateData = {
    name: '更新后的知识库名称_' + Date.now(),
    description: '这是更新后的描述'
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/knowledge-bases/${knowledgeBaseId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TEST_TOKEN}`
      },
      body: JSON.stringify(updateData)
    });

    console.log('更新响应状态:', response.status);
    console.log('更新响应头:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('更新失败:', errorText);
      return false;
    }

    const result = await response.json();
    console.log('更新成功:', result);
    return true;
  } catch (error) {
    console.error('更新请求失败:', error);
    return false;
  }
}

// 测试删除知识库
async function testDeleteKnowledgeBase(knowledgeBaseId) {
  console.log(`=== 测试删除知识库 ID: ${knowledgeBaseId} ===`);
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/knowledge-bases/${knowledgeBaseId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${TEST_TOKEN}`
      }
    });

    console.log('删除响应状态:', response.status);
    console.log('删除响应头:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('删除失败:', errorText);
      return false;
    }

    const result = await response.json();
    console.log('删除成功:', result);
    return true;
  } catch (error) {
    console.error('删除请求失败:', error);
    return false;
  }
}

// 获取知识库列表
async function testGetKnowledgeBases() {
  console.log('=== 测试获取知识库列表 ===');
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/knowledge-bases`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${TEST_TOKEN}`
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('获取列表失败:', errorText);
      return null;
    }

    const result = await response.json();
    console.log('获取列表成功:', result);
    return result;
  } catch (error) {
    console.error('获取列表请求失败:', error);
    return null;
  }
}

// 完整测试流程
async function runFullTest() {
  console.log('开始完整测试流程...');
  
  // 1. 创建知识库
  const createdKb = await testCreateKnowledgeBase();
  if (!createdKb) {
    console.error('创建失败，停止测试');
    return;
  }
  
  const kbId = createdKb.id;
  console.log(`使用知识库ID: ${kbId} 进行后续测试`);
  
  // 等待一秒
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 2. 测试更新
  const updateSuccess = await testUpdateKnowledgeBase(kbId);
  if (!updateSuccess) {
    console.error('更新失败');
  }
  
  // 等待一秒
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 3. 获取列表验证更新
  await testGetKnowledgeBases();
  
  // 等待一秒
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 4. 测试删除
  const deleteSuccess = await testDeleteKnowledgeBase(kbId);
  if (!deleteSuccess) {
    console.error('删除失败');
  }
  
  // 5. 再次获取列表验证删除
  await testGetKnowledgeBases();
  
  console.log('完整测试流程结束');
}

// 使用说明
console.log('知识库操作测试脚本已加载');
console.log('使用前请先设置 TEST_TOKEN 为实际的认证token');
console.log('可用函数:');
console.log('- testCreateKnowledgeBase(): 测试创建');
console.log('- testUpdateKnowledgeBase(id): 测试更新');
console.log('- testDeleteKnowledgeBase(id): 测试删除');
console.log('- testGetKnowledgeBases(): 测试获取列表');
console.log('- runFullTest(): 运行完整测试流程');