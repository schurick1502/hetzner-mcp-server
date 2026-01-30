import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

interface MetricsChartProps {
  data: Array<{ timestamp: string; value: number }>
  title: string
  color: string
  unit: string
}

export default function MetricsChart({ data, title, color, unit }: MetricsChartProps) {
  const chartData = data.map(d => ({
    time: new Date(d.timestamp).getTime(),
    value: d.value
  }))

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="time"
            tickFormatter={(ts) => format(new Date(ts), 'HH:mm')}
          />
          <YAxis label={{ value: unit, angle: -90, position: 'insideLeft' }} />
          <Tooltip
            labelFormatter={(ts) => format(new Date(ts), 'HH:mm:ss')}
            formatter={(value) => [typeof value === 'number' ? value.toFixed(2) : '0.00', unit]}
          />
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
