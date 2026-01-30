import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bot } from 'lucide-react'
import { aiApi } from '../services/api'
import { useAiChat } from '../hooks/useAiChat'
import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'

export default function AiAssistantPage() {
  const [provider, setProvider] = useState('claude')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: providersData } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: aiApi.listProviders,
  })

  const { messages, sendMessage, isStreaming } = useAiChat(provider)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const providers = providersData?.data?.providers || []
  const availableProviders = providers.filter((p: any) => p.available)

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Bot size={32} className="text-hetzner-red" />
          <h1 className="text-3xl font-bold">AI Assistant</h1>
        </div>

        <div className="flex items-center gap-4">
          {availableProviders.length === 0 && (
            <div className="text-sm text-yellow-600 bg-yellow-50 px-4 py-2 rounded">
              ⚠ Keine AI-Provider konfiguriert. Bitte API-Keys in .env setzen.
            </div>
          )}
          {availableProviders.length > 0 && (
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="input"
            >
              {availableProviders.map((p: any) => (
                <option key={p.name} value={p.name}>
                  {p.name.charAt(0).toUpperCase() + p.name.slice(1)}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      <div className="card flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto mb-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-12">
              <Bot size={64} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg mb-2">Stelle eine Frage über deine Hetzner Cloud Infrastruktur</p>
              <p className="text-sm text-gray-400">
                Der AI-Assistent kann alle 117 MCP-Tools nutzen, um dir zu helfen
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <ChatMessage
                key={idx}
                role={msg.role}
                content={msg.content}
                toolCalls={msg.toolCalls}
              />
            ))
          )}
          {isStreaming && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 rounded-lg p-4">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <ChatInput
          onSend={sendMessage}
          disabled={isStreaming || availableProviders.length === 0}
        />
      </div>
    </div>
  )
}
