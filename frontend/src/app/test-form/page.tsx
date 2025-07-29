/**
 * Test page for form validation
 */
'use client';

import { useState } from 'react';
import { LoginForm } from '@/components/auth/LoginForm';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { Card, Switch, Space, Typography } from 'antd';

const { Title } = Typography;

export default function TestFormPage() {
  const [showLogin, setShowLogin] = useState(true);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <Card>
          <Space direction="vertical" size="large" className="w-full">
            <div className="text-center">
              <Title level={2}>表单测试页面</Title>
              <Space>
                <span>注册</span>
                <Switch 
                  checked={showLogin} 
                  onChange={setShowLogin}
                />
                <span>登录</span>
              </Space>
            </div>
            
            <div className="flex justify-center">
              {showLogin ? (
                <LoginForm 
                  onSuccess={() => alert('登录成功！')}
                  onSwitchToRegister={() => setShowLogin(false)}
                />
              ) : (
                <RegisterForm 
                  onSuccess={() => alert('注册成功！')}
                  onSwitchToLogin={() => setShowLogin(true)}
                />
              )}
            </div>
          </Space>
        </Card>
      </div>
    </div>
  );
}