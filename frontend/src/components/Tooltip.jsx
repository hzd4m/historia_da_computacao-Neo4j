import { useState, useRef, useEffect } from 'react'

export default function Tooltip({ children, content, direction = 'top' }) {
  const [visible, setVisible] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const triggerRef = useRef(null)

  const handleMouseEnter = (e) => {
    setVisible(true)
    const rect = e.currentTarget.getBoundingClientRect()
    setPosition({
      x: rect.left + rect.width / 2,
      y: rect.top
    })
  }

  const handleMouseLeave = () => {
    setVisible(false)
  }

  return (
    <div 
      className="tooltip-trigger"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      ref={triggerRef}
    >
      {children}
      {visible && (
        <div 
          className={`tooltip tooltip-${direction}`}
          style={{
            position: 'fixed',
            left: position.x,
            top: position.y,
            transform: direction === 'top' ? 'translate(-50%, -100%)' : 'translate(-50%, 100%)',
            zIndex: 1000
          }}
        >
          {content}
        </div>
      )}
    </div>
  )
}