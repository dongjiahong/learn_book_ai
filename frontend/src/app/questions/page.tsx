'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';
import { LearningSetList } from '@/components/learning-sets/LearningSetList';
import { LearningSet } from '@/lib/api';

function LearningSetManagementContent() {
  const handleSelectLearningSet = (learningSet: LearningSet) => {
    // TODO: 导航到学习集详情页面或学习界面
    console.log('Selected learning set:', learningSet);
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