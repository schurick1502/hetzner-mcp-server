import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import { cliApi } from '../services/api'
import { useCommandHistory } from '../hooks/useCommandHistory'

export default function CliPage() {
  const terminalRef = useRef<HTMLDivElement>(null)
  const [terminal, setTerminal] = useState<Terminal | null>(null)
  const { addToHistory, navigateHistory } = useCommandHistory()

  const { data: toolsData } = useQuery({
    queryKey: ['cli-tools'],
    queryFn: cliApi.listTools,
  })

  const executeMutation = useMutation({
    mutationFn: ({ command, args }: { command: string; args: any }) =>
      cliApi.execute(command, args),
    onSuccess: (data) => {
      if (terminal) {
        terminal.writeln('')
        if (data.success) {
          terminal.writeln('\x1b[32m✓ Success\x1b[0m')
          terminal.writeln(JSON.stringify(data.output, null, 2))
        } else {
          terminal.writeln('\x1b[31m✗ Error: ' + data.error + '\x1b[0m')
        }
        terminal.writeln(`\x1b[90mExecution time: ${data.execution_time_ms}ms\x1b[0m`)
        terminal.write('\r\n$ ')
      }
    },
  })

  useEffect(() => {
    if (!terminalRef.current || terminal) return

    const term = new Terminal({
      cursorBlink: true,
      theme: {
        background: '#1e1e1e',
        foreground: '#ffffff',
      },
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(terminalRef.current)
    fitAddon.fit()

    term.writeln('\x1b[1;34mHetzner Cloud MCP CLI\x1b[0m')
    term.writeln('Type a command (e.g., "server_list") or "help" for available commands\r\n')
    term.write('$ ')

    let currentLine = ''

    term.onData((data) => {
      const code = data.charCodeAt(0)

      if (code === 13) { // Enter
        term.write('\r\n')
        if (currentLine.trim()) {
          if (currentLine.trim() === 'help') {
            term.writeln('\x1b[33mAvailable commands - see sidebar for full list\x1b[0m')
            term.write('\r\n$ ')
          } else if (currentLine.trim() === 'clear') {
            term.clear()
            term.write('$ ')
          } else {
            addToHistory(currentLine)
            const [command, ...args] = currentLine.split(' ')
            executeMutation.mutate({ command, args: {} })
          }
        } else {
          term.write('$ ')
        }
        currentLine = ''
      } else if (code === 127) { // Backspace
        if (currentLine.length > 0) {
          currentLine = currentLine.slice(0, -1)
          term.write('\b \b')
        }
      } else if (code === 27) { // Escape sequences (Arrow keys)
        if (data.length === 3) {
          const direction = data[2] === 'A' ? 'up' : data[2] === 'B' ? 'down' : null
          if (direction) {
            const historyCommand = navigateHistory(direction)
            if (historyCommand !== null) {
              // Clear current line
              term.write('\r\x1b[K')
              term.write('$ ')
              currentLine = historyCommand
              term.write(currentLine)
            }
          }
        }
      } else if (code >= 32 && code < 127) { // Printable characters
        currentLine += data
        term.write(data)
      }
    })

    setTerminal(term)

    return () => {
      term.dispose()
    }
  }, [terminalRef])

  const tools = toolsData?.data?.tools || []

  return (
    <div className="grid grid-cols-4 gap-6 h-[calc(100vh-8rem)]">
      <div className="col-span-3">
        <div className="card h-full flex flex-col">
          <h1 className="text-2xl font-bold mb-4">CLI Terminal</h1>
          <div
            ref={terminalRef}
            className="flex-1 bg-[#1e1e1e] rounded-lg p-2"
          />
        </div>
      </div>

      <div className="card overflow-y-auto">
        <h2 className="text-lg font-semibold mb-4">Available Tools</h2>
        <div className="space-y-2">
          {tools.map((tool: any) => (
            <div
              key={tool.name}
              className="p-2 hover:bg-gray-50 rounded cursor-pointer text-xs"
              onClick={() => {
                if (terminal) {
                  terminal.write(tool.name)
                }
              }}
            >
              <div className="font-mono text-sm text-hetzner-red">{tool.name}</div>
              <div className="text-xs text-gray-600 line-clamp-2">{tool.description}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
