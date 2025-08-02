'use client';

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api';
import type { 
  KnowledgeBase, 
  AnkiExportResponse, 
  AnswerRecord, 
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
  const [answerRecords, setAnswerRecords] = useState<AnswerRecord[]>([]);
  const [knowledgePoints, setKnowledgePoints] = useState<KnowledgePoint[]>([]);
  const [selectedAnswerRecords, setSelectedAnswerRecords] = useState<number[]>([]);
  const [selectedKnowledgePoints, setSelectedKnowledgePoints] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'qa' | 'kp'>('qa');

  useEffect(() => {
    if (selectedKnowledgeBase && token) {
      loadKnowledgeBaseContent();
    }
  }, [selectedKnowledgeBase, token]);

  const loadKnowledgeBaseContent = async () => {
    if (!selectedKnowledgeBase || !token) return;

    try {
      setLoading(true);
      setError(null);

      // Load answer records
      const answerResponse = await apiClient.getAnswerRecords(
        token,
        undefined,
        selectedKnowledgeBase,
        0,
        1000
      );
      setAnswerRecords(answerResponse.records);

      // Load knowledge points
      const kpResponse = await apiClient.getKnowledgePoints(token, {
        knowledge_base_id: selectedKnowledgeBase,
        limit: 1000
      });
      setKnowledgePoints(kpResponse.knowledge_points);

    } catch (error) {
      console.error('Failed to load content:', error);
      setError('加载内容失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerRecordToggle = (recordId: number) => {
    setSelectedAnswerRecords(prev => 
      prev.includes(recordId) 
        ? prev.filter(id => id !== recordId)
        : [...prev, recordId]
    );
  };

  const handleKnowledgePointToggle = (kpId: number) => {
    setSelectedKnowledgePoints(prev => 
      prev.includes(kpId) 
        ? prev.filter(id => id !== kpId)
        : [...prev, kpId]
    );
  };

  const handleSelectAllAnswerRecords = () => {
    if (selectedAnswerRecords.length === answerRecords.length) {
      setSelectedAnswerRecords([]);
    } else {
      setSelectedAnswerRecords(answerRecords.map(record => record.id));
    }
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
    if (!token || !deckName.trim() || (selectedAnswerRecords.length === 0 && selectedKnowledgePoints.length === 0)) {
      return;
    }

    try {
      setExporting(true);
      setError(null);

      const exportData = await apiClient.exportCustomAnkiDeck(token, {
        deck_name: deckName.trim(),
        answer_record_ids: selectedAnswerRecords.length > 0 ? selectedAnswerRecords : undefined,
        knowledge_point_ids: selectedKnowledgePoints.length > 0 ? selectedKnowledgePoints : undefined
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
      setSelectedAnswerRecords([]);
      setSelectedKnowledgePoints([]);
      setSelectedKnowledgeBase(null);
      setAnswerRecords([]);
      setKnowledgePoints([]);

    } catch (error) {
      console.error('Export failed:', error);
      setError(error instanceof Error ? error.message : '导出失败');
    } finally {
      setExporting(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600 bg-green-100';
    if (score >= 6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
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
        精确选择要导出的问答记录和知识点，创建个性化的Anki卡片包
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
              setSelectedAnswerRecords([]);
              setSelectedKnowledgePoints([]);
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
            <option value="">请选择知识库</option>
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id}>
                {kb.name} ({kb.document_count || 0} 文档)
              </option>
            ))}
          </select>
        </div>

        {/* Content Selection */}
        {selectedKnowledgeBase && (
          <div>
            <div className="border-b border-gray-200 mb-4">
              <nav className="-mb-px flex space-x-8">
                <button
                  type="button"
                  onClick={() => setActiveSection('qa')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeSection === 'qa'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  问答记录
                  {answerRecords.length > 0 && (
                    <span className="ml-2 bg-gray-100 text-gray-600 py-1 px-2 rounded-full text-xs">
                      {selectedAnswerRecords.length}/{answerRecords.length}
                    </span>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setActiveSection('kp')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeSection === 'kp'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  知识点
                  {knowledgePoints.length > 0 && (
                    <span className="ml-2 bg-gray-100 text-gray-600 py-1 px-2 rounded-full text-xs">
                      {selectedKnowledgePoints.length}/{knowledgePoints.length}
                    </span>
                  )}
                </button>
              </nav>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">加载中...</span>
              </div>
            ) : (
              <div>
                {/* Answer Records Section */}
                {activeSection === 'qa' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-medium text-gray-700">
                        问答记录 ({answerRecords.length})
                      </h3>
                      {answerRecords.length > 0 && (
                        <button
                          type="button"
                          onClick={handleSelectAllAnswerRecords}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          {selectedAnswerRecords.length === answerRecords.length ? '取消全选' : '全选'}
                        </button>
                      )}
                    </div>

                    {answerRecords.length === 0 ? (
                      <p className="text-gray-500 text-sm py-4">该知识库暂无问答记录</p>
                    ) : (
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {answerRecords.map((record) => (
                          <label key={record.id} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                            <input
                              type="checkbox"
                              checked={selectedAnswerRecords.includes(record.id)}
                              onChange={() => handleAnswerRecordToggle(record.id)}
                              className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 mb-1">
                                {record.question_text}
                              </p>
                              <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                                {record.user_answer}
                              </p>
                              <div className="flex items-center space-x-4 text-xs">
                                <span className={`px-2 py-1 rounded-full font-medium ${getScoreColor(record.score)}`}>
                                  {record.score.toFixed(1)}分
                                </span>
                                <span className="text-gray-500">
                                  {new Date(record.answered_at).toLocaleDateString()}
                                </span>
                                <span className="text-gray-500">
                                  {record.document_name}
                                </span>
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Knowledge Points Section */}
                {activeSection === 'kp' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-medium text-gray-700">
                        知识点 ({knowledgePoints.length})
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

                    {knowledgePoints.length === 0 ? (
                      <p className="text-gray-500 text-sm py-4">该知识库暂无知识点</p>
                    ) : (
                      <div className="space-y-3 max-h-96 overflow-y-auto">
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
              (selectedAnswerRecords.length === 0 && selectedKnowledgePoints.length === 0)
            }
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {exporting ? '导出中...' : `创建并下载 (${selectedAnswerRecords.length + selectedKnowledgePoints.length} 项)`}
          </button>
        </div>
      </form>
    </div>
  );
}