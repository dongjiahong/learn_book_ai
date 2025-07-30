'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';
import { QuestionList } from '@/components/questions/QuestionList';
import { AnswerForm } from '@/components/questions/AnswerForm';
import { EvaluationResult } from '@/components/questions/EvaluationResult';
import { AnswerHistory } from '@/components/questions/AnswerHistory';
import { Question, AnswerEvaluationResponse, AnswerRecord } from '@/lib/api';

type ViewMode = 'list' | 'answer' | 'result' | 'history';

interface PracticeState {
  mode: ViewMode;
  selectedQuestion: Question | null;
  evaluationResult: AnswerEvaluationResponse | null;
  selectedRecord: AnswerRecord | null;
}

function PracticeContent() {
  const [state, setState] = useState<PracticeState>({
    mode: 'list',
    selectedQuestion: null,
    evaluationResult: null,
    selectedRecord: null
  });

  const handleSelectQuestion = (question: Question) => {
    setState({
      mode: 'answer',
      selectedQuestion: question,
      evaluationResult: null,
      selectedRecord: null
    });
  };

  const handleSubmitSuccess = (result: AnswerEvaluationResponse) => {
    setState(prev => ({
      ...prev,
      mode: 'result',
      evaluationResult: result
    }));
  };

  const handleRetry = () => {
    setState(prev => ({
      ...prev,
      mode: 'answer',
      evaluationResult: null
    }));
  };

  const handleViewHistory = () => {
    setState(prev => ({
      ...prev,
      mode: 'history'
    }));
  };

  const handleViewRecord = (record: AnswerRecord) => {
    setState(prev => ({
      ...prev,
      mode: 'history',
      selectedRecord: record
    }));
  };

  const handleBackToList = () => {
    setState({
      mode: 'list',
      selectedQuestion: null,
      evaluationResult: null,
      selectedRecord: null
    });
  };

  const handleBackToAnswer = () => {
    setState(prev => ({
      ...prev,
      mode: 'answer',
      evaluationResult: null
    }));
  };

  const renderContent = () => {
    switch (state.mode) {
      case 'list':
        return (
          <QuestionList 
            onSelectQuestion={handleSelectQuestion}
          />
        );

      case 'answer':
        return state.selectedQuestion ? (
          <AnswerForm
            question={state.selectedQuestion}
            onSubmitSuccess={handleSubmitSuccess}
            onBack={handleBackToList}
          />
        ) : null;

      case 'result':
        return state.selectedQuestion && state.evaluationResult ? (
          <EvaluationResult
            question={state.selectedQuestion}
            evaluationResult={state.evaluationResult}
            onRetry={handleRetry}
            onViewHistory={handleViewHistory}
            onBack={handleBackToAnswer}
          />
        ) : null;

      case 'history':
        return (
          <AnswerHistory
            questionId={state.selectedQuestion?.id}
            onViewRecord={handleViewRecord}
            onBack={handleBackToList}
          />
        );

      default:
        return null;
    }
  };

  return (
    <MainLayout>
      <div className="p-6">
        {renderContent()}
      </div>
    </MainLayout>
  );
}

export default function PracticePage() {
  return (
    <ProtectedRoute>
      <PracticeContent />
    </ProtectedRoute>
  );
}