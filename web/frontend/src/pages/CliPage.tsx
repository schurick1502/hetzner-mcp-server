import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { cliApi } from '../services/api'
import { Play, Loader2 } from 'lucide-react'

export default function CliPage() {
  const [command, setCommand] = useState('')
  const [output, setOutput] = useState<string[]>([
    '╔═══════════════════════════════════════╗',
    '║     Hetzner Cloud CLI Terminal        ║',
    '╚═══════════════════════════════════════╝',
    '',
    'Gib einen Befehl ein oder klicke auf einen Befehl rechts.',
    ''
  ])
  const [isLoading, setIsLoading] = useState(false)
  const outputRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data: toolsData } = useQuery({
    queryKey: ['cli-tools'],
    queryFn: cliApi.listTools,
  })

  // Auto-scroll to bottom
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [output])

  const executeCommand = async (cmd: string) => {
    if (!cmd.trim() || isLoading) return

    const trimmedCmd = cmd.trim()
    setOutput(prev => [...prev, `$ ${trimmedCmd}`, 'Executing...'])
    setIsLoading(true)
    setCommand('')

    try {
      // Parse command and arguments
      const parts = trimmedCmd.split(/\s+/)
      const commandName = parts[0]
      const args: Record<string, any> = {}

      for (let i = 1; i < parts.length; i++) {
        const part = parts[i]
        if (part.includes('=')) {
          const [key, ...valueParts] = part.split('=')
          args[key] = valueParts.join('=')
        } else if (i === 1) {
          args['identifier'] = part
        }
      }

      const response = await cliApi.execute(commandName, args)
      const data = response.data

      if (data.success) {
        const formatted = JSON.stringify(data.output, null, 2).split('\n')
        setOutput(prev => [
          ...prev.slice(0, -1), // Remove "Executing..."
          '✓ Success',
          ...formatted,
          `(${data.execution_time_ms}ms)`,
          ''
        ])
      } else {
        setOutput(prev => [
          ...prev.slice(0, -1),
          `✗ Error: ${data.error}`,
          ''
        ])
      }
    } catch (error: any) {
      setOutput(prev => [
        ...prev.slice(0, -1),
        `✗ Error: ${error.message || String(error)}`,
        ''
      ])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      executeCommand(command)
    }
  }

  const tools = toolsData?.data?.tools || []

  return (
    <div className="grid grid-cols-4 gap-6 h-[calc(100vh-8rem)]">
      {/* Terminal */}
      <div className="col-span-3">
        <div className="card h-full flex flex-col">
          <h1 className="text-2xl font-bold mb-4">CLI Terminal</h1>

          {/* Output */}
          <div
            ref={outputRef}
            className="flex-1 bg-gray-900 text-green-400 font-mono text-sm p-4 rounded-t-lg overflow-auto"
            style={{ minHeight: '400px' }}
          >
            {output.map((line, i) => (
              <div key={i} className={
                line.startsWith('✓') ? 'text-green-500' :
                line.startsWith('✗') ? 'text-red-500' :
                line.startsWith('$') ? 'text-blue-400' :
                line.startsWith('Executing') ? 'text-gray-500' :
                'text-gray-300'
              }>
                {line || '\u00A0'}
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="flex bg-gray-800 rounded-b-lg p-2">
            <span className="text-green-400 font-mono px-2 py-2">$</span>
            <input
              ref={inputRef}
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Befehl eingeben (z.B. server_list)"
              className="flex-1 bg-transparent text-white font-mono outline-none px-2"
              disabled={isLoading}
              autoFocus
            />
            <button
              onClick={() => executeCommand(command)}
              disabled={isLoading || !command.trim()}
              className="px-4 py-2 bg-hetzner-red text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
              Run
            </button>
          </div>
        </div>
      </div>

      {/* Commands Sidebar */}
      <div className="card overflow-y-auto">
        <h2 className="text-lg font-semibold mb-4">
          Commands ({tools.length})
        </h2>
        {tools.length === 0 && (
          <div className="text-sm text-gray-500 mb-4">
            Loading commands...
          </div>
        )}
        <div className="mb-4 text-xs text-gray-600 bg-blue-50 p-2 rounded">
          Klicke auf einen Befehl um ihn auszuführen
        </div>
        <div className="space-y-2">
          {tools.map((tool: any) => {
            const hasParams = tool.parameters?.some((p: any) => p.required)

            return (
              <button
                key={tool.name}
                onClick={() => {
                  if (hasParams) {
                    // Nur einfügen wenn Parameter benötigt
                    setCommand(tool.name + ' ')
                    inputRef.current?.focus()
                  } else {
                    // Direkt ausführen
                    executeCommand(tool.name)
                  }
                }}
                disabled={isLoading}
                className="w-full text-left p-3 hover:bg-gray-50 rounded border border-gray-200 transition-colors disabled:opacity-50"
              >
                <div className="font-mono text-sm text-hetzner-red font-bold">
                  {tool.name}
                  {hasParams && <span className="text-gray-400 ml-1">...</span>}
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  {tool.description}
                </div>
                {tool.parameters?.length > 0 && (
                  <div className="text-xs text-gray-400 mt-1">
                    {tool.parameters.filter((p: any) => p.required).map((p: any) => p.name).join(', ')}
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
