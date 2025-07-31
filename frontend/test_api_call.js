// 测试创建知识库的API调用
// 这个脚本可以帮助调试Content-Type问题

const API_BASE_URL = 'http://172.18.3.1:8800';

// 调试函数：检查请求头
function debugRequest(url, options) {
  console.log('=== 请求调试信息 ===');
  console.log('URL:', url);
  console.log('Method:', options.method);
  console.log('Headers:', options.headers);
  console.log('Body:', options.body);
  console.log('Body type:', typeof options.body);
  console.log('===================');
}

async function testCreateKnowledgeBase() {
  // 模拟登录获取token（你需要替换为实际的token）
  const token = 'your_actual_token_here';
  
  const data = {
    name: '测试知识库',
    description: '这是一个测试知识库'
  };

  const requestOptions = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  };

  debugRequest(`${API_BASE_URL}/api/knowledge-bases`, requestOptions);

  try {
    const response = await fetch(`${API_BASE_URL}/api/knowledge-bases`, requestOptions);

    console.log('响应状态:', response.status);
    console.log('响应头:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('错误响应:', errorText);
      
      // 尝试解析为JSON看是否有更详细的错误信息
      try {
        const errorJson = JSON.parse(errorText);
        console.error('解析后的错误:', errorJson);
      } catch (e) {
        console.error('无法解析错误响应为JSON');
      }
      return;
    }

    const result = await response.json();
    console.log('成功响应:', result);
  } catch (error) {
    console.error('请求失败:', error);
  }
}

// 测试不同的Content-Type设置
async function testDifferentContentTypes() {
  const token = 'your_actual_token_here';
  const data = {
    name: '测试知识库2',
    description: '测试不同Content-Type'
  };

  const tests = [
    {
      name: '标准application/json',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    },
    {
      name: '显式设置charset',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': `Bearer ${token}`
      }
    },
    {
      name: '不设置Content-Type',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  ];

  for (const test of tests) {
    console.log(`\n=== 测试: ${test.name} ===`);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/knowledge-bases`, {
        method: 'POST',
        headers: test.headers,
        body: JSON.stringify(data)
      });

      console.log('状态:', response.status);
      console.log('请求头:', test.headers);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('错误:', errorText);
      } else {
        const result = await response.json();
        console.log('成功:', result);
      }
    } catch (error) {
      console.error('请求失败:', error);
    }
  }
}

// 在浏览器控制台中运行这些函数
console.log('可用的测试函数:');
console.log('1. testCreateKnowledgeBase() - 基本测试');
console.log('2. testDifferentContentTypes() - 测试不同Content-Type');
console.log('记得先替换token为实际的认证token');