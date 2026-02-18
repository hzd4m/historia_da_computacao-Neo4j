import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { useGraphContext } from '../state/GraphContext'

export default function InnovationTimeline() {
  const { originalGraph } = useGraphContext()
  const [timelineData, setTimelineData] = useState([])
  const [cumulativeData, setCumulativeData] = useState([])

  useEffect(() => {
    if (!originalGraph.nodes.length) return

    // Process timeline data
    const yearCount = {}
    const categoryTimeline = {}

    originalGraph.nodes.forEach(node => {
      if (node.year) {
        // Count by year
        if (!yearCount[node.year]) {
          yearCount[node.year] = 0
        }
        yearCount[node.year]++

        // Count by category and year
        if (!categoryTimeline[node.category]) {
          categoryTimeline[node.category] = {}
        }
        if (!categoryTimeline[node.category][node.year]) {
          categoryTimeline[node.category][node.year] = 0
        }
        categoryTimeline[node.category][node.year]++
      }
    })

    // Format timeline data
    const formattedTimelineData = Object.keys(yearCount)
      .sort((a, b) => a - b)
      .map(year => ({
        year: parseInt(year),
        innovations: yearCount[year]
      }))

    setTimelineData(formattedTimelineData)

    // Create cumulative data
    let cumulativeCount = 0
    const formattedCumulativeData = formattedTimelineData.map(dataPoint => {
      cumulativeCount += dataPoint.innovations
      return {
        year: dataPoint.year,
        cumulative: cumulativeCount,
        innovations: dataPoint.innovations
      }
    })

    setCumulativeData(formattedCumulativeData)
  }, [originalGraph])

  if (!timelineData.length) return null

  return (
    <div className="visualization-container">
      <h3>Inovações ao Longo do Tempo</h3>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={timelineData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="innovations" 
              stroke="#8884d8" 
              activeDot={{ r: 8 }} 
              name="Inovações por Ano"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h3>Crescimento Cumulativo</h3>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={cumulativeData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="cumulative" 
              stackId="1" 
              stroke="#8884d8" 
              fill="#8884d8" 
              fillOpacity={0.6}
              name="Total Acumulado"
            />
            <Area 
              type="monotone" 
              dataKey="innovations" 
              stackId="2" 
              stroke="#82ca9d" 
              fill="#82ca9d" 
              fillOpacity={0.6}
              name="Novas Inovações"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}