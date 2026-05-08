import type { DocumentDetail, DocumentSummary, ProgressEvent } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || response.statusText)
  }
  return response.json() as Promise<T>
}

export async function uploadDocuments(files: File[]): Promise<{ created: DocumentSummary[] }> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  const response = await fetch(`${API_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    throw new Error(await response.text())
  }
  return response.json()
}

export async function listDocuments(params: { query?: string; status?: string; sortBy?: string; sortOrder?: string }): Promise<DocumentSummary[]> {
  const search = new URLSearchParams()
  if (params.query) search.set('query', params.query)
  if (params.status) search.set('status', params.status)
  if (params.sortBy) search.set('sort_by', params.sortBy)
  if (params.sortOrder) search.set('sort_order', params.sortOrder)
  const queryString = search.toString()
  return request(`/documents${queryString ? `?${queryString}` : ''}`)
}

export function getDocument(documentId: string): Promise<DocumentDetail> {
  return request(`/documents/${documentId}`)
}

export async function updateDocument(documentId: string, reviewedData: Record<string, unknown>): Promise<DocumentDetail> {
  return request(`/documents/${documentId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewed_data: reviewedData }),
  })
}

export async function finalizeDocument(documentId: string): Promise<{ status: string }> {
  return request(`/documents/${documentId}/finalize`, { method: 'POST' })
}

export async function retryDocument(documentId: string): Promise<{ status: string }> {
  return request(`/documents/${documentId}/retry`, { method: 'POST' })
}

export function exportDocument(documentId: string, format: 'json' | 'csv'): string {
  return `${API_URL}/documents/${documentId}/export?format=${format}`
}

export function subscribeToProgress(documentId: string, onEvent: (event: ProgressEvent) => void): () => void {
  const source = new EventSource(`${API_URL}/documents/${documentId}/events`)
  source.onmessage = (event) => {
    onEvent(JSON.parse(event.data) as ProgressEvent)
  }
  return () => source.close()
}
