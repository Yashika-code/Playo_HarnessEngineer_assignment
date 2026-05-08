export type DocumentStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'finalized'

export type DocumentSummary = {
  id: string
  original_filename: string
  file_type: string
  file_size: number
  status: DocumentStatus
  progress_step: string
  progress_percent: number
  created_at: string
  updated_at: string
  finalized_at: string | null
}

export type DocumentDetail = DocumentSummary & {
  storage_path: string
  extracted_data: Record<string, unknown> | null
  reviewed_data: Record<string, unknown> | null
  finalized_data: Record<string, unknown> | null
  error_message: string | null
  completed_at: string | null
}

export type ProgressEvent = {
  document_id: string
  event: string
  status: DocumentStatus
  progress_percent: number
  progress_step: string
  message?: string
  payload?: Record<string, unknown>
}
