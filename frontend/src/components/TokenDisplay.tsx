import { useState } from 'react'
import { useSessionStore } from '../store/sessionStore'
import './TokenDisplay.css'

interface TokenDisplayProps {
  onClose: () => void
}

export default function TokenDisplay({ onClose }: TokenDisplayProps) {
  const [copied, setCopied] = useState(false)
  const token = useSessionStore(state => state.token) ?? ""

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(token)
      setCopied(true)
      setTimeout(() => {
        setCopied(false)
      }, 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="token-modal" onClick={(e) => e.stopPropagation()}>
      <div className="modal-content">
        <div className="modal-header">
          <h2>Session Token</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          <p className="token-label">Current Token:</p>
          <div className="token-display">
            <code className='select-all'>{token}</code>
            <button className="copy-btn" onClick={copyToClipboard}>
              {copied ? '✓ Copied' : 'Copy'}
            </button>
          </div>
          <p className="token-info">
            This token identifies your simulation session. Use it to continue working with the same
            map and drone configuration.
          </p>
        </div>

        <div className="modal-footer">
          <button className="ok-btn" onClick={onClose}>
            OK
          </button>
        </div>
      </div>
    </div>
  )
}
