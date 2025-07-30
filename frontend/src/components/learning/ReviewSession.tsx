'use client';

import React, { useState } from 'react';
import { Card, Button, Typography, Space, Progress, Rate, message, Divider, Tag, Alert } from 'antd';
import { ArrowLeftOutlined, BookOutlined, BulbOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { DueReviewItem } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

interface ReviewSessionProps {
  reviewItem: DueReviewItem;
  onComplete: (quality: number) => void;
  onExit: () => void;
  remainingCount: number;
}

const qualityDescriptions = {
  0: 'Complete blackout',
  1: 'Incorrect response; the correct one remembered',
  2: 'Incorrect response; where the correct one seemed easy to recall',
  3: 'Correct response recalled with serious difficulty',
  4: 'Correct response after a hesitation',
  5: 'Perfect response'
};

export default function ReviewSession({ reviewItem, onComplete, onExit, remainingCount }: ReviewSessionProps) {
  const [showAnswer, setShowAnswer] = useState(false);
  const [selectedQuality, setSelectedQuality] = useState<number | null>(null);

  const handleShowAnswer = () => {
    setShowAnswer(true);
  };

  const handleQualitySelect = (quality: number) => {
    setSelectedQuality(quality);
  };

  const handleComplete = () => {
    if (selectedQuality !== null) {
      onComplete(selectedQuality);
      // Reset for next review
      setShowAnswer(false);
      setSelectedQuality(null);
    } else {
      message.warning('Please rate your recall quality');
    }
  };

  const isQuestion = reviewItem.content_type === 'question';
  const progressPercent = Math.round(((remainingCount - remainingCount + 1) / remainingCount) * 100);

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={onExit}>
            Exit Review
          </Button>
          <div>
            <Text type="secondary">Review Session</Text>
            <br />
            <Text strong>{remainingCount} items remaining</Text>
          </div>
        </Space>
        <Progress 
          percent={progressPercent} 
          style={{ marginTop: '16px' }}
          strokeColor="#52c41a"
        />
      </div>

      {/* Review Content */}
      <Card>
        <div style={{ marginBottom: '16px' }}>
          <Space>
            {isQuestion ? <BookOutlined /> : <BulbOutlined />}
            <Tag color={isQuestion ? 'blue' : 'green'}>
              {isQuestion ? 'Question' : 'Knowledge Point'}
            </Tag>
            {reviewItem.difficulty_level && (
              <Tag color="orange">
                Difficulty: {reviewItem.difficulty_level}
              </Tag>
            )}
            {reviewItem.importance_level && (
              <Tag color="purple">
                Importance: {reviewItem.importance_level}
              </Tag>
            )}
          </Space>
        </div>

        {/* Question/Knowledge Point Content */}
        <div style={{ marginBottom: '24px' }}>
          {isQuestion ? (
            <div>
              <Title level={4}>Question:</Title>
              <Paragraph style={{ fontSize: '16px', lineHeight: '1.6' }}>
                {reviewItem.question_text}
              </Paragraph>
              {reviewItem.context && (
                <div>
                  <Text type="secondary" strong>Context:</Text>
                  <Paragraph type="secondary" style={{ marginTop: '8px' }}>
                    {reviewItem.context}
                  </Paragraph>
                </div>
              )}
            </div>
          ) : (
            <div>
              <Title level={4}>{reviewItem.title}</Title>
              <Paragraph style={{ fontSize: '16px', lineHeight: '1.6' }}>
                {reviewItem.content}
              </Paragraph>
            </div>
          )}
        </div>

        {/* Review Info */}
        <Alert
          message="Review Information"
          description={
            <div>
              <Text>Review count: {reviewItem.review_count}</Text>
              <br />
              <Text>Current interval: {reviewItem.interval_days} days</Text>
              <br />
              <Text>Ease factor: {reviewItem.ease_factor.toFixed(2)}</Text>
            </div>
          }
          type="info"
          style={{ marginBottom: '24px' }}
        />

        {!showAnswer ? (
          <div style={{ textAlign: 'center' }}>
            <Paragraph type="secondary" style={{ marginBottom: '24px' }}>
              {isQuestion 
                ? 'Think about your answer, then click "Show Answer" to continue.'
                : 'Review this knowledge point carefully, then click "Continue" when ready.'
              }
            </Paragraph>
            <Button type="primary" size="large" onClick={handleShowAnswer}>
              {isQuestion ? 'Show Answer' : 'Continue'}
            </Button>
          </div>
        ) : (
          <div>
            <Divider />
            
            {/* Quality Rating */}
            <div style={{ marginBottom: '24px' }}>
              <Title level={5}>Rate your recall quality:</Title>
              <div style={{ marginBottom: '16px' }}>
                <Rate 
                  count={6}
                  value={selectedQuality !== null ? selectedQuality : undefined}
                  onChange={handleQualitySelect}
                  style={{ fontSize: '24px' }}
                />
              </div>
              
              {selectedQuality !== null && (
                <Alert
                  message={`Quality ${selectedQuality}: ${qualityDescriptions[selectedQuality as keyof typeof qualityDescriptions]}`}
                  type="info"
                  style={{ marginBottom: '16px' }}
                />
              )}

              <div style={{ fontSize: '12px', color: '#666' }}>
                <div><strong>0:</strong> Complete blackout</div>
                <div><strong>1:</strong> Incorrect response; the correct one remembered</div>
                <div><strong>2:</strong> Incorrect response; where the correct one seemed easy to recall</div>
                <div><strong>3:</strong> Correct response recalled with serious difficulty</div>
                <div><strong>4:</strong> Correct response after a hesitation</div>
                <div><strong>5:</strong> Perfect response</div>
              </div>
            </div>

            <div style={{ textAlign: 'center' }}>
              <Button 
                type="primary" 
                size="large" 
                icon={<CheckCircleOutlined />}
                onClick={handleComplete}
                disabled={selectedQuality === null}
              >
                Complete Review
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}