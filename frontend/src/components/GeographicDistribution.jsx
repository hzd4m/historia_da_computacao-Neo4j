import { useState, useEffect } from 'react'
import { ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Scatter } from 'recharts'
import { useGraphContext } from '../state/GraphContext'

export default function GeographicDistribution() {
  const { originalGraph } = useGraphContext()
  const [geoData, setGeoData] = useState([])
  const [timelineData, setTimelineData] = useState([])

  useEffect(() => {
    if (!originalGraph.nodes.length) return

    // Process geographic data
    const countryCount = {}
    const timelineByCountry = {}

    originalGraph.nodes.forEach(node => {
      if (node.nacionalidade) {
        const country = node.nacionalidade.trim()
        if (!countryCount[country]) {
          countryCount[country] = 0
        }
        countryCount[country]++

        // Process timeline data by country
        if (node.year) {
          if (!timelineByCountry[country]) {
            timelineByCountry[country] = {}
          }
          const decade = Math.floor(node.year / 10) * 10
          if (!timelineByCountry[country][decade]) {
            timelineByCountry[country][decade] = 0
          }
          timelineByCountry[country][decade]++
        }
      }
    })

    // Format geographic data
    const formattedGeoData = Object.keys(countryCount)
      .map(country => ({
        name: country,
        contributions: countryCount[country],
        researchers: countryCount[country] // Simplified for now
      }))
      .sort((a, b) => b.contributions - a.contributions)
      .slice(0, 10) // Top 10 countries

    setGeoData(formattedGeoData)

    // Format timeline data
    const formattedTimelineData = []
    Object.keys(timelineByCountry).forEach(country => {
      Object.keys(timelineByCountry[country]).forEach(decade => {
        formattedTimelineData.push({
          country,
          decade: parseInt(decade),
          contributions: timelineByCountry[country][decade]
        })
      })
    })

    // Group by decade for stacked chart
    const groupedByDecade = {}
    formattedTimelineData.forEach(item => {
      if (!groupedByDecade[item.decade]) {
        groupedByDecade[item.decade] = { decade: item.decade }
      }
      groupedByDecade[item.decade][item.country] = item.contributions
    })

    const finalTimelineData = Object.values(groupedByDecade)
      .sort((a, b) => a.decade - b.decade)

    setTimelineData(finalTimelineData)
  }, [originalGraph])

  if (!geoData.length) return null

  return (
    <div className="visualization-container">
      <h3>Distribuição Geográfica de Contribuições</h3>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={geoData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="contributions" fill="#8884d8" name="Contribuições" />
            <Scatter dataKey="researchers" fill="#82ca9d" name="Pesquisadores" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <h3>Linha do Tempo por País</h3>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={timelineData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="decade" type="number" domain={['dataMin', 'dataMax']} />
            <YAxis />
            <Tooltip />
            <Legend />
            {geoData.slice(0, 5).map((country, index) => (
              <Scatter 
                key={country.name} 
                dataKey={country.name} 
                fill={`#${Math.floor(Math.random()*16777215).toString(16)}`} 
                name={country.name}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}