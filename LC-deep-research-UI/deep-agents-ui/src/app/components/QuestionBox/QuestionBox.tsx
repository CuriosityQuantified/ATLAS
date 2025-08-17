"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, ChevronUp, Send } from "lucide-react";
import type { ToolCall } from "../../types/types";
import styles from "./QuestionBox.module.scss";

interface QuestionBoxProps {
  toolCall: ToolCall;
  sendMessage?: (message: string) => void;
}

export const QuestionBox: React.FC<QuestionBoxProps> = ({ toolCall, sendMessage }) => {
  const [answer, setAnswer] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const question = toolCall.args?.question || "";
  const context = toolCall.args?.context;

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      if (isExpanded) {
        textareaRef.current.style.height = `${Math.min(scrollHeight, 300)}px`;
      } else {
        textareaRef.current.style.height = `${Math.min(scrollHeight, 60)}px`;
      }
    }
  }, [answer, isExpanded]);

  const handleSubmitAnswer = () => {
    const trimmedAnswer = answer.trim();
    if (trimmedAnswer && sendMessage) {
      console.log(`Submitting answer for question "${question}": ${trimmedAnswer}`);
      // Send the answer as a regular message
      sendMessage(trimmedAnswer);
      setAnswer("");
      setIsExpanded(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmitAnswer();
    }
  };

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
    // Focus textarea when expanding
    if (!isExpanded && textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className={styles.questionBox}>
      <div className={styles.questionContent}>
        <div className={styles.questionHeader}>
          <div className={styles.questionText}>{question}</div>
          <button
            type="button"
            className={styles.expandButton}
            onClick={toggleExpanded}
            title={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
        {context && (
          <div className={styles.questionContext}>{context}</div>
        )}
        <div className={styles.inputWrapper}>
          <textarea
            ref={textareaRef}
            className={`${styles.questionInput} ${isExpanded ? styles.expanded : ''}`}
            placeholder="Type your answer (Enter to send, Shift+Enter for new line)..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            rows={isExpanded ? 5 : 1}
          />
          <button
            type="button"
            className={styles.sendButton}
            onClick={handleSubmitAnswer}
            disabled={!answer.trim()}
            title="Send answer"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};