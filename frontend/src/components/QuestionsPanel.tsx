'use client'

export default function QuestionsPanel() {
  const questions = [
    {
      id: 1,
      agent: 'Research Supervisor',
      question: 'Should I prioritize recent sources (2024-2025) or include foundational research from earlier years?'
    },
    {
      id: 2,
      agent: 'Analysis Supervisor',
      question: 'The data shows conflicting trends. Should I flag this as an uncertainty or investigate further?'
    },
    {
      id: 3,
      agent: 'Global Supervisor',
      question: 'Quality threshold reached for research phase. Proceed to analysis phase?'
    }
  ]

  return (
    <div className="w-80 bg-sidebar-bg glass-effect shadow-custom p-6 border-l border-border">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-text">Agent Questions</h3>
      </div>

      <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
        {questions.map((q) => (
          <div
            key={q.id}
            className="bg-card-glass glass-effect p-4 rounded-xl border border-border"
          >
            <div className="text-xs text-accent font-medium mb-2">
              {q.agent}
            </div>
            <div className="text-sm text-text mb-3 leading-relaxed">
              {q.question}
            </div>
            <button className="bg-primary hover:bg-primary-light text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors">
              Reply
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}