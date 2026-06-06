import type { ResponseSimulation, ResponseHub, ResponseDrone, ResponseConnection } from '../types'

const API_BASE = import.meta.env.VITE_BACKEND_URL + "/api"

export async function generateToken(): Promise<string> {
  const response = await fetch(`${API_BASE}/token`)
  if (!response.ok) {
    throw new Error('Failed to generate token')
  }
  return response.json()
}

export async function createSimulation(token: string, file: File): Promise<ResponseSimulation> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/simulation?token=${encodeURIComponent(token)}`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to create simulation: ${error}`)
  }

  return response.json()
}

export async function getSimulation(token: string): Promise<ResponseSimulation> {
  const response = await fetch(`${API_BASE}/simulation?token=${encodeURIComponent(token)}`)
  
  if (!response.ok) {
    throw new Error('Simulation not found')
  }

  return response.json()
}

export async function advanceSimulation(token: string, steps: number = 1): Promise<ResponseSimulation> {
  const response = await fetch(
    `${API_BASE}/simulation/step?token=${encodeURIComponent(token)}&steps=${steps}`,
    { method: 'POST' }
  )

  if (!response.ok) {
    throw new Error('Failed to advance simulation')
  }

  return response.json()
}

export async function getHub(token: string, id: string): Promise<ResponseHub> {
  const response = await fetch(
    `${API_BASE}/hub?token=${encodeURIComponent(token)}&id=${encodeURIComponent(id)}`
  )

  if (!response.ok) {
    throw new Error('Hub not found')
  }

  return response.json()
}

export async function getDrone(token: string, id: string): Promise<ResponseDrone> {
  const response = await fetch(
    `${API_BASE}/drone?token=${encodeURIComponent(token)}&id=${encodeURIComponent(id)}`
  )

  if (!response.ok) {
    throw new Error('Drone not found')
  }

  return response.json()
}

export async function getConnection(token: string, id: string): Promise<ResponseConnection> {
  const response = await fetch(
    `${API_BASE}/connection?token=${encodeURIComponent(token)}&id=${encodeURIComponent(id)}`
  )

  if (!response.ok) {
    throw new Error('Connection not found')
  }

  return response.json()
}
