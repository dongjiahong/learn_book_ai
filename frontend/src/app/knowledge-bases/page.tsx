'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';
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
    <MainLayout>
      <div className="p-6">
        {selectedKnowledgeBase ? (
          <DocumentList
            knowledgeBase={selectedKnowledgeBase}
            onBack={handleBackToList}
          />
        ) : (
          <KnowledgeBaseList onSelectKnowledgeBase={handleSelectKnowledgeBase} />
        )}
      </div>
    </MainLayout>
  );
}

export default function KnowledgeBasesPage() {
  return (
    <ProtectedRoute>
      <KnowledgeBasesContent />
    </ProtectedRoute>
  );
}