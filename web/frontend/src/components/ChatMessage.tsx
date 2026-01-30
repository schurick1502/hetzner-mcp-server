interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  toolCalls?: string[]
}

export default function ChatMessage({ role, content, toolCalls }: ChatMessageProps) {
  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg p-4 ${
          role === 'user'
            ? 'bg-hetzner-red text-white'
            : 'bg-gray-100 text-gray-900'
        }`}
      >
        <div className="whitespace-pre-wrap">{content}</div>
        {toolCalls && toolCalls.length > 0 && (
          <div className="mt-2 text-sm opacity-75 flex flex-wrap gap-1">
            <span>🔧 Tools:</span>
            {toolCalls.map((tool, idx) => (
              <span key={idx} className="bg-black/10 px-2 py-0.5 rounded">
                {tool}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
