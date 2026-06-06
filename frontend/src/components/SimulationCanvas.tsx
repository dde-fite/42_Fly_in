import { useRef, useEffect, useState, useCallback } from 'react'
import type { ResponseSimulation, ResponseHub, ResponseDrone, ResponseConnection } from '../types'
import { getHub, getDrone, getConnection } from '../services/api'
import './SimulationCanvas.css'

interface SimulationCanvasProps {
  simulation: ResponseSimulation | null
  token: string
}

export default function SimulationCanvas({ simulation, token }: SimulationCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [hubs, setHubs] = useState<Map<string, ResponseHub>>(new Map())
  const [drones, setDrones] = useState<Map<string, ResponseDrone>>(new Map())
  const [connections, setConnections] = useState<Map<string, ResponseConnection>>(new Map())
  const [selectedHubId, setSelectedHubId] = useState<string | null>(null)
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null)
  const [droneColors, setDroneColors] = useState<Map<string, string>>(new Map())

  // Canvas state - persistent across simulation steps
  const stateRef = useRef({
    scale: 100,
    panX: 50,
    panY: 50,
    canvasWidth: 800,
    canvasHeight: 600,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
  })

  const modelToCanvas = useCallback((x: number, y: number): [number, number] => {
    const { scale, panX, panY } = stateRef.current
    return [x * scale + panX, y * scale + panY]
  }, [])

  const canvasToModel = useCallback((x: number, y: number): [number, number] => {
    const { scale, panX, panY } = stateRef.current
    return [(x - panX) / scale, (y - panY) / scale]
  }, [])

  // Generate deterministic color for drone based on its ID
  const getDroneColor = useCallback((droneId: string): string => {
    if (droneColors.has(droneId)) {
      return droneColors.get(droneId)!
    }
    
    // Generate hash from drone ID
    let hash = 0
    for (let i = 0; i < droneId.length; i++) {
      const char = droneId.charCodeAt(i)
      hash = (hash << 5) - hash + char
      hash = hash & hash // Convert to 32bit integer
    }
    
    // Generate vibrant colors
    const hue = (Math.abs(hash) % 360)
    const saturation = 70 + (Math.abs(hash) % 30)
    const lightness = 50
    
    const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`
    
    // Cache it
    const newColors = new Map(droneColors)
    newColors.set(droneId, color)
    setDroneColors(newColors)
    
    return color
  }, [droneColors])

  const autoFit = useCallback((hubsMap: Map<string, ResponseHub>) => {
    if (hubsMap.size === 0) return

    let minX = Infinity,
      maxX = -Infinity
    let minY = Infinity,
      maxY = -Infinity

    for (const hub of hubsMap.values()) {
      const [x, y] = hub.position
      minX = Math.min(minX, x)
      maxX = Math.max(maxX, x)
      minY = Math.min(minY, y)
      maxY = Math.max(maxY, y)
    }

    const width = maxX - minX || 1
    const height = maxY - minY || 1
    const padding = 80

    const { canvasWidth, canvasHeight } = stateRef.current
    const scaleX = (canvasWidth - padding * 2) / width
    const scaleY = (canvasHeight - padding * 2) / height
    const newScale = Math.min(scaleX, scaleY, 200)

    stateRef.current.scale = newScale
    stateRef.current.panX = padding - minX * newScale
    stateRef.current.panY = padding - minY * newScale
  }, [])

  const loadSimulationData = useCallback(async () => {
    if (!simulation || !token) {
      console.warn('Cannot load simulation data: simulation or token missing', { simulation, token })
      return
    }

    try {
      console.log('Loading simulation data for turn:', simulation.turn, 'with token:', token.substring(0, 10) + '...')
      const newHubs = new Map<string, ResponseHub>()
      const newDrones = new Map<string, ResponseDrone>()
      const newConnections = new Map<string, ResponseConnection>()

      // Load all hubs
      console.log('Fetching hubs:', simulation.hubs)
      for (const hubId of simulation.hubs) {
        try {
          const hub = await getHub(token, hubId)
          newHubs.set(hubId, hub)
        } catch (err) {
          console.error(`Failed to load hub ${hubId}:`, err)
          throw err
        }
      }

      // Load all drones
      console.log('Fetching drones:', simulation.drones)
      for (const droneId of simulation.drones) {
        try {
          const drone = await getDrone(token, droneId)
          console.log(`Loaded drone ${droneId}:`, drone)
          newDrones.set(droneId, drone)
        } catch (err) {
          console.error(`Failed to load drone ${droneId}:`, err)
          throw err
        }
      }

      // Load all connections
      console.log('Fetching connections:', simulation.connections)
      for (const connectionId of simulation.connections) {
        try {
          const connection = await getConnection(token, connectionId)
          newConnections.set(connectionId, connection)
        } catch (err) {
          console.error(`Failed to load connection ${connectionId}:`, err)
          throw err
        }
      }

      console.log('Successfully loaded simulation data:', {
        hubs: newHubs.size,
        drones: newDrones.size,
        connections: newConnections.size
      })

      setHubs(newHubs)
      setDrones(newDrones)
      setConnections(newConnections)

      // Log drone details
      for (const [droneId, drone] of newDrones) {
        console.log(`✈️ Drone ${droneId}: location=${drone.location}, destination=${drone.destination}`)
      }

      // Auto-fit only on first load
      if (newHubs.size > 0 && stateRef.current.scale === 100) {
        autoFit(newHubs)
      }
    } catch (err) {
      console.error('Failed to load simulation data:', err)
    }
  }, [simulation, token, autoFit])

  const drawGrid = useCallback((ctx: CanvasRenderingContext2D) => {
    const { canvasWidth, canvasHeight, scale, panX, panY } = stateRef.current

    ctx.strokeStyle = 'rgba(46, 125, 50, 0.05)'
    ctx.lineWidth = 0.5

    // Draw vertical lines
    const startX = Math.floor((-panX) / scale)
    const endX = Math.ceil((canvasWidth - panX) / scale)
    for (let i = startX; i < endX; i++) {
      const x = i * scale + panX
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, canvasHeight)
      ctx.stroke()
    }

    // Draw horizontal lines
    const startY = Math.floor((-panY) / scale)
    const endY = Math.ceil((canvasHeight - panY) / scale)
    for (let i = startY; i < endY; i++) {
      const y = i * scale + panY
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(canvasWidth, y)
      ctx.stroke()
    }
  }, [])

  const drawConnections = useCallback((ctx: CanvasRenderingContext2D) => {
    const { scale } = stateRef.current

    for (const [connId, connection] of connections) {
      const hub1 = hubs.get(connection.hubs[0])
      const hub2 = hubs.get(connection.hubs[1])

      if (!hub1 || !hub2) continue

      const [x1, y1] = modelToCanvas(...hub1.position)
      const [x2, y2] = modelToCanvas(...hub2.position)

      // Draw track line
      ctx.strokeStyle = '#2e7d32'
      ctx.lineWidth = Math.max(2, scale * 0.03)
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.stroke()

      // Draw capacity indicator
      const midX = (x1 + x2) / 2
      const midY = (y1 + y2) / 2
      const dronesOnConnection = Array.from(drones.values()).filter(
        (d) =>
          (d.location === connection.hubs[0] && d.destination === connection.hubs[1]) ||
          (d.location === connection.hubs[1] && d.destination === connection.hubs[0])
      ).length

      ctx.fillStyle = dronesOnConnection > 0 ? '#ff9800' : 'rgba(76, 175, 80, 0.3)'
      ctx.font = `bold ${Math.max(8, scale * 0.1)}px Courier New`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(`${dronesOnConnection}/${connection.capacity}`, midX, midY)
    }
  }, [connections, drones, hubs, modelToCanvas])

  const drawHubs = useCallback((ctx: CanvasRenderingContext2D) => {
    const { scale } = stateRef.current

    for (const [hubId, hub] of hubs) {
      const [x, y] = modelToCanvas(...hub.position)
      const isSelected = hubId === selectedHubId
      const isOrigin = hubId === simulation?.origin
      const isDestination = hubId === simulation?.destination
      const droneCount = hub.drones.length

      // Draw hub circle
      const radius = Math.max(12, scale * 0.15)
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)

      if (isOrigin) {
        ctx.fillStyle = '#4caf50'
      } else if (isDestination) {
        ctx.fillStyle = '#f44336'
      } else {
        ctx.fillStyle = '#1b5e20'
      }

      ctx.fill()

      // Border
      ctx.strokeStyle = isSelected ? '#ffeb3b' : '#4caf50'
      ctx.lineWidth = isSelected ? Math.max(2, scale * 0.03) : Math.max(1.5, scale * 0.02)
      ctx.stroke()

      // Hub name
      ctx.fillStyle = '#fff'
      ctx.font = `bold ${Math.max(9, scale * 0.11)}px Courier New`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(hub.name, x, y - radius - 5)

      // Drone count
      if (droneCount > 0) {
        ctx.fillStyle = '#ffeb3b'
        ctx.font = `bold ${Math.max(8, scale * 0.1)}px Courier New`
        ctx.fillText(`${droneCount}`, x, y)
      }

      // Capacity
      ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
      ctx.font = `${Math.max(7, scale * 0.08)}px Courier New`
      ctx.fillText(`Cap: ${hub.capacity}`, x, y + radius + 12)
    }
  }, [hubs, modelToCanvas, selectedHubId, simulation])

  const drawDrones = useCallback((ctx: CanvasRenderingContext2D) => {
    const { scale } = stateRef.current

    if (drones.size === 0) {
      console.log('No drones to draw')
      return
    }

    console.log(`Drawing ${drones.size} drones`)

    // Group drones by location to avoid overlapping
    const dronesByLocation = new Map<string, string[]>()
    for (const [droneId, drone] of drones) {
      if (!dronesByLocation.has(drone.location)) {
        dronesByLocation.set(drone.location, [])
      }
      dronesByLocation.get(drone.location)!.push(droneId)
    }

    for (const [droneId, drone] of drones) {
      // Try to find the position: first check if it's a hub
      let posX = 0, posY = 0
      let found = false

      // Check if location is a hub
      const locationHub = hubs.get(drone.location)
      if (locationHub) {
        [posX, posY] = modelToCanvas(...locationHub.position)
        found = true
        console.log(`Drone ${droneId} in hub ${drone.location} at (${posX.toFixed(0)}, ${posY.toFixed(0)})`)
      } else {
        // Try to find if it's between two hubs (on a connection)
        for (const [connId, connection] of connections) {
          if (connId === drone.location || 
              connection.hubs.includes(drone.location as any)) {
            const hub1 = hubs.get(connection.hubs[0])
            const hub2 = hubs.get(connection.hubs[1])
            if (hub1 && hub2) {
              const [x1, y1] = modelToCanvas(...hub1.position)
              const [x2, y2] = modelToCanvas(...hub2.position)
              // Position drone in middle of connection
              posX = (x1 + x2) / 2
              posY = (y1 + y2) / 2
              found = true
              console.log(`Drone ${droneId} on connection ${connId} at (${posX.toFixed(0)}, ${posY.toFixed(0)})`)
              break
            }
          }
        }
      }

      if (!found) {
        console.warn(`Cannot find position for drone ${droneId} at location ${drone.location}`)
        continue
      }

      // Calculate small offset if multiple drones at same location
      const dronesAtLocation = dronesByLocation.get(drone.location)?.length || 1
      const dronePositionAtLocation = (dronesByLocation.get(drone.location) || []).indexOf(droneId)
      const angleOffset = (dronePositionAtLocation / Math.max(1, dronesAtLocation)) * Math.PI * 2
      const radiusOffset = Math.max(4, scale * 0.05) // Much smaller offset
      
      const x = posX + Math.cos(angleOffset) * radiusOffset
      const y = posY + Math.sin(angleOffset) * radiusOffset

      // Draw very small blue drone with random color
      const droneSize = Math.max(4, scale * 0.05) // Much smaller
      const droneColor = getDroneColor(droneId)
      drawDroneIllustration(ctx, x, y, droneSize, droneColor)
    }
  }, [drones, hubs, connections, modelToCanvas, getDroneColor])

  const drawDroneIllustration = (ctx: CanvasRenderingContext2D, x: number, y: number, size: number, color: string) => {
    // Main body (rectangle) - use random color
    ctx.fillStyle = color
    ctx.fillRect(x - size / 2, y - size / 3, size, size * 0.6)

    // Propellers (4 small circles at corners)
    const propRadius = size * 0.25
    const propPositions = [
      { px: -size / 2.5, py: -size / 2 },
      { px: size / 2.5, py: -size / 2 },
      { px: -size / 2.5, py: size / 2 },
      { px: size / 2.5, py: size / 2 },
    ]

    ctx.fillStyle = color
    ctx.globalAlpha = 0.7
    for (const pos of propPositions) {
      ctx.beginPath()
      ctx.arc(x + pos.px, y + pos.py, propRadius * 0.4, 0, Math.PI * 2)
      ctx.fill()
    }
    ctx.globalAlpha = 1

    // Thin white border for visibility
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 0.5
    ctx.strokeRect(x - size / 2, y - size / 3, size, size * 0.6)
  }

  const redraw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const { canvasWidth, canvasHeight } = stateRef.current

    // Clear canvas
    ctx.fillStyle = '#0a0a0a'
    ctx.fillRect(0, 0, canvasWidth, canvasHeight)

    // Draw grid
    drawGrid(ctx)

    // Draw connections
    drawConnections(ctx)

    // Draw hubs
    drawHubs(ctx)

    // Draw drones
    console.log(`Redraw: canvas size ${canvasWidth}x${canvasHeight}, drones count: ${drones.size}`)
    drawDrones(ctx)
  }, [drawGrid, drawConnections, drawHubs, drawDrones, drones.size, hubs.size, connections.size])

  const handleCanvasClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current
      if (!canvas) return

      const rect = canvas.getBoundingClientRect()
      const canvasX = e.clientX - rect.left
      const canvasY = e.clientY - rect.top

      // Check if clicked on a hub
      for (const [hubId, hub] of hubs) {
        const [hx, hy] = modelToCanvas(...hub.position)
        const distance = Math.sqrt((canvasX - hx) ** 2 + (canvasY - hy) ** 2)

        if (distance < 25) {
          setSelectedHubId(hubId)
          setSelectedConnectionId(null)
          return
        }
      }

      // Check if clicked on a connection
      for (const [connId, connection] of connections) {
        const hub1 = hubs.get(connection.hubs[0])
        const hub2 = hubs.get(connection.hubs[1])
        if (!hub1 || !hub2) continue

        const [x1, y1] = modelToCanvas(...hub1.position)
        const [x2, y2] = modelToCanvas(...hub2.position)

        // Distance from point to line
        const A = canvasX - x1
        const B = canvasY - y1
        const C = x2 - x1
        const D = y2 - y1

        const dot = A * C + B * D
        const lenSq = C * C + D * D
        let param = -1

        if (lenSq !== 0) param = dot / lenSq

        let xx, yy

        if (param < 0) {
          xx = x1
          yy = y1
        } else if (param > 1) {
          xx = x2
          yy = y2
        } else {
          xx = x1 + param * C
          yy = y1 + param * D
        }

        const distance = Math.sqrt((canvasX - xx) ** 2 + (canvasY - yy) ** 2)

        if (distance < 10) {
          setSelectedConnectionId(connId)
          setSelectedHubId(null)
          return
        }
      }

      setSelectedHubId(null)
      setSelectedConnectionId(null)
    },
    [hubs, connections, modelToCanvas]
  )

  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault()

    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
    const newScale = stateRef.current.scale * zoomFactor

    if (newScale >= 20 && newScale <= 500) {
      stateRef.current.scale = newScale
      redraw()
    }
  }, [redraw])

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (e.button !== 0) return // Left click only

    stateRef.current.isDragging = true
    stateRef.current.dragStartX = e.clientX
    stateRef.current.dragStartY = e.clientY
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!stateRef.current.isDragging) return

    const deltaX = e.clientX - stateRef.current.dragStartX
    const deltaY = e.clientY - stateRef.current.dragStartY

    stateRef.current.panX += deltaX
    stateRef.current.panY += deltaY
    stateRef.current.dragStartX = e.clientX
    stateRef.current.dragStartY = e.clientY

    redraw()
  }, [redraw])

  const handleMouseUp = useCallback(() => {
    stateRef.current.isDragging = false
  }, [])

  const handleResize = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas || !canvas.parentElement) return

    stateRef.current.canvasWidth = canvas.parentElement.clientWidth
    stateRef.current.canvasHeight = canvas.parentElement.clientHeight

    canvas.width = stateRef.current.canvasWidth
    canvas.height = stateRef.current.canvasHeight

    redraw()
  }, [redraw])

  const handleFit = useCallback(() => {
    autoFit(hubs)
    redraw()
  }, [hubs, autoFit, redraw])

  useEffect(() => {
    console.log('useEffect: loading simulation data, simulation=', simulation?.turn, 'token=', token?.substring(0, 10))
    console.log('Drones before reload:', drones.size)
    loadSimulationData()
  }, [simulation, loadSimulationData, token])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    handleResize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [handleResize])

  useEffect(() => {
    redraw()
  }, [redraw, hubs, drones, connections, selectedHubId, selectedConnectionId])

  const selectedHub = hubs.get(selectedHubId || '')
  const selectedConnection = connections.get(selectedConnectionId || '')

  return (
    <div className="simulation-canvas-container">
      <canvas
        ref={canvasRef}
        className="simulation-canvas"
        onClick={handleCanvasClick}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      />

      {/* Controls overlay */}
      <div className="canvas-controls">
        <button className="control-btn" onClick={handleFit} title="Fit to view">
          🔍 Fit
        </button>
        <div className="scale-info">Scale: {stateRef.current.scale.toFixed(0)}x</div>
      </div>

      {/* Hub detail panel */}
      {selectedHub && (
        <div className="detail-panel hub-panel">
          <div className="detail-header">
            <h4>{selectedHub.name}</h4>
            <button className="close-btn" onClick={() => setSelectedHubId(null)}>
              ✕
            </button>
          </div>
          <div className="detail-body">
            <div className="detail-row">
              <span>Position:</span>
              <strong>{selectedHub.position.join(', ')}</strong>
            </div>
            <div className="detail-row">
              <span>Access:</span>
              <strong>{selectedHub.access}</strong>
            </div>
            <div className="detail-row">
              <span>Capacity:</span>
              <strong>{selectedHub.capacity}</strong>
            </div>
            <div className="detail-row">
              <span>Drones:</span>
              <strong>{selectedHub.drones.length}</strong>
            </div>
            <div className="detail-row">
              <span>Connections:</span>
              <strong>{selectedHub.connections.length}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Connection detail panel */}
      {selectedConnection && (
        <div className="detail-panel connection-panel">
          <div className="detail-header">
            <h4>Connection</h4>
            <button className="close-btn" onClick={() => setSelectedConnectionId(null)}>
              ✕
            </button>
          </div>
          <div className="detail-body">
            <div className="detail-row">
              <span>From:</span>
              <strong>{hubs.get(selectedConnection.hubs[0])?.name || 'Unknown'}</strong>
            </div>
            <div className="detail-row">
              <span>To:</span>
              <strong>{hubs.get(selectedConnection.hubs[1])?.name || 'Unknown'}</strong>
            </div>
            <div className="detail-row">
              <span>Capacity:</span>
              <strong>{selectedConnection.capacity}</strong>
            </div>
            <div className="detail-row">
              <span>Active Drones:</span>
              <strong>
                {
                  Array.from(drones.values()).filter(
                    (d) =>
                      (d.location === selectedConnection.hubs[0] &&
                        d.destination === selectedConnection.hubs[1]) ||
                      (d.location === selectedConnection.hubs[1] &&
                        d.destination === selectedConnection.hubs[0])
                  ).length
                }
              </strong>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
