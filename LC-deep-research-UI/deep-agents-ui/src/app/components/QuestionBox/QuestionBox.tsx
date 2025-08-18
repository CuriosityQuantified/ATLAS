"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, ChevronUp, Send, Edit2, Check } from "lucide-react";
import type { ToolCall } from "../../types/types";
import styles from "./QuestionBox.module.scss";

interface QuestionBoxProps {
  toolCall: ToolCall;
  sendMessage?: (message: string) => void;
  sendQuestionResponse?: (message: string, metadata?: { question_tool_call_id?: string }) => void;
}

export const QuestionBox: React.FC<QuestionBoxProps> = ({ toolCall, sendMessage, sendQuestionResponse }) => {
  // Helper function to detect if a message is just a question acknowledgment
  const isQuestionAcknowledgment = (message: string | undefined): boolean => {
    if (!message) return true;
    
    // Detect various forms of question echoes and acknowledgments
    return (
      message.startsWith("Question:") || 
      message.startsWith("Waiting for user response") ||
      message === toolCall.args?.question ||
      message.includes("Waiting for user response to:") ||
      // Also check if it's exactly the question wrapped in a standard format
      message === `Question: ${toolCall.args?.question}`
    );
  };
  
  // Derive initial state from toolCall to persist across re-renders
  // Only consider it answered if we have a real answer, not just an acknowledgment
  const hasRealAnswer = toolCall.status === "completed" && 
                       toolCall.result && 
                       !isQuestionAcknowledgment(toolCall.result);
  const existingAnswer = hasRealAnswer ? (toolCall.result || "") : "";
  
  const [answer, setAnswer] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const [isAnswered, setIsAnswered] = useState(hasRealAnswer);
  const [submittedAnswer, setSubmittedAnswer] = useState(existingAnswer);
  const [isEditing, setIsEditing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const question = toolCall.args?.question || "";
  const context = toolCall.args?.context;

  // Sync state with toolCall changes to handle external updates
  useEffect(() => {
    // Only update if we have a real answer, not just an acknowledgment
    if (toolCall.status === "completed" && toolCall.result && !isAnswered) {
      if (!isQuestionAcknowledgment(toolCall.result)) {
        setIsAnswered(true);
        setSubmittedAnswer(toolCall.result);
      }
    }
  }, [toolCall.status, toolCall.result, isAnswered]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current && !isAnswered) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      if (isExpanded) {
        textareaRef.current.style.height = `${Math.min(scrollHeight, 300)}px`;
      } else {
        textareaRef.current.style.height = `${Math.min(scrollHeight, 60)}px`;
      }
    }
  }, [answer, isExpanded, isAnswered]);

  const handleSubmitAnswer = () => {
    const trimmedAnswer = answer.trim();
    if (trimmedAnswer) {
      console.log(`Submitting answer for question "${question}": ${trimmedAnswer}`);
      // Use sendQuestionResponse if available, otherwise fall back to sendMessage
      if (sendQuestionResponse) {
        // Send as question response with metadata
        sendQuestionResponse(trimmedAnswer, { question_tool_call_id: toolCall.id });
      } else if (sendMessage) {
        // Fallback to regular message
        sendMessage(trimmedAnswer);
      }
      setSubmittedAnswer(trimmedAnswer);
      setIsAnswered(true);
      setAnswer("");
      setIsExpanded(false);
      setIsEditing(false);
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
    if (!isAnswered) {
      setIsExpanded(!isExpanded);
      // Focus textarea when expanding
      if (!isExpanded && textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setIsAnswered(false);
    setAnswer(submittedAnswer);
    setIsExpanded(false);
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
        textareaRef.current.select();
      }
    }, 0);
  };

  return (
    <div className={`${styles.questionBox} ${isAnswered ? styles.answered : ''}`}>
      <div className={styles.questionContent}>
        <div className={styles.questionHeader}>
          <div className={styles.questionText}>
            {isAnswered && <Check className={styles.checkIcon} size={16} />}
            {question}
          </div>
          {!isAnswered && (
            <button
              type="button"
              className={styles.expandButton}
              onClick={toggleExpanded}
              title={isExpanded ? "Collapse" : "Expand"}
            >
              {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          )}
          {isAnswered && (
            <button
              type="button"
              className={styles.editButton}
              onClick={handleEdit}
              title="Edit answer"
            >
              <Edit2 size={14} />
            </button>
          )}
        </div>
        {context && (
          <div className={styles.questionContext}>{context}</div>
        )}
        
        {isAnswered && !isEditing ? (
          <div className={styles.answeredWrapper}>
            <div className={styles.answeredLabel}>Your answer:</div>
            <div className={styles.answeredText}>{submittedAnswer}</div>
          </div>
        ) : (
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
        )}
      </div>
    </div>
  );
};