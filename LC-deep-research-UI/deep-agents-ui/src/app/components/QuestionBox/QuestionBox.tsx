"use client";

import React, { useState } from "react";
import type { ToolCall } from "../../types/types";
import styles from "./QuestionBox.module.scss";

interface QuestionBoxProps {
  toolCall: ToolCall;
  onSubmitAnswer?: (toolCallId: string, answer: string) => void;
}

export const QuestionBox: React.FC<QuestionBoxProps> = ({ toolCall, onSubmitAnswer }) => {
  const [answer, setAnswer] = useState("");
  
  // Debug logging to see what we're receiving
  console.log('QuestionBox toolCall:', toolCall);
  console.log('QuestionBox args:', toolCall.args);
  
  const question = toolCall.args?.question || "";
  const context = toolCall.args?.context;

  const handleSubmitAnswer = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && answer.trim()) {
      // TODO: Submit answer back to the agent
      console.log(`Answering question ${toolCall.id}: ${answer}`);
      if (onSubmitAnswer) {
        onSubmitAnswer(toolCall.id, answer);
      }
      // This would need to be connected to the backend
      setAnswer("");
    }
  };

  return (
    <div className={styles.questionBox}>
      <div className={styles.questionContent}>
        <div className={styles.questionText}>{question}</div>
        {context && (
          <div className={styles.questionContext}>{context}</div>
        )}
      </div>
      <input
        type="text"
        className={styles.questionInput}
        placeholder="Type your answer and press Enter..."
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        onKeyPress={handleSubmitAnswer}
        autoFocus
      />
    </div>
  );
};