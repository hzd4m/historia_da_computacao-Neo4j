import { useState, useEffect } from 'react'
import { useGraphContext } from '../state/GraphContext'

export default function Notifications() {
  const { originalGraph } = useGraphContext()
  const [notifications, setNotifications] = useState([])
  const [visible, setVisible] = useState(true)

  // Função para gerar notificações inteligentes
  useEffect(() => {
    if (!originalGraph.nodes.length) return

    const newNotifications = []
    
    // Verificar conexões interessantes
    const nodeConnections = {}
    originalGraph.edges.forEach(edge => {
      if (!nodeConnections[edge.source]) nodeConnections[edge.source] = 0
      if (!nodeConnections[edge.target]) nodeConnections[edge.target] = 0
      nodeConnections[edge.source]++
      nodeConnections[edge.target]++
    })
    
    // Encontrar nós com muitas conexões
    const highlyConnectedNodes = Object.entries(nodeConnections)
      .filter(([_, count]) => count > 3)
      .map(([nodeId]) => originalGraph.nodes.find(n => n.id === nodeId))
      .filter(Boolean)
    
    if (highlyConnectedNodes.length > 0) {
      newNotifications.push({
        id: 'highly-connected',
        type: 'info',
        title: 'Nós Altamente Conectados',
        message: `Existem ${highlyConnectedNodes.length} nós com mais de 3 conexões. Clique para explorar.`,
        action: () => console.log('Explorar nós altamente conectados')
      })
    }
    
    // Verificar períodos históricos densos
    const nodesByDecade = {}
    originalGraph.nodes.forEach(node => {
      if (node.year) {
        const decade = Math.floor(node.year / 10) * 10
        if (!nodesByDecade[decade]) nodesByDecade[decade] = 0
        nodesByDecade[decade]++
      }
    })
    
    const densestDecade = Object.entries(nodesByDecade)
      .sort((a, b) => b[1] - a[1])[0]
    
    if (densestDecade && densestDecade[1] > 5) {
      newNotifications.push({
        id: 'dense-period',
        type: 'info',
        title: 'Período Histórico Denso',
        message: `A década de ${densestDecade[0]} teve ${densestDecade[1]} eventos significativos.`,
        action: () => console.log('Explorar período denso')
      })
    }
    
    // Verificar categorias predominantes
    const categoryCount = {}
    originalGraph.nodes.forEach(node => {
      if (!categoryCount[node.category]) categoryCount[node.category] = 0
      categoryCount[node.category]++
    })
    
    const predominantCategory = Object.entries(categoryCount)
      .sort((a, b) => b[1] - a[1])[0]
    
    if (predominantCategory && predominantCategory[1] > originalGraph.nodes.length * 0.4) {
      newNotifications.push({
        id: 'predominant-category',
        type: 'info',
        title: 'Categoria Predominante',
        message: `${predominantCategory[1]} nós são do tipo "${predominantCategory[0]}".`,
        action: () => console.log('Explorar categoria predominante')
      })
    }
    
    setNotifications(newNotifications)
  }, [originalGraph])

  const dismissNotification = (id) => {
    setNotifications(notifications.filter(n => n.id !== id))
  }

  const dismissAll = () => {
    setNotifications([])
  }

  if (!visible || notifications.length === 0) return null

  return (
    <div className="notifications-container">
      <div className="notifications-header">
        <h3>Notificações Inteligentes</h3>
        <button onClick={() => setVisible(false)}>×</button>
      </div>
      <div className="notifications-list">
        {notifications.map(notification => (
          <div key={notification.id} className={`notification notification-${notification.type}`}>
            <div className="notification-content">
              <h4>{notification.title}</h4>
              <p>{notification.message}</p>
            </div>
            <div className="notification-actions">
              <button onClick={notification.action}>Explorar</button>
              <button onClick={() => dismissNotification(notification.id)}>Dispensar</button>
            </div>
          </div>
        ))}
        {notifications.length > 1 && (
          <div className="notifications-footer">
            <button onClick={dismissAll}>Dispensar Todas</button>
          </div>
        )}
      </div>
    </div>
  )
}