import { useState, useEffect } from 'react'
import { useGraphContext } from '../state/GraphContext'

export default function WordCloudVisualization() {
  const { originalGraph } = useGraphContext()
  const [words, setWords] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')

  useEffect(() => {
    if (!originalGraph.nodes.length) return

    // Extract words from node names and descriptions
    const wordFrequency = {}
    const categories = new Set(['all'])

    originalGraph.nodes.forEach(node => {
      categories.add(node.category)
      
      // Process node name
      const nameWords = node.name.toLowerCase().split(/[\s\-]+/)
      nameWords.forEach(word => {
        if (word.length > 3) { // Filter out short words
          const cleanWord = word.replace(/[^\w]/g, '')
          if (cleanWord && cleanWord.length > 2) {
            if (!wordFrequency[cleanWord]) {
              wordFrequency[cleanWord] = { frequency: 0, categories: new Set() }
            }
            wordFrequency[cleanWord].frequency++
            wordFrequency[cleanWord].categories.add(node.category)
          }
        }
      })

      // Process description/bio
      const description = node.description || node.bio || ''
      const descWords = description.toLowerCase().split(/[\s\-]+/)
      descWords.forEach(word => {
        if (word.length > 3) {
          const cleanWord = word.replace(/[^\w]/g, '')
          if (cleanWord && cleanWord.length > 2) {
            if (!wordFrequency[cleanWord]) {
              wordFrequency[cleanWord] = { frequency: 0, categories: new Set() }
            }
            wordFrequency[cleanWord].frequency++
            wordFrequency[cleanWord].categories.add(node.category)
          }
        }
      })
    })

    // Convert to array and filter
    const wordArray = Object.entries(wordFrequency)
      .map(([word, data]) => ({
        text: word,
        value: data.frequency,
        categories: Array.from(data.categories)
      }))
      .filter(item => item.value > 1) // Only words appearing more than once
      .sort((a, b) => b.value - a.value)
      .slice(0, 100) // Top 100 words

    setWords(wordArray)
  }, [originalGraph])

  // Filter words by selected category
  const filteredWords = selectedCategory === 'all' 
    ? words 
    : words.filter(word => word.categories.includes(selectedCategory))

  // Generate random positions for words
  const positionedWords = filteredWords.map((word, index) => ({
    ...word,
    x: Math.random() * 80 + 10, // 10-90% of container
    y: Math.random() * 80 + 10,
    fontSize: Math.max(12, Math.min(40, word.value * 2)) // Scale font size
  }))

  if (!words.length) return null

  return (
    <div className="visualization-container">
      <h3>Nuvem de Palavras dos Conteúdos</h3>
      <div className="wordcloud-controls">
        <label>
          Filtrar por Categoria:
          <select 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">Todas</option>
            {Array.from(new Set(words.flatMap(word => word.categories)))
              .map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
          </select>
        </label>
      </div>
      <div className="wordcloud-container">
        {positionedWords.map((word, index) => (
          <span
            key={`${word.text}-${index}`}
            className="wordcloud-word"
            style={{
              position: 'absolute',
              left: `${word.x}%`,
              top: `${word.y}%`,
              fontSize: `${word.fontSize}px`,
              color: `hsl(${(index * 30) % 360}, 70%, 50%)`,
              transform: `rotate(${Math.random() * 20 - 10}deg)`,
              opacity: 0.8 + (word.value / 20),
              fontWeight: word.value > 5 ? 'bold' : 'normal'
            }}
          >
            {word.text}
          </span>
        ))}
      </div>
    </div>
  )
}