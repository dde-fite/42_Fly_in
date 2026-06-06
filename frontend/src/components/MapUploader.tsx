import { useRef, useState } from 'react'
import './MapUploader.css'

interface MapUploaderProps {
  onMapUploaded: (file: File) => void
  isLoading?: boolean
}

export default function MapUploader({ onMapUploaded, isLoading }: MapUploaderProps) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [fileName, setFileName] = useState<string>('')

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0]

    if (file && file.name.endsWith('.txt')) {
      setFileName(file.name)
      onMapUploaded(file)
      // Reset input
      if (fileInput.current) {
        fileInput.current.value = ''
      }
    } else {
      alert('Please select a .txt file')
    }
  }

  const triggerFileSelect = () => {
    fileInput.current?.click()
  }

  return (
    <div className="map-uploader">
      <h3>Map File</h3>
      <div className="upload-area">
        <input
          ref={fileInput}
          type="file"
          accept=".txt"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <button
          className="upload-btn"
          onClick={triggerFileSelect}
          disabled={isLoading}
        >
          {isLoading ? 'Loading...' : fileName || 'Upload Map'}
        </button>
      </div>
      {fileName && <div className="file-name">📄 {fileName}</div>}
    </div>
  )
}
