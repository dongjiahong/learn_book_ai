'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';
import { QuestionList } from '@/components/questions/QuestionList';
import { QuestionDetail } from '@/components/questions/QuestionDetail';
import { Question } from '@/lib/api';

function QuestionsContent() {
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);

  const handleSelectQuestion = (question: Question) => {
    setSelectedQuestion(question);
  };

  const handleBackToList = () => {
    setSelectedQuestion(null);
  };

  return (
    <MainLayout>
      <div className="p-6">
        {selectedQuestion ? (
          <QuestionDetail
            question={selectedQuestion}
            onBack={handleBackToList}
            onUpdate={setSelectedQuestion}
          />
        ) : (
          <QuestionList onSelectQuestion={handleSelectQuestion} />
        )}
      </div>
    </MainLayout>
  );
}

export default function QuestionsPage() {
  return (
    <ProtectedRoute>
      <QuestionsContent />
    </ProtectedRoute>
  );
}