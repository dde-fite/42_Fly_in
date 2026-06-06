import { useState } from 'react'
import './Controls.css'

interface ControlsProps {
  onAdvanceSteps: (steps: number) => void
  isLoading?: boolean
}

export default function Controls({ onAdvanceSteps, isLoading }: ControlsProps) {
  const [steps, setSteps] = useState(1)

  const handleAdvance = () => {
    onAdvanceSteps(steps)
  }

  const quickStep = (count: number) => {
    onAdvanceSteps(count)
  }

  return (
    <div className="controls">
      <h3>Simulation Control</h3>

      <div className="control-section">
        <label htmlFor="steps">Steps</label>
        <div className="input-group">
          <input
            id="steps"
            type="number"
            min="1"
            max="100"
            value={steps}
            onChange={(e) => setSteps(parseInt(e.target.value) || 1)}
            disabled={isLoading}
          />
          <button className="advance-btn" onClick={handleAdvance} disabled={isLoading}>
            ▶ Advance
          </button>
        </div>
      </div>

      <div className="quick-buttons">
        {[1, 5, 10].map((count) => (
          <button
            key={count}
            className="quick-btn"
            onClick={() => quickStep(count)}
            disabled={isLoading}
          >
            +{count}
          </button>
        ))}
      </div>
    </div>
  )
}
