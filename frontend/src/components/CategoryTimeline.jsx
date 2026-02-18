import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useGraphContext } from '../state/GraphContext'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8']

export default function CategoryTimeline() {
  const { originalGraph } = useGraphContext()
  const [chartData, setChartData] = useState([])
  const [pieData, setPieData] = useState([])

  useEffect(() => {
    if (!originalGraph.nodes.length) return

    // Process data for timeline chart
    const timelineData = {}
    const categoryCount = {}

    originalGraph.nodes.forEach(node => {
      // Count categories
      if (!categoryCount[node.category]) {
        categoryCount[node.category] = 0
      }
      categoryCount[node.category]++

      // Process timeline data
      if (node.year) {
        const decade = Math.floor(node.year / 10) * 10
        if (!timelineData[decade]) {
          timelineData[decade] = {}
        }
        if (!timelineData[decade][node.category]) {
          timelineData[decade][node.category] = 0
        }
        timelineData[decade][node.category]++
      }
    })

    // Format timeline data
    const formattedTimelineData = Object.keys(timelineData)
      .sort((a, b) => a - b)
      .map(decade => {
        const dataPoint = { name: `${decade}s`, total: 0 }
        Object.keys(timelineData[decade]).forEach(category => {
          dataPoint[category] = timelineData[decade][category]
          dataPoint.total += timelineData[decade][category]
        })
        return dataPoint
      })

    setChartData(formattedTimelineData)

    // Format pie chart data
    const formattedPieData = Object.keys(categoryCount)
      .map(category => ({
        name: category,
        value: categoryCount[category]
      }))
      .sort((a, b) => b.value - a.value)

    setPieData(formattedPieData)
  }, [originalGraph])

  if (!chartData.length) return null

  return (
    <div className="visualization-container">
      <h3>Evolução Histórica por Categoria</h3>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            {pieData.map((category, index) => (
              <Bar 
                key={category.name} 
                dataKey={category.name} 
                stackId="a" 
                fill={COLORS[index % COLORS.length]} 
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      <h3>Distribuição de Categorias</h3>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={true}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}