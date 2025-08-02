'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api';
import type { 
  KnowledgeBase, 
  AnkiExportResponse, 
  KnowledgePoint 
} from '@/lib/api';

interface AnkiCustomExportFormProps {
  knowledgeBases: KnowledgeBase[];
  onExportComplete: (exportData: AnkiExportResponse) => void;
  exporting: boolean;
  setExporting: (exporting: boolean) => void;
}

export function AnkiCustomExportForm({ 
  knowledgeBases, 
  onExportComplete, 
  exporting, 
  setExporting 
}: AnkiCustomExportFormProps) {
  const { tokens } = useAuthStore();
  const token = tokens?.access_token;
  const [deckName, setDeckName] = useState('');
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<number | null>(null);
  const [knowledgePoints, setKnowledgePoints] = useState<KnowledgePoint[]>([]);
  const [selectedKnowledgePoints, setSelectedKnowledgePoints] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);


  const loadKnowledgeBaseContent = useCallback(async () => {
    if (!selectedKnowledgeBase || !token) return;

    try {
      setLoading(true);
      setError(null);

      // Load knowledge points only
      const kpResponse = await apiClient.getKnowledgePoints(token, {
        knowledge_base_id: selectedKnowledgeBase,
        limit: 500
      });
      setKnowledgePoints(kpResponse.knowledge_points);

    } catch (error) {
      console.error('Failed to load content:', error);
      setError('加载内容失败');
    } finally {
      setLoading(false);
    }
  }, [selectedKnowledgeBase, token]);

  useEffect(() => {
    if (selectedKnowledgeBase && token) {
      loadKnowledgeBaseContent();
    }
  }, [loadKnowledgeBaseContent, selectedKnowledgeBase, token]);

  const handleKnowledgePointToggle = (kpId: number) => {
    setSelectedKnowledgePoints(prev => 
      prev.includes(kpId) 
        ? prev.filter(id => id !== kpId)
        : [...prev, kpId]
    );
  };

  const handleSelectAllKnowledgePoints = () => {
    if (selectedKnowledgePoints.length === knowledgePoints.length) {
      setSelectedKnowledgePoints([]);
    } else {
      setSelectedKnowledgePoints(knowledgePoints.map(kp => kp.id));
    }
  };

  const handleExport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !deckName.trim() || selectedKnowledgePoints.length === 0) {
      return;
    }

    try {
      setExporting(true);
      setError(null);

      const exportData = await apiClient.exportCustomAnkiDeck(token, {
        deck_name: deckName.trim(),
        knowledge_point_ids: selectedKnowledgePoints
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
      setSelectedKnowledgePoints([]);
      setSelectedKnowledgeBase(null);
      setKnowledgePoints([]);

    } catch (error) {
      console.error('Export failed:', error);
      setError(error instanceof Error ? error.message : '导出失败');
    } finally {
      setExporting(false);
    }
  };

  const getImportanceColor = (level: number) => {
    if (level >= 4) return 'text-red-600 bg-red-100';
    if (level >= 3) return 'text-yellow-600 bg-yellow-100';
    return 'text-blue-600 bg-blue-100';
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">自定义选择导出</h2>
      <p className="text-gray-600 mb-6">
        精确选择要导出的知识点，创建个性化的Anki卡片包
      </p>

      <form onSubmit={handleExport} className="space-y-6">
        {/* Deck Name */}
        <div>
          <label htmlFor="customDeckName" className="block text-sm font-medium text-gray-700 mb-2">
            卡片包名称 *
          </label>
          <input
            type="text"
            id="customDeckName"
            value={deckName}
            onChange={(e) => setDeckName(e.target.value)}
            placeholder="输入自定义卡片包名称"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
        </div>

        {/* Knowledge Base Selection */}
        <div>
          <label htmlFor="knowledgeBaseSelect" className="block text-sm font-medium text-gray-700 mb-2">
            选择知识库 *
          </label>
          <select
            id="knowledgeBaseSelect"
            value={selectedKnowledgeBase || ''}
            onChange={(e) => {
              const value = e.target.value;
              setSelectedKnowledgeBase(value ? parseInt(value) : null);
              setSelectedKnowledgePoints([]);
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
            <option value="">请选择知识库</option>
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id}>
                {kb.name} ({kb.document_count || 0} 文档, {kb.knowledge_point_count || 0} 知识点)
              </option>
            ))}
          </select>
        </div>

        {/* Knowledge Points Selection */}
        {selectedKnowledgeBase && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-700">
                选择知识点 ({knowledgePoints.length})
              </h3>
              {knowledgePoints.length > 0 && (
                <button
                  type="button"
                  onClick={handleSelectAllKnowledgePoints}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {selectedKnowledgePoints.length === knowledgePoints.length ? '取消全选' : '全选'}
                </button>
              )}
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">加载中...</span>
              </div>
            ) : knowledgePoints.length === 0 ? (
              <p className="text-gray-500 text-sm py-4">该知识库暂无知识点</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto border border-gray-200 rounded-md p-3">
                {knowledgePoints.map((kp) => (
                  <label key={kp.id} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="checkbox"
                      checked={selectedKnowledgePoints.includes(kp.id)}
                      onChange={() => handleKnowledgePointToggle(kp.id)}
                      className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        {kp.title}
                      </p>
                      <p className="text-xs text-gray-600 mb-2 line-clamp-3">
                        {kp.content}
                      </p>
                      <div className="flex items-center space-x-4 text-xs">
                        <span className={`px-2 py-1 rounded-full font-medium ${getImportanceColor(kp.importance_level)}`}>
                          重要度 {kp.importance_level}
                        </span>
                        <span className="text-gray-500">
                          {new Date(kp.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>
        )}

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
            disabled={
              exporting || 
              !deckName.trim() || 
              !selectedKnowledgeBase ||
              selectedKnowledgePoints.length === 0
            }
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {exporting ? '导出中...' : `创建并下载 (${selectedKnowledgePoints.length} 个知识点)`}
          </button>
        </div>
      </form>
    </div>
  );
}