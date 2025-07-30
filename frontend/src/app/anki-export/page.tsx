'use client';

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api';
import type { 
  KnowledgeBase, 
  AnkiExportResponse, 
  AnkiExportListItem,
  AnswerRecord,
  KnowledgePoint
} from '@/lib/api';
import { MainLayout } from '@/components/layout/MainLayout';
import { AnkiExportForm } from '@/components/anki/AnkiExportForm';
import { AnkiExportHistory } from '@/components/anki/AnkiExportHistory';
import { AnkiCustomExportForm } from '@/components/anki/AnkiCustomExportForm';

export default function AnkiExportPage() {
  const { user, token } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'knowledge-base' | 'custom' | 'history'>('knowledge-base');
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [exports, setExports] = useState<AnkiExportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (token) {
      loadData();
    }
  }, [token]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load knowledge bases
      const kbResponse = await apiClient.getKnowledgeBases(token!, 0, 100);
      setKnowledgeBases(kbResponse.knowledge_bases);
      
      // Load export history
      const exportsResponse = await apiClient.getAnkiExports(token!);
      setExports(exportsResponse.exports);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportComplete = (exportData: AnkiExportResponse) => {
    // Add new export to history
    setExports(prev => [{
      export_id: exportData.export_id,
      deck_name: exportData.deck_name,
      created_at: exportData.created_at,
      card_count: exportData.card_count
    }, ...prev]);
    
    // Switch to history tab to show the new export
    setActiveTab('history');
  };

  const handleExportDeleted = (exportId: string) => {
    setExports(prev => prev.filter(exp => exp.export_id !== exportId));
  };

  if (!user) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">请先登录</h2>
            <p className="text-gray-600">您需要登录才能使用Anki导出功能</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Anki 导出</h1>
          <p className="text-gray-600">
            将您的学习记录和知识点导出为Anki卡片，支持离线学习和复习
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('knowledge-base')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'knowledge-base'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              知识库导出
            </button>
            <button
              onClick={() => setActiveTab('custom')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'custom'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              自定义导出
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              导出历史
              {exports.length > 0 && (
                <span className="ml-2 bg-blue-100 text-blue-600 py-1 px-2 rounded-full text-xs">
                  {exports.length}
                </span>
              )}
            </button>
          </nav>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">加载中...</span>
          </div>
        ) : (
          <div>
            {activeTab === 'knowledge-base' && (
              <AnkiExportForm
                knowledgeBases={knowledgeBases}
                onExportComplete={handleExportComplete}
                exporting={exporting}
                setExporting={setExporting}
              />
            )}
            
            {activeTab === 'custom' && (
              <AnkiCustomExportForm
                knowledgeBases={knowledgeBases}
                onExportComplete={handleExportComplete}
                exporting={exporting}
                setExporting={setExporting}
              />
            )}
            
            {activeTab === 'history' && (
              <AnkiExportHistory
                exports={exports}
                onExportDeleted={handleExportDeleted}
                onRefresh={loadData}
              />
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}