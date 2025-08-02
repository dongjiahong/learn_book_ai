/**
 * Help modal component showing keyboard shortcuts and tips
 */
'use client';

import React from 'react';
import { Modal, Typography, Divider, Tag, Space, Grid } from 'antd';
import {
  SettingOutlined,
  QuestionCircleOutlined,
  BulbOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { useBreakpoint } = Grid;

interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  metaKey?: boolean;
  description: string;
}

interface HelpModalProps {
  open: boolean;
  onClose: () => void;
  shortcuts?: KeyboardShortcut[];
}

export const HelpModal: React.FC<HelpModalProps> = ({
  open,
  onClose,
  shortcuts = [],
}) => {
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  const defaultShortcuts: KeyboardShortcut[] = [
    { key: '/', description: '搜索' },
    { key: 'd', ctrlKey: true, description: '前往仪表板' },
    { key: 'k', ctrlKey: true, description: '前往知识库' },
    { key: 'q', ctrlKey: true, description: '前往问题管理' },
    { key: 'n', ctrlKey: true, description: '新建项目' },
    { key: 's', ctrlKey: true, description: '保存' },
    { key: 'r', ctrlKey: true, description: '刷新页面' },
    { key: 'b', ctrlKey: true, description: '切换侧边栏' },
    { key: 't', ctrlKey: true, description: '切换主题' },
    { key: '?', description: '显示此帮助' },
    { key: 'Escape', description: '取消/关闭' },
  ];

  const allShortcuts = shortcuts.length > 0 ? shortcuts : defaultShortcuts;

  const formatKey = (shortcut: KeyboardShortcut) => {
    const keys = [];

    if (shortcut.ctrlKey) keys.push(isMobile ? 'Ctrl' : '⌘');
    if (shortcut.altKey) keys.push('Alt');
    if (shortcut.shiftKey) keys.push('Shift');
    if (shortcut.metaKey) keys.push('Meta');

    keys.push(shortcut.key === ' ' ? 'Space' : shortcut.key);

    return keys;
  };

  const tips = [
    {
      icon: <BulbOutlined className="text-yellow-500" />,
      title: '快速上传',
      description: '拖拽文件到页面任意位置即可快速上传文档',
    },
    {
      icon: <BulbOutlined className="text-yellow-500" />,
      title: '批量操作',
      description: '按住 Shift 键可以选择多个项目进行批量操作',
    },
    {
      icon: <BulbOutlined className="text-yellow-500" />,
      title: '自动保存',
      description: '表单内容会自动保存到本地，避免意外丢失',
    },
    {
      icon: <BulbOutlined className="text-yellow-500" />,
      title: '深色模式',
      description: '系统会根据您的设备设置自动切换主题',
    },
  ];

  return (
    <Modal
      title={
        <Space>
          <QuestionCircleOutlined />
          <span>帮助与快捷键</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={isMobile ? '90%' : 600}
      className="help-modal"
    >
      <div className="space-y-6">
        {/* Keyboard Shortcuts */}
        <div>
          <Title level={4} className="flex items-center space-x-2 !mb-4">
            <SettingOutlined />
            <span>键盘快捷键</span>
          </Title>

          <div className="space-y-3">
            {allShortcuts.map((shortcut, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-2 px-3 rounded-lg bg-gray-50"
              >
                <Text className={isMobile ? 'text-sm' : 'text-base'}>
                  {shortcut.description}
                </Text>
                <Space size="small">
                  {formatKey(shortcut).map((key, keyIndex) => (
                    <Tag
                      key={keyIndex}
                      className="font-mono text-xs px-2 py-1 bg-white border border-gray-300"
                    >
                      {key}
                    </Tag>
                  ))}
                </Space>
              </div>
            ))}
          </div>
        </div>

        <Divider />

        {/* Tips */}
        <div>
          <Title level={4} className="!mb-4">
            使用技巧
          </Title>

          <div className="space-y-4">
            {tips.map((tip, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {tip.icon}
                </div>
                <div>
                  <Text strong className={`block ${isMobile ? 'text-sm' : 'text-base'}`}>
                    {tip.title}
                  </Text>
                  <Text
                    type="secondary"
                    className={`block mt-1 ${isMobile ? 'text-xs' : 'text-sm'}`}
                  >
                    {tip.description}
                  </Text>
                </div>
              </div>
            ))}
          </div>
        </div>

        <Divider />

        {/* Additional Info */}
        <div>
          <Paragraph type="secondary" className={isMobile ? 'text-xs' : 'text-sm'}>
            <strong>提示：</strong>在输入框中输入时，键盘快捷键会被暂时禁用。
            如果遇到问题，请尝试刷新页面或联系技术支持。
          </Paragraph>
        </div>
      </div>
    </Modal>
  );
};