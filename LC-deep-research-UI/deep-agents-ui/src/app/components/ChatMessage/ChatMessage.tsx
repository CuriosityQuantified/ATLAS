"use client";

import React, { useEffect, useMemo } from "react";
import { User, Bot } from "lucide-react";
import { SubAgentIndicator } from "../SubAgentIndicator/SubAgentIndicator";
import { ToolCallBox } from "../ToolCallBox/ToolCallBox";
import { MarkdownContent } from "../MarkdownContent/MarkdownContent";
import type { SubAgent, ToolCall } from "../../types/types";
import styles from "./ChatMessage.module.scss";
import { Message } from "@langchain/langgraph-sdk";
import { extractStringFromMessageContent } from "../../utils/utils";

interface ChatMessageProps {
  message: Message;
  toolCalls: ToolCall[];
  showAvatar: boolean;
  onSelectSubAgent: (subAgent: SubAgent) => void;
  selectedSubAgent: SubAgent | null;
}

export const ChatMessage = React.memo<ChatMessageProps>(
  ({ message, toolCalls, showAvatar, onSelectSubAgent, selectedSubAgent }) => {
    const isUser = message.type === "human";
    const messageContent = extractStringFromMessageContent(message);
    const hasContent = messageContent && messageContent.trim() !== "";
    
    // Separate respond_to_user tool calls from other tool calls
    const userResponseCalls = toolCalls.filter((toolCall: ToolCall) => toolCall.name === "respond_to_user");
    const otherToolCalls = toolCalls.filter((toolCall: ToolCall) => toolCall.name !== "respond_to_user");
    const hasToolCalls = otherToolCalls.length > 0;
    const subAgents = useMemo(() => {
      return otherToolCalls
        .filter((toolCall: ToolCall) => {
          return (
            toolCall.name === "task" &&
            toolCall.args["subagent_type"] &&
            toolCall.args["subagent_type"] !== "" &&
            toolCall.args["subagent_type"] !== null
          );
        })
        .map((toolCall: ToolCall) => {
          return {
            id: toolCall.id,
            name: toolCall.name,
            subAgentName: toolCall.args["subagent_type"],
            input: toolCall.args["description"],
            output: toolCall.result,
            status: toolCall.status,
          };
        });
    }, [otherToolCalls]);

    const subAgentsString = useMemo(() => {
      return JSON.stringify(subAgents);
    }, [subAgents]);

    useEffect(() => {
      if (
        subAgents.some(
          (subAgent: SubAgent) => subAgent.id === selectedSubAgent?.id,
        )
      ) {
        onSelectSubAgent(
          subAgents.find(
            (subAgent: SubAgent) => subAgent.id === selectedSubAgent?.id,
          )!,
        );
      }
    }, [selectedSubAgent, onSelectSubAgent, subAgentsString]);

    return (
      <div
        className={`${styles.message} ${isUser ? styles.user : styles.assistant}`}
      >
        <div
          className={`${styles.avatar} ${!showAvatar ? styles.avatarHidden : ""}`}
        >
          {showAvatar &&
            (isUser ? (
              <User className={styles.avatarIcon} />
            ) : (
              <Bot className={styles.avatarIcon} />
            ))}
        </div>
        <div className={styles.content}>
          {hasContent && (
            <div className={styles.bubble}>
              {isUser ? (
                <p className={styles.text}>{messageContent}</p>
              ) : (
                <MarkdownContent content={messageContent} />
              )}
            </div>
          )}
          {/* Display user responses prominently */}
          {userResponseCalls.length > 0 && (
            <div className={styles.userResponses}>
              {userResponseCalls.map((toolCall: ToolCall) => {
                const responseMessage = toolCall.args?.message || toolCall.result || "";
                const status = toolCall.args?.status;
                return (
                  <div key={toolCall.id} className={styles.userResponse}>
                    <div className={styles.responseContent}>
                      {responseMessage}
                      {status && (
                        <span className={`${styles.status} ${styles[status]}`}>
                          {status}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          {hasToolCalls && (
            <div className={styles.toolCalls}>
              {otherToolCalls.map((toolCall: ToolCall) => {
                if (toolCall.name === "task") return null;
                return <ToolCallBox key={toolCall.id} toolCall={toolCall} />;
              })}
            </div>
          )}
          {!isUser && subAgents.length > 0 && (
            <div className={styles.subAgents}>
              {subAgents.map((subAgent: SubAgent) => (
                <SubAgentIndicator
                  key={subAgent.id}
                  subAgent={subAgent}
                  onClick={() => onSelectSubAgent(subAgent)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    );
  },
);

ChatMessage.displayName = "ChatMessage";
