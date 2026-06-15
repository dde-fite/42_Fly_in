import { useRef, useState } from 'react'
import './MapUploader.css'

interface MapUploaderProps {
  onMapUploaded: (file: File) => void
  isLoading?: boolean
}

export default function MapUploader({ onMapUploaded, isLoading }: MapUploaderProps) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [fileName, setFileName] = useState<string>('')

  const handleMapUploaded = async (file: File) => {
    try {
      setIsLoading(true)
      setError('')

      const sim = await createSimulation(file)
      // Store both simulation and token together to avoid desync
      setsimulation({ data: sim, token })
    } catch (err: any) {
      setError(err.message || 'Failed to create simulation')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

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
    <div className="upload-area">
      <input
        ref={fileInput}
        type="file"
        accept=".txt"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
      <button
        className="relative overflow-hidden px-5 py-2.5 bg-gray-900 text-white rounded transition-all duration-300 cursor-pointer hover:bg-neutral-800 hover:ring-4 hover:ring-neutral-800 hover:ring-offset-1 active:ring-0"
        onClick={triggerFileSelect}
        disabled={isLoading}
      >
        <span className="relative">
          {isLoading ? 'Loading...' : fileName || 'New simulation'}
        </span>
      </button>
    </div>
  )
}
