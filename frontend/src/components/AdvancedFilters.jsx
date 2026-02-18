import { useState, useEffect } from 'react'
import { useGraphContext } from '../state/GraphContext'

export default function AdvancedFilters() {
  const { originalGraph, filters, applyFilters } = useGraphContext()
  const [localFilters, setLocalFilters] = useState(filters)
  
  // Obter categorias únicas do grafo
  const categories = [...new Set(originalGraph.nodes.map(node => node.category))]
  
  // Obter anos mínimo e máximo do grafo
  const years = originalGraph.nodes
    .map(node => node.year)
    .filter(year => year !== null)
    .sort((a, b) => a - b)
  
  const minYear = years.length > 0 ? years[0] : 1900
  const maxYear = years.length > 0 ? years[years.length - 1] : new Date().getFullYear()

  useEffect(() => {
    setLocalFilters(filters)
  }, [filters])

  const handleCategoryChange = (category) => {
    const newCategories = localFilters.categories.includes(category)
      ? localFilters.categories.filter(c => c !== category)
      : [...localFilters.categories, category]
    
    setLocalFilters({
      ...localFilters,
      categories: newCategories
    })
  }

  const handleYearChange = (type, value) => {
    setLocalFilters({
      ...localFilters,
      yearRange: {
        ...localFilters.yearRange,
        [type]: parseInt(value) || null
      }
    })
  }

  const handleRegionChange = (value) => {
    setLocalFilters({
      ...localFilters,
      region: value
    })
  }

  const handleApply = () => {
    applyFilters(localFilters)
  }

  const handleReset = () => {
    const resetFilters = {
      categories: [],
      yearRange: { min: null, max: null },
      region: ''
    }
    setLocalFilters(resetFilters)
    applyFilters(resetFilters)
  }

  return (
    <div className="advanced-filters">
      <h3>Filtros Avançados</h3>
      
      <div className="filter-group">
        <h4>Categorias</h4>
        <div className="category-filters">
          {categories.map(category => (
            <label key={category} className="filter-checkbox">
              <input
                type="checkbox"
                checked={localFilters.categories.includes(category)}
                onChange={() => handleCategoryChange(category)}
              />
              {category}
            </label>
          ))}
        </div>
      </div>
      
      <div className="filter-group">
        <h4>Período</h4>
        <div className="year-range">
          <label>
            De:
            <input
              type="number"
              min={minYear}
              max={maxYear}
              value={localFilters.yearRange.min || ''}
              onChange={(e) => handleYearChange('min', e.target.value)}
            />
          </label>
          <label>
            Até:
            <input
              type="number"
              min={minYear}
              max={maxYear}
              value={localFilters.yearRange.max || ''}
              onChange={(e) => handleYearChange('max', e.target.value)}
            />
          </label>
        </div>
      </div>
      
      <div className="filter-group">
        <h4>Região</h4>
        <input
          type="text"
          placeholder="Digite uma região..."
          value={localFilters.region}
          onChange={(e) => handleRegionChange(e.target.value)}
        />
      </div>
      
      <div className="filter-actions">
        <button onClick={handleApply}>Aplicar Filtros</button>
        <button onClick={handleReset}>Limpar Filtros</button>
      </div>
    </div>
  )
}