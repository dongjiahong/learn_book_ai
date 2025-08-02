'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';
import { LearningSetList } from '@/components/learning-sets/LearningSetList';
import { LearningSet } from '@/lib/api';

function LearningSetManagementContent() {
  const router = useRouter();

  const handleSelectLearningSet = (learningSet: LearningSet) => {
    console.log('Selected learning set:', learningSet);
    // 导航到学习集详情页面
    router.push(`/learning-sets/${learningSet.id}`);
  };

  return (
    <MainLayout>
      <div className="p-6">
        <LearningSetList onSelectLearningSet={handleSelectLearningSet} />
      </div>
    </MainLayout>
  );
}

export default function LearningSetManagementPage() {
  return (
    <ProtectedRoute>
      <LearningSetManagementContent />
    </ProtectedRoute>
  );
}