import { useState, useEffect } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, RadialBarChart, RadialBar, Legend, Tooltip } from 'recharts'
import { useGraphContext } from '../state/GraphContext'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8']

export default function NetworkMetrics() {
  const { originalGraph } = useGraphContext()
  const [metricsData, setMetricsData] = useState([])
  const [centralityData, setCentralityData] = useState([])

  useEffect(() => {
    if (!originalGraph.nodes.length) return

    // Calculate network metrics
    const nodeCount = originalGraph.nodes.length
    const edgeCount = originalGraph.edges.length
    const avgDegree = nodeCount > 0 ? (2 * edgeCount / nodeCount).toFixed(2) : 0
    
    // Calculate category distribution
    const categoryCount = {}
    originalGraph.nodes.forEach(node => {
      if (!categoryCount[node.category]) {
        categoryCount[node.category] = 0
      }
      categoryCount[node.category]++
    })

    // Format metrics data
    const formattedMetricsData = [
      { metric: 'Total de Nós', value: nodeCount },
      { metric: 'Total de Arestas', value: edgeCount },
      { metric: 'Grau Médio', value: parseFloat(avgDegree) },
      { metric: 'Densidade', value: nodeCount > 1 ? (2 * edgeCount / (nodeCount * (nodeCount - 1))).toFixed(4) : 0 },
      { metric: 'Categorias', value: Object.keys(categoryCount).length }
    ]

    setMetricsData(formattedMetricsData)

    // Calculate centrality measures (simplified)
    const nodeConnections = {}
    originalGraph.edges.forEach(edge => {
      if (!nodeConnections[edge.source]) nodeConnections[edge.source] = 0
      if (!nodeConnections[edge.target]) nodeConnections[edge.target] = 0
      nodeConnections[edge.source]++
      nodeConnections[edge.target]++
    })

    // Get top connected nodes
    const topNodes = Object.entries(nodeConnections)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([nodeId, connections]) => {
        const node = originalGraph.nodes.find(n => n.id === nodeId)
        return {
          name: node ? node.name : nodeId,
          connections: connections
        }
      })

    // Format centrality data
    const formattedCentralityData = topNodes.map((node, index) => ({
      name: node.name.length > 15 ? `${node.name.substring(0, 15)}...` : node.name,
      value: node.connections,
      fill: COLORS[index % COLORS.length]
    }))

    setCentralityData(formattedCentralityData)
  }, [originalGraph])

  if (!metricsData.length) return null

  return (
    <div className="visualization-container">
      <h3>Métricas da Rede</h3>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={metricsData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="metric" />
            <PolarRadiusAxis />
            <Radar 
              name="Métricas" 
              dataKey="value" 
              stroke="#8884d8" 
              fill="#8884d8" 
              fillOpacity={0.6} 
            />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <h3>Centralidade dos Nós Principais</h3>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <RadialBarChart 
            cx="50%" 
            cy="50%" 
            innerRadius="10%" 
            outerRadius="80%" 
            barSize={10} 
            data={centralityData}
          >
            <PolarGrid />
            <PolarAngleAxis 
              type="number" 
              domain={[0, 10]} 
              angleAxisId={0} 
              tick={false} 
            />
            <PolarRadiusAxis 
              angle={90} 
              tick={false} 
              axisLine={false} 
            />
            <RadialBar
              background
              dataKey="value"
              cornerRadius={10}
            >
              {centralityData.map((entry, index) => (
                <span key={`radial-bar-${index}`} fill={entry.fill} />
              ))}
            </RadialBar>
            <Tooltip />
            <Legend 
              layout="vertical" 
              verticalAlign="middle" 
              align="right"
              formatter={(value, entry, index) => (
                <span style={{ color: entry.payload.fill }}>
                  {entry.payload.name}: {entry.payload.value}
                </span>
              )}
            />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}