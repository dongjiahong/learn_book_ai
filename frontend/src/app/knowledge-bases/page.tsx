'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { KnowledgeBaseList } from '@/components/knowledge-base/KnowledgeBaseList';
import { DocumentList } from '@/components/documents/DocumentList';
import { KnowledgeBase } from '@/lib/api';

function KnowledgeBasesContent() {
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBase | null>(null);

  const handleSelectKnowledgeBase = (kb: KnowledgeBase) => {
    setSelectedKnowledgeBase(kb);
  };

  const handleBackToList = () => {
    setSelectedKnowledgeBase(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {selectedKnowledgeBase ? (
          <DocumentList
            knowledgeBase={selectedKnowledgeBase}
            onBack={handleBackToList}
          />
        ) : (
          <KnowledgeBaseList onSelectKnowledgeBase={handleSelectKnowledgeBase} />
        )}
      </div>
    </div>
  );
}

export default function KnowledgeBasesPage() {
  return (
    <ProtectedRoute>
      <KnowledgeBasesContent />
    </ProtectedRoute>
  );
}