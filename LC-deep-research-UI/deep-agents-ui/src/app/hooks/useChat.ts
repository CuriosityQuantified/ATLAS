import { useCallback, useMemo, useRef, useState, useEffect } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import { type Message } from "@langchain/langgraph-sdk";
import { getDeployment } from "@/lib/environment/deployments";
import { v4 as uuidv4 } from "uuid";
import type { TodoItem } from "../types/types";
import { createClient } from "@/lib/client";
import { useAuthContext } from "@/providers/Auth";

type StateType = {
  messages: Message[];
  todos: TodoItem[];
  files: Record<string, string>;
};

export function useChat(
  threadId: string | null,
  setThreadId: (
    value: string | ((old: string | null) => string | null) | null,
  ) => void,
  onTodosUpdate: (todos: TodoItem[]) => void,
  onFilesUpdate: (files: Record<string, string>) => void,
) {
  const deployment = useMemo(() => getDeployment(), []);
  const { session } = useAuthContext();
  const accessToken = session?.accessToken;
  
  // State for interrupt handling
  const [currentInterrupt, setCurrentInterrupt] = useState<any>(null);

  const agentId = useMemo(() => {
    if (!deployment?.agentId) {
      throw new Error(`No agent ID configured in environment`);
    }
    return deployment.agentId;
  }, [deployment]);

  const handleUpdateEvent = useCallback(
    (data: { [node: string]: Partial<StateType> }) => {
      Object.entries(data).forEach(([_, nodeData]) => {
        if (nodeData?.todos) {
          // Ensure todos is always an array
          const todos = Array.isArray(nodeData.todos) ? nodeData.todos : [];
          onTodosUpdate(todos);
        }
        if (nodeData?.files) {
          // Ensure files is always an object
          const files = nodeData.files && typeof nodeData.files === 'object' && !Array.isArray(nodeData.files) 
            ? nodeData.files 
            : {};
          onFilesUpdate(files);
        }
      });
    },
    [onTodosUpdate, onFilesUpdate],
  );

  const stream = useStream<StateType>({
    assistantId: agentId,
    client: createClient(accessToken || ""),
    reconnectOnMount: true,
    threadId: threadId ?? null,
    onUpdateEvent: handleUpdateEvent,
    onThreadId: setThreadId,
    defaultHeaders: {
      "x-auth-scheme": "langsmith",
    },
  });

  const sendMessage = useCallback(
    (message: string) => {
      const humanMessage: Message = {
        id: uuidv4(),
        type: "human",
        content: message,
      };
      stream.submit(
        { messages: [humanMessage] },
        {
          optimisticValues(prev) {
            const prevMessages = prev.messages ?? [];
            const newMessages = [...prevMessages, humanMessage];
            return { ...prev, messages: newMessages };
          },
          config: {
            recursion_limit: 100,
          },
        },
      );
    },
    [stream],
  );

  const stopStream = useCallback(() => {
    stream.stop();
  }, [stream]);
  
  // Monitor for interrupt states in stream
  useEffect(() => {
    if (stream.messages && stream.messages.length > 0) {
      // Check if the last message indicates an interrupt
      const lastMessage = stream.messages[stream.messages.length - 1];
      
      // Check for interrupt in message metadata or special interrupt field
      if ((lastMessage as any)?.interrupt) {
        setCurrentInterrupt((lastMessage as any).interrupt);
      } else if (lastMessage?.additional_kwargs?.interrupt) {
        setCurrentInterrupt(lastMessage.additional_kwargs.interrupt);
      }
    }
  }, [stream.messages]);

  // Resume function for answering interrupts (Phase 2)
  const resumeWithAnswer = useCallback(
    (answer: string) => {
      if (!threadId) {
        console.error("Cannot resume: no thread ID");
        return;
      }
      
      // Send resume command to backend for interrupt pattern
      stream.submit(
        { 
          command: { 
            resume: answer,
          } 
        },
        {
          config: {
            thread_id: threadId,
            recursion_limit: 100,
          },
        },
      );
      
      // Clear interrupt state
      setCurrentInterrupt(null);
    },
    [stream, threadId]
  );

  const sendQuestionResponse = useCallback(
    (message: string, metadata?: { question_tool_call_id?: string }) => {
      // Check if we're using interrupt pattern
      const useInterruptPattern = process.env.NEXT_PUBLIC_USE_INTERRUPT_PATTERN === 'true';
      
      if (useInterruptPattern && currentInterrupt) {
        // Use resume for interrupt pattern
        resumeWithAnswer(message);
        return;
      }
      
      // Original implementation for backward compatibility
      const humanMessage: Message = {
        id: uuidv4(),
        type: "human",
        content: message,
        additional_kwargs: {
          is_question_response: true,
          ...metadata,
        },
      };
      stream.submit(
        { messages: [humanMessage] },
        {
          optimisticValues(prev) {
            const prevMessages = prev.messages ?? [];
            // Add the answer message optimistically to prevent flickering
            const updatedMessages = [...prevMessages, humanMessage];
            
            // Return updated state with the new message
            // This provides immediate feedback to the user
            return { 
              ...prev, 
              messages: updatedMessages 
            };
          },
          config: {
            recursion_limit: 100,
          },
        },
      );
    },
    [stream, currentInterrupt, resumeWithAnswer],
  );

  return {
    messages: stream.messages,
    isLoading: stream.isLoading,
    sendMessage,
    sendQuestionResponse,
    stopStream,
    currentInterrupt,  // Expose interrupt state
    resumeWithAnswer,  // Expose resume function
  };
}
