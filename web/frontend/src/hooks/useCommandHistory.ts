import { useState, useCallback } from 'react'

export function useCommandHistory() {
  const [history, setHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)

  const addToHistory = useCallback((command: string) => {
    setHistory(prev => [...prev, command])
    setHistoryIndex(-1)
  }, [])

  const navigateHistory = useCallback((direction: 'up' | 'down') => {
    if (history.length === 0) return null

    let newIndex = historyIndex
    if (direction === 'up') {
      newIndex = historyIndex === -1 ? history.length - 1 : Math.max(0, historyIndex - 1)
    } else {
      newIndex = historyIndex === -1 ? -1 : Math.min(history.length - 1, historyIndex + 1)
    }

    setHistoryIndex(newIndex)
    return newIndex === -1 ? '' : history[newIndex]
  }, [history, historyIndex])

  return { addToHistory, navigateHistory, history }
}
