'use client';

import React from 'react';
import { LearningSetList } from '@/components/learning-sets/LearningSetList';
import { useRouter } from 'next/navigation';
import { LearningSet } from '@/lib/api';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';

export default function LearningSetsPage() {
  const router = useRouter();

  const handleSelectLearningSet = (learningSet: LearningSet) => {
    router.push(`/learning-sets/${learningSet.id}`);
  };

  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="container mx-auto px-4 py-6">
          <LearningSetList onSelectLearningSet={handleSelectLearningSet} />
        </div>
      </MainLayout>
    </ProtectedRoute>
  );
}