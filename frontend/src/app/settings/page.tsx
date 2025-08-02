'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Switch,
  Divider,
  message,
  Tabs,
  Space,
  Alert,
  InputNumber,
  Typography,
  Spin,
  Tag
} from 'antd';
import {
  SettingOutlined,
  ApiOutlined,
  CloudOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  SaveOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ResponsiveLayout } from '@/components/layout/ResponsiveLayout';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface ModelSettings {
  provider: string;
  fallback_provider?: string;
  openai_api_key_set: boolean;
  openai_base_url: string;
  openai_model: string;
  openai_embedding_model: string;
  ollama_base_url: string;
  ollama_model: string;
  embedding_provider: string;
  embedding_model: string;
  embedding_dimension: number;
  openai_embedding_dimension: number;
  temperature: number;
  max_tokens: number;
  timeout: number;
}

interface ModelStatus {
  active_provider: string;
  fallback_provider?: string;
  openai_configured: boolean;
  ollama_configured: boolean;
  embedding_provider: string;
  health_check_interval: number;
}

export default function SettingsPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const [settings, setSettings] = useState<ModelSettings | null>(null);
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const { tokens } = useAuth();

  // 加载设置
  const loadSettings = async () => {
    if (!tokens?.access_token) return;

    try {
      setLoading(true);
      const [settingsResponse, statusResponse] = await Promise.all([
        apiClient.getModelSettings(tokens.access_token),
        apiClient.getModelStatus(tokens.access_token)
      ]);

      setSettings(settingsResponse);
      setStatus(statusResponse);

      // 设置表单值
      form.setFieldsValue({
        provider: settingsResponse.provider,
        fallback_provider: settingsResponse.fallback_provider,
        openai_base_url: settingsResponse.openai_base_url,
        openai_model: settingsResponse.openai_model,
        openai_embedding_model: settingsResponse.openai_embedding_model,
        ollama_base_url: settingsResponse.ollama_base_url,
        ollama_model: settingsResponse.ollama_model,
        embedding_provider: settingsResponse.embedding_provider,
        embedding_model: settingsResponse.embedding_model,
        embedding_dimension: settingsResponse.embedding_dimension,
        openai_embedding_model: settingsResponse.openai_embedding_model,
        openai_embedding_dimension: settingsResponse.openai_embedding_dimension,
        temperature: settingsResponse.temperature,
        max_tokens: settingsResponse.max_tokens,
      });
    } catch (error) {
      console.error('加载设置失败:', error);
      message.error('加载设置失败');
    } finally {
      setLoading(false);
    }
  };

  // 保存设置
  const handleSave = async (values: any) => {
    if (!tokens?.access_token) return;

    try {
      setLoading(true);

      const updateData: Record<string, any> = {};

      // 只发送有变化的字段
      if (values.provider !== settings?.provider) {
        updateData.provider = values.provider;
      }
      if (values.fallback_provider !== settings?.fallback_provider) {
        updateData.fallback_provider = values.fallback_provider;
      }
      if (values.openai_api_key) {
        updateData.openai_api_key = values.openai_api_key;
      }
      if (values.openai_base_url !== settings?.openai_base_url) {
        updateData.openai_base_url = values.openai_base_url;
      }
      if (values.openai_model !== settings?.openai_model) {
        updateData.openai_model = values.openai_model;
      }
      if (values.openai_embedding_model !== settings?.openai_embedding_model) {
        updateData.openai_embedding_model = values.openai_embedding_model;
      }
      if (values.ollama_base_url !== settings?.ollama_base_url) {
        updateData.ollama_base_url = values.ollama_base_url;
      }
      if (values.ollama_model !== settings?.ollama_model) {
        updateData.ollama_model = values.ollama_model;
      }
      if (values.embedding_provider !== settings?.embedding_provider) {
        updateData.embedding_provider = values.embedding_provider;
      }
      if (values.embedding_model !== settings?.embedding_model) {
        updateData.embedding_model = values.embedding_model;
      }
      if (values.embedding_dimension !== settings?.embedding_dimension) {
        updateData.embedding_dimension = values.embedding_dimension;
      }
      if (values.openai_embedding_model !== settings?.openai_embedding_model) {
        updateData.openai_embedding_model_name = values.openai_embedding_model;
      }
      if (values.openai_embedding_dimension !== settings?.openai_embedding_dimension) {
        updateData.openai_embedding_dimension = values.openai_embedding_dimension;
      }
      if (values.temperature !== settings?.temperature) {
        updateData.temperature = values.temperature;
      }
      if (values.max_tokens !== settings?.max_tokens) {
        updateData.max_tokens = values.max_tokens;
      }

      await apiClient.updateModelSettings(tokens.access_token, updateData);
      message.success('设置保存成功');

      // 重新加载设置
      await loadSettings();
    } catch (error) {
      console.error('保存设置失败:', error);
      message.error('保存设置失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试连接
  const testConnection = async (provider: string) => {
    if (!tokens?.access_token) return;

    try {
      setTestingConnection(provider);
      const response = await apiClient.testModelConnection(tokens.access_token, provider);

      if (response.success) {
        message.success(`${provider} 连接测试成功`);
      } else {
        message.error(`${provider} 连接测试失败: ${response.error}`);
      }
    } catch (error) {
      console.error('连接测试失败:', error);
      message.error('连接测试失败');
    } finally {
      setTestingConnection(null);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const tabItems = [
    {
      key: 'models',
      label: (
        <span>
          <ApiOutlined />
          模型配置
        </span>
      ),
      children: (
        <div className="space-y-6">
          {/* 基础配置 */}
          <Card title="基础配置" size="small">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                label="主要提供商"
                name="provider"
                rules={[{ required: true, message: '请选择主要提供商' }]}
              >
                <Select>
                  <Option value="ollama">Ollama (本地)</Option>
                  <Option value="openai">OpenAI</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="备用提供商"
                name="fallback_provider"
              >
                <Select allowClear placeholder="选择备用提供商">
                  <Option value="ollama">Ollama (本地)</Option>
                  <Option value="openai">OpenAI</Option>
                </Select>
              </Form.Item>
            </div>
          </Card>

          {/* OpenAI 配置 */}
          <Card
            title={
              <div className="flex items-center justify-between">
                <span>
                  <CloudOutlined className="mr-2" />
                  OpenAI 配置
                </span>
                <div className="flex items-center space-x-2">
                  {status?.openai_configured && (
                    <Tag color="green">已配置</Tag>
                  )}
                  <Button
                    size="small"
                    icon={<ExperimentOutlined />}
                    loading={testingConnection === 'openai'}
                    onClick={() => testConnection('openai')}
                  >
                    测试连接
                  </Button>
                </div>
              </div>
            }
            size="small"
          >
            <div className="space-y-4">
              <Form.Item
                label="API Key"
                name="openai_api_key"
                extra={settings?.openai_api_key_set ? "API Key 已设置" : "请输入 OpenAI API Key"}
              >
                <Input.Password
                  placeholder={settings?.openai_api_key_set ? "••••••••••••••••" : "sk-..."}
                />
              </Form.Item>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Form.Item
                  label="API 基础 URL"
                  name="openai_base_url"
                >
                  <Input placeholder="https://api.openai.com/v1" />
                </Form.Item>

                <Form.Item
                  label="聊天模型"
                  name="openai_model"
                >
                  <Input placeholder="gpt-4" />
                </Form.Item>
              </div>

              <Form.Item
                label="嵌入模型"
                name="openai_embedding_model"
              >
                <Input placeholder="text-embedding-3-large" />
              </Form.Item>
            </div>
          </Card>

          {/* Ollama 配置 */}
          <Card
            title={
              <div className="flex items-center justify-between">
                <span>
                  <DatabaseOutlined className="mr-2" />
                  Ollama 配置
                </span>
                <div className="flex items-center space-x-2">
                  {status?.ollama_configured && (
                    <Tag color="blue">已配置</Tag>
                  )}
                  <Button
                    size="small"
                    icon={<ExperimentOutlined />}
                    loading={testingConnection === 'ollama'}
                    onClick={() => testConnection('ollama')}
                  >
                    测试连接
                  </Button>
                </div>
              </div>
            }
            size="small"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                label="服务器地址"
                name="ollama_base_url"
              >
                <Input placeholder="http://localhost:11434" />
              </Form.Item>

              <Form.Item
                label="模型名称"
                name="ollama_model"
              >
                <Input placeholder="qwen3:1.7b" />
              </Form.Item>
            </div>
          </Card>

          {/* 生成参数 */}
          <Card title="生成参数" size="small">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                label="温度"
                name="temperature"
                extra="控制生成文本的随机性 (0.0-2.0)"
              >
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item
                label="最大令牌数"
                name="max_tokens"
                extra="生成文本的最大长度"
              >
                <InputNumber
                  min={1}
                  max={8192}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </div>
          </Card>
        </div>
      ),
    },
    {
      key: 'embeddings',
      label: (
        <span>
          <DatabaseOutlined />
          嵌入配置
        </span>
      ),
      children: (
        <div className="space-y-6">
          <Card title="嵌入模型配置" size="small">
            <div className="space-y-4">
              <Form.Item
                label="嵌入提供商"
                name="embedding_provider"
                rules={[{ required: true, message: '请选择嵌入提供商' }]}
              >
                <Select>
                  <Option value="ollama">Ollama (本地)</Option>
                  <Option value="openai">OpenAI</Option>
                </Select>
              </Form.Item>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Form.Item
                  label="Ollama 嵌入模型"
                  name="embedding_model"
                >
                  <Input placeholder="shaw/dmeta-embedding-zh-small-q4" />
                </Form.Item>

                <Form.Item
                  label="嵌入维度"
                  name="embedding_dimension"
                >
                  <InputNumber
                    min={1}
                    max={4096}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </div>

              <Divider>OpenAI 嵌入配置</Divider>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Form.Item
                  label="OpenAI 嵌入模型"
                  name="openai_embedding_model"
                >
                  <Input placeholder="text-embedding-3-large" />
                </Form.Item>

                <Form.Item
                  label="OpenAI 嵌入维度"
                  name="openai_embedding_dimension"
                >
                  <InputNumber
                    min={1}
                    max={3072}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </div>
            </div>
          </Card>
        </div>
      ),
    },
  ];

  if (loading && !settings) {
    return (
      <ProtectedRoute>
        <ResponsiveLayout>
          <div className="flex justify-center items-center h-64">
            <Spin size="large" />
          </div>
        </ResponsiveLayout>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <ResponsiveLayout>
        <div className="max-w-6xl mx-auto p-6">
          <div className="mb-6">
            <Title level={2}>
              <SettingOutlined className="mr-2" />
              系统设置
            </Title>
            <Text type="secondary">
              配置模型提供商、API 密钥和其他系统参数
            </Text>
          </div>

          {status && (
            <Alert
              message="当前状态"
              description={
                <div className="space-y-1">
                  <div>主要提供商: <Tag color="blue">{status.active_provider}</Tag></div>
                  {status.fallback_provider && (
                    <div>备用提供商: <Tag color="orange">{status.fallback_provider}</Tag></div>
                  )}
                  <div>嵌入提供商: <Tag color="green">{status.embedding_provider}</Tag></div>
                </div>
              }
              type="info"
              showIcon
              className="mb-6"
            />
          )}

          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
            disabled={loading}
          >
            <Tabs items={tabItems} />

            <div className="mt-6 flex justify-end space-x-2">
              <Button
                icon={<ReloadOutlined />}
                onClick={loadSettings}
                disabled={loading}
              >
                重新加载
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                htmlType="submit"
                loading={loading}
              >
                保存设置
              </Button>
            </div>
          </Form>
        </div>
      </ResponsiveLayout>
    </ProtectedRoute>
  );
}