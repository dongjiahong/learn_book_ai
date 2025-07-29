'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
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
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
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
    </div>
  );
}

export default function QuestionsPage() {
  return (
    <ProtectedRoute>
      <QuestionsContent />
    </ProtectedRoute>
  );
}