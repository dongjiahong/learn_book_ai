/**
 * Global keyboard shortcut provider
 */
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { HelpModal } from '@/components/feedback/HelpModal';


interface KeyboardShortcutProviderProps {
  children: React.ReactNode;
}

export const KeyboardShortcutProvider: React.FC<KeyboardShortcutProviderProps> = ({
  children,
}) => {
  const [helpModalOpen, setHelpModalOpen] = useState(false);
  const router = useRouter();


  const shortcuts = [
    {
      key: '/',
      description: '搜索',
      action: () => {
        // Focus search input if exists
        const searchInput = document.querySelector('input[placeholder*="搜索"]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      },
    },
    {
      key: 'd',
      ctrlKey: true,
      description: '前往仪表板',
      action: () => router.push('/dashboard'),
    },
    {
      key: 'k',
      ctrlKey: true,
      description: '前往知识库',
      action: () => router.push('/knowledge-bases'),
    },
    {
      key: 'q',
      ctrlKey: true,
      description: '前往问题管理',
      action: () => router.push('/questions'),
    },

    {
      key: 'r',
      ctrlKey: true,
      description: '刷新页面',
      action: () => window.location.reload(),
      preventDefault: false, // Allow default browser refresh
    },
    {
      key: 'n',
      ctrlKey: true,
      description: '新建项目',
      action: () => {
        // Try to find and click the "新建" or "添加" button
        const newButton = document.querySelector('button[title*="新建"], button[title*="添加"], button:contains("新建"), button:contains("添加")') as HTMLButtonElement;
        if (newButton) {
          newButton.click();
        }
      },
    },
    {
      key: 'b',
      ctrlKey: true,
      description: '切换侧边栏',
      action: () => {
        // Try to find and click the sidebar toggle button
        const toggleButton = document.querySelector('button[aria-label*="toggle"], button[title*="折叠"]') as HTMLButtonElement;
        if (toggleButton) {
          toggleButton.click();
        }
      },
    },

    {
      key: '?',
      description: '显示帮助',
      action: () => setHelpModalOpen(true),
    },
    {
      key: 'Escape',
      description: '关闭弹窗/取消',
      action: () => {
        // Close any open modals or drawers
        const closeButtons = document.querySelectorAll('.ant-modal-close, .ant-drawer-close, [aria-label="Close"]');
        if (closeButtons.length > 0) {
          (closeButtons[0] as HTMLButtonElement).click();
        } else {
          setHelpModalOpen(false);
        }
      },
    },
  ];

  useKeyboardShortcuts({ shortcuts });

  return (
    <>
      {children}
      <HelpModal
        open={helpModalOpen}
        onClose={() => setHelpModalOpen(false)}
        shortcuts={shortcuts}
      />
    </>
  );
};