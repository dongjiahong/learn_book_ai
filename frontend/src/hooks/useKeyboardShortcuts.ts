/**
 * Hook for managing keyboard shortcuts
 */
'use client';

import { useEffect, useCallback } from 'react';

interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  metaKey?: boolean;
  action: () => void;
  description: string;
  preventDefault?: boolean;
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
}

export const useKeyboardShortcuts = ({ shortcuts, enabled = true }: UseKeyboardShortcutsOptions) => {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return;

    // Don't trigger shortcuts when user is typing in input fields
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.contentEditable === 'true'
    ) {
      return;
    }

    const matchingShortcut = shortcuts.find(shortcut => {
      const keyMatch = shortcut.key.toLowerCase() === event.key.toLowerCase();
      const ctrlMatch = !!shortcut.ctrlKey === event.ctrlKey;
      const altMatch = !!shortcut.altKey === event.altKey;
      const shiftMatch = !!shortcut.shiftKey === event.shiftKey;
      const metaMatch = !!shortcut.metaKey === event.metaKey;

      return keyMatch && ctrlMatch && altMatch && shiftMatch && metaMatch;
    });

    if (matchingShortcut) {
      if (matchingShortcut.preventDefault !== false) {
        event.preventDefault();
      }
      matchingShortcut.action();
    }
  }, [shortcuts, enabled]);

  useEffect(() => {
    if (enabled) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [handleKeyDown, enabled]);

  return { shortcuts };
};

// Common keyboard shortcuts
export const commonShortcuts = {
  // Navigation
  goToSearch: { key: '/', description: '搜索' },
  goToDashboard: { key: 'd', ctrlKey: true, description: '前往仪表板' },
  goToKnowledgeBases: { key: 'k', ctrlKey: true, description: '前往知识库' },
  goToQuestions: { key: 'q', ctrlKey: true, description: '前往问题管理' },
  
  // Actions
  save: { key: 's', ctrlKey: true, description: '保存' },
  refresh: { key: 'r', ctrlKey: true, description: '刷新' },
  newItem: { key: 'n', ctrlKey: true, description: '新建' },
  delete: { key: 'Delete', description: '删除' },
  
  // UI
  toggleSidebar: { key: 'b', ctrlKey: true, description: '切换侧边栏' },
  toggleTheme: { key: 't', ctrlKey: true, description: '切换主题' },
  showHelp: { key: '?', description: '显示帮助' },
  
  // Escape
  escape: { key: 'Escape', description: '取消/关闭' },
};