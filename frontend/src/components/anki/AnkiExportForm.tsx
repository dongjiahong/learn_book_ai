'use client';

import React, { useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api';
import type { KnowledgeBase, AnkiExportResponse } from '@/lib/api';

interface AnkiExportFormProps {
  knowledgeBases: KnowledgeBase[];
  onExportComplete: (exportData: AnkiExportResponse) => void;
  exporting: boolean;
  setExporting: (exporting: boolean) => void;
}

export function AnkiExportForm({ 
  knowledgeBases, 
  onExportComplete, 
  exporting, 
  setExporting 
}: AnkiExportFormProps) {
  const { tokens } = useAuthStore();
  const token = tokens?.access_token;
  const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState<number[]>([]);
  const [deckName, setDeckName] = useState('');

  const [error, setError] = useState<string | null>(null);

  const handleKnowledgeBaseToggle = (kbId: number) => {
    setSelectedKnowledgeBases(prev => 
      prev.includes(kbId) 
        ? prev.filter(id => id !== kbId)
        : [...prev, kbId]
    );
  };

  const handleSelectAll = () => {
    if (selectedKnowledgeBases.length === knowledgeBases.length) {
      setSelectedKnowledgeBases([]);
    } else {
      setSelectedKnowledgeBases(knowledgeBases.map(kb => kb.id));
    }
  };

  const handleQuickExport = async (kbId: number, kbName: string) => {
    if (!token) return;

    try {
      setExporting(true);
      setError(null);

      const exportData = await apiClient.exportKnowledgeBaseAnkiDeck(
        token,
        kbId
      );

      onExportComplete(exportData);
      
      // Trigger download
      const blob = await apiClient.downloadAnkiDeck(token, exportData.export_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${exportData.deck_name.replace(/\s+/g, '_')}.apkg`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      console.error('Export failed:', error);
      setError(error instanceof Error ? error.message : '导出失败');
    } finally {
      setExporting(false);
    }
  };

  const handleCustomExport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || selectedKnowledgeBases.length === 0 || !deckName.trim()) return;

    try {
      setExporting(true);
      setError(null);

      const exportData = await apiClient.exportAnkiDeck(token, {
        deck_name: deckName.trim(),
        knowledge_base_ids: selectedKnowledgeBases
      });

      onExportComplete(exportData);
      
      // Trigger download
      const blob = await apiClient.downloadAnkiDeck(token, exportData.export_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${exportData.deck_name.replace(/\s+/g, '_')}.apkg`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Reset form
      setDeckName('');
      setSelectedKnowledgeBases([]);

    } catch (error) {
      console.error('Export failed:', error);
      setError(error instanceof Error ? error.message : '导出失败');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Quick Export Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">快速导出</h2>
        <p className="text-gray-600 mb-4">
          为每个知识库单独创建Anki卡片包，包含所有知识点
        </p>
        
        {knowledgeBases.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">暂无知识库</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {knowledgeBases.map((kb) => (
              <div key={kb.id} className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">{kb.name}</h3>
                {kb.description && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {kb.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
                  <span>文档数: {kb.document_count || 0}</span>
                  <span>知识点: {kb.knowledge_point_count || 0}</span>
                </div>
                <div className="text-xs text-gray-400 mb-3">
                  创建于: {new Date(kb.created_at).toLocaleDateString()}
                </div>
                <button
                  onClick={() => handleQuickExport(kb.id, kb.name)}
                  disabled={exporting}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                >
                  {exporting ? '导出中...' : '导出'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Custom Export Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">自定义导出</h2>
        <p className="text-gray-600 mb-6">
          选择多个知识库，创建合并的Anki卡片包
        </p>

        <form onSubmit={handleCustomExport} className="space-y-6">
          {/* Deck Name */}
          <div>
            <label htmlFor="deckName" className="block text-sm font-medium text-gray-700 mb-2">
              卡片包名称 *
            </label>
            <input
              type="text"
              id="deckName"
              value={deckName}
              onChange={(e) => setDeckName(e.target.value)}
              placeholder="输入Anki卡片包名称"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Knowledge Base Selection */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-medium text-gray-700">
                选择知识库 *
              </label>
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {selectedKnowledgeBases.length === knowledgeBases.length ? '取消全选' : '全选'}
              </button>
            </div>
            
            {knowledgeBases.length === 0 ? (
              <p className="text-gray-500 text-sm">暂无知识库</p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-md p-3">
                {knowledgeBases.map((kb) => (
                  <label key={kb.id} className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedKnowledgeBases.includes(kb.id)}
                      onChange={() => handleKnowledgeBaseToggle(kb.id)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{kb.name}</p>
                      {kb.description && (
                        <p className="text-xs text-gray-500 truncate">{kb.description}</p>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">
                      {kb.document_count || 0} 文档
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Export Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-blue-800">
                  <strong>导出内容：</strong>将导出选中知识库中的所有知识点，生成问答形式的Anki卡片
                </p>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={exporting || selectedKnowledgeBases.length === 0 || !deckName.trim()}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {exporting ? '导出中...' : '创建并下载'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}