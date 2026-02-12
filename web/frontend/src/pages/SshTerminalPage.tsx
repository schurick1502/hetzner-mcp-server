import { useState, useRef, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Terminal, Plug, PlugZap, Server } from 'lucide-react'
import { serversApi } from '../services/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8501'

function getWsUrl(serverIp: string): string {
  const base = API_URL.replace(/^http/, 'ws')
  return `${base}/api/ssh/ws/${serverIp}`
}

export default function SshTerminalPage() {
  const [selectedIp, setSelectedIp] = useState('')
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const termRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const xtermRef = useRef<any>(null)
  const fitAddonRef = useRef<any>(null)

  const { data: serversData } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
  })

  const servers = serversData?.data?.servers || []

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
    setConnecting(false)
  }, [])

  const connect = useCallback(async () => {
    if (!selectedIp || connecting) return

    setConnecting(true)

    // Terminal initialisieren (lazy import)
    try {
      const { Terminal } = await import('xterm')
      const { FitAddon } = await import('xterm-addon-fit')
      await import('xterm/css/xterm.css')

      // Altes Terminal aufräumen
      if (xtermRef.current) {
        xtermRef.current.dispose()
      }
      if (termRef.current) {
        termRef.current.innerHTML = ''
      }

      const fitAddon = new FitAddon()
      fitAddonRef.current = fitAddon

      const term = new Terminal({
        cursorBlink: true,
        fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
        fontSize: 14,
        theme: {
          background: '#1a1b26',
          foreground: '#a9b1d6',
          cursor: '#c0caf5',
          selectionBackground: '#33467c',
          black: '#32344a',
          red: '#f7768e',
          green: '#9ece6a',
          yellow: '#e0af68',
          blue: '#7aa2f7',
          magenta: '#ad8ee6',
          cyan: '#449dab',
          white: '#787c99',
          brightBlack: '#444b6a',
          brightRed: '#ff7a93',
          brightGreen: '#b9f27c',
          brightYellow: '#ff9e64',
          brightBlue: '#7da6ff',
          brightMagenta: '#bb9af7',
          brightCyan: '#0db9d7',
          brightWhite: '#acb0d0',
        },
        scrollback: 5000,
      })

      term.loadAddon(fitAddon)
      xtermRef.current = term

      if (termRef.current) {
        term.open(termRef.current)
        fitAddon.fit()
      }

      // WebSocket verbinden
      const ws = new WebSocket(getWsUrl(selectedIp))
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        setConnecting(false)
        term.focus()
      }

      ws.onmessage = (event) => {
        term.write(event.data)
      }

      ws.onerror = () => {
        term.write('\r\n*** WebSocket-Verbindungsfehler ***\r\n')
        setConnecting(false)
      }

      ws.onclose = () => {
        term.write('\r\n*** Verbindung getrennt ***\r\n')
        setConnected(false)
        setConnecting(false)
      }

      // Terminal-Input → WebSocket
      term.onData((data: string) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data)
        }
      })

      // Terminal resize → SSH resize
      term.onResize(({ cols, rows }: { cols: number; rows: number }) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'resize', cols, rows }))
        }
      })

    } catch (error: any) {
      console.error('Terminal init error:', error)
      setConnecting(false)
    }
  }, [selectedIp, connecting])

  // Cleanup bei Unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (xtermRef.current) {
        xtermRef.current.dispose()
      }
    }
  }, [])

  // Resize handler
  useEffect(() => {
    const handleResize = () => {
      if (fitAddonRef.current) {
        try {
          fitAddonRef.current.fit()
        } catch {}
      }
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Auto-select first server
  useEffect(() => {
    if (servers.length > 0 && !selectedIp) {
      const first = servers.find((s: any) => s.public_ipv4 && s.status === 'running')
      if (first) {
        setSelectedIp(first.public_ipv4)
      }
    }
  }, [servers, selectedIp])

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Terminal size={32} /> SSH Terminal
        </h1>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4 mb-4 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Server size={16} className="text-gray-500" />
          <select
            value={selectedIp}
            onChange={(e) => {
              if (connected) disconnect()
              setSelectedIp(e.target.value)
            }}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-hetzner-blue"
            disabled={connecting}
          >
            <option value="">Server wählen...</option>
            {servers.map((s: any) => (
              <option
                key={s.id || s.name}
                value={s.public_ipv4}
                disabled={!s.public_ipv4 || s.status !== 'running'}
              >
                {s.name} ({s.public_ipv4 || 'keine IP'}) - {s.status}
              </option>
            ))}
          </select>
        </div>

        {!connected ? (
          <button
            onClick={connect}
            disabled={!selectedIp || connecting}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plug size={16} />
            {connecting ? 'Verbinde...' : 'Verbinden'}
          </button>
        ) : (
          <button
            onClick={disconnect}
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center gap-2"
          >
            <PlugZap size={16} />
            Trennen
          </button>
        )}

        <div className="ml-auto flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : connecting ? 'bg-yellow-500 animate-pulse' : 'bg-gray-300'}`} />
          <span className="text-sm text-gray-600">
            {connected ? 'Verbunden' : connecting ? 'Verbinde...' : 'Getrennt'}
          </span>
        </div>
      </div>

      {/* Terminal */}
      <div className="flex-1 bg-[#1a1b26] rounded-lg overflow-hidden relative">
        {!connected && !connecting && (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <div className="text-center">
              <Terminal size={64} className="mx-auto text-gray-600 mb-4" />
              <p className="text-gray-400 text-lg mb-2">SSH Web-Terminal</p>
              <p className="text-gray-500 text-sm">
                Wähle einen Server und klicke auf "Verbinden"
              </p>
            </div>
          </div>
        )}
        <div
          ref={termRef}
          className="w-full h-full"
          style={{ padding: connected || connecting ? '4px' : '0' }}
        />
      </div>
    </div>
  )
}
