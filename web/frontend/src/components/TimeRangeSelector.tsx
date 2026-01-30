interface TimeRangeSelectorProps {
  selected: string
  onChange: (range: string) => void
}

export default function TimeRangeSelector({ selected, onChange }: TimeRangeSelectorProps) {
  const ranges = [
    { value: '1h', label: '1 Stunde' },
    { value: '24h', label: '24 Stunden' },
    { value: '7d', label: '7 Tage' },
  ]

  return (
    <div className="flex gap-2">
      {ranges.map(range => (
        <button
          key={range.value}
          onClick={() => onChange(range.value)}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            selected === range.value
              ? 'bg-hetzner-red text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  )
}
