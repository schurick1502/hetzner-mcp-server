import { useState, useCallback } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  toolCalls?: string[]
}

export function useAiChat(provider: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = useCallback((content: string) => {
    const newMessage: Message = { role: 'user', content }
    const allMessages = [...messages, newMessage]
    setMessages(allMessages)
    setIsStreaming(true)

    // Neue SSE-Verbindung via fetch
    const url = `/api/ai/chat`

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider,
        messages: allMessages
      })
    }).then(async response => {
      const reader = response.body?.getReader()
      if (!reader) return

      let assistantMessage = ''
      const toolCalls: string[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = new TextDecoder().decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === 'text') {
                assistantMessage += data.text
                setMessages(prev => {
                  const newMessages = [...prev]
                  const lastMsg = newMessages[newMessages.length - 1]
                  if (lastMsg?.role === 'assistant') {
                    lastMsg.content = assistantMessage
                    lastMsg.toolCalls = toolCalls.length > 0 ? toolCalls : undefined
                  } else {
                    newMessages.push({
                      role: 'assistant',
                      content: assistantMessage,
                      toolCalls: toolCalls.length > 0 ? toolCalls : undefined
                    })
                  }
                  return newMessages
                })
              } else if (data.type === 'tool_use' || data.type === 'tool_executing') {
                if (data.tool && !toolCalls.includes(data.tool)) {
                  toolCalls.push(data.tool)
                }
              } else if (data.type === 'done') {
                setIsStreaming(false)
              } else if (data.type === 'error') {
                console.error('AI Error:', data.error)
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: `Fehler: ${data.error}`
                }])
                setIsStreaming(false)
              }
            } catch (e) {
              // Ignore JSON parse errors
            }
          }
        }
      }

      setIsStreaming(false)
    }).catch(error => {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Verbindungsfehler: ${error.message}`
      }])
      setIsStreaming(false)
    })
  }, [messages, provider])

  return { messages, sendMessage, isStreaming }
}
