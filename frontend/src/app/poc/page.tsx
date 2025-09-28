'use client';

import { useState } from 'react';
import { useCopilotAction, useCopilotChat } from '@copilotkit/react-core';

export default function POCPage() {
  const [taskResult, setTaskResult] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Register a CopilotKit action for task execution
  useCopilotAction({
    name: "execute_task",
    description: "Execute a complex task using the ATLAS agent hierarchy",
    parameters: [
      {
        name: "query",
        type: "string",
        description: "The task or question to analyze",
        required: true,
      },
    ],
    handler: async ({ query }) => {
      setIsProcessing(true);
      setTaskResult(null);

      try {
        const response = await fetch('/api/copilotkit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Task-ID': `task_${Date.now()}`,
          },
          body: JSON.stringify({
            action: 'execute_task',
            parameters: { query },
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Handle streaming response
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.type === 'result') {
                    setTaskResult(data.data);
                  }
                } catch (e) {
                  // Ignore parsing errors for incomplete chunks
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('Error executing task:', error);
        setTaskResult({ error: 'Failed to execute task' });
      } finally {
        setIsProcessing(false);
      }

      return "Task execution initiated. Results will appear below.";
    },
  });

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-blue-400">
          ATLAS POC - Multi-Agent Task Execution
        </h1>

        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">How to Use:</h2>
          <ol className="list-decimal list-inside space-y-2">
            <li>Open the CopilotKit sidebar (button in bottom-right)</li>
            <li>Type a complex task or question</li>
            <li>The system will decompose it and coordinate agents</li>
            <li>Results will appear below</li>
          </ol>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Agent Hierarchy:</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="font-bold text-blue-400">Supervisor</h3>
              <p className="text-sm">Coordinates all agents</p>
            </div>
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="font-bold text-green-400">Research</h3>
              <p className="text-sm">Gathers information</p>
            </div>
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="font-bold text-yellow-400">Analysis</h3>
              <p className="text-sm">Interprets data</p>
            </div>
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="font-bold text-purple-400">Writing</h3>
              <p className="text-sm">Generates content</p>
            </div>
          </div>
        </div>

        {isProcessing && (
          <div className="bg-blue-900 rounded-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Processing...</h2>
            <div className="animate-pulse">
              <div className="h-2 bg-blue-400 rounded"></div>
            </div>
          </div>
        )}

        {taskResult && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Results:</h2>
            <pre className="bg-gray-900 p-4 rounded overflow-x-auto">
              {JSON.stringify(taskResult, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}