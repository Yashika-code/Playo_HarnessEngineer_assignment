import { useEffect, useState } from 'react'
import { Link, Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import { exportDocument, finalizeDocument, getDocument, listDocuments, retryDocument, subscribeToProgress, updateDocument, uploadDocuments } from './api'
import type { DocumentDetail, DocumentSummary, ProgressEvent } from './types'

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1024
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${value.toFixed(1)} ${units[index]}`
}

function statusClass(status: string): string {
  return `status status-${status}`
}

function UploadView() {
  const navigate = useNavigate()
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit() {
    if (files.length === 0) return
    setLoading(true)
    setError('')
    try {
      const result = await uploadDocuments(files)
      navigate(`/documents/${result.created[0].id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel hero-panel">
      <div>
        <p className="eyebrow">Async workflow</p>
        <h1>Upload documents and track processing live.</h1>
        <p className="muted">
          Documents are persisted immediately, queued in Celery, and streamed back through Redis Pub/Sub.
        </p>
      </div>
      <label className="dropzone">
        <input
          type="file"
          multiple
          onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
        />
        <span>{files.length > 0 ? `${files.length} file(s) selected` : 'Choose one or more files'}</span>
      </label>
      {error ? <div className="error-banner">{error}</div> : null}
      <button className="primary" onClick={submit} disabled={loading || files.length === 0}>
        {loading ? 'Uploading…' : 'Upload and process'}
      </button>
    </section>
  )
}

function DashboardView() {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState('desc')
  const [documents, setDocuments] = useState<DocumentSummary[]>([])

  useEffect(() => {
    let cancelled = false
    listDocuments({ query, status, sortBy, sortOrder }).then((items) => {
      if (!cancelled) setDocuments(items)
    })
    return () => {
      cancelled = true
    }
  }, [query, status, sortBy, sortOrder])

  return (
    <section className="panel">
      <div className="toolbar">
        <input placeholder="Search documents" value={query} onChange={(event) => setQuery(event.target.value)} />
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          <option value="queued">Queued</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="finalized">Finalized</option>
        </select>
        <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
          <option value="created_at">Created</option>
          <option value="updated_at">Updated</option>
          <option value="status">Status</option>
          <option value="progress_percent">Progress</option>
          <option value="filename">Filename</option>
        </select>
        <select value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
          <option value="desc">Newest first</option>
          <option value="asc">Oldest first</option>
        </select>
      </div>
      <div className="document-list">
        {documents.map((doc) => (
          <Link className="document-card" to={`/documents/${doc.id}`} key={doc.id}>
            <div>
              <h3>{doc.original_filename}</h3>
              <p>{formatBytes(doc.file_size)} · {doc.file_type}</p>
            </div>
            <div className={statusClass(doc.status)}>{doc.status}</div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${doc.progress_percent}%` }} />
            </div>
            <small>{doc.progress_step}</small>
          </Link>
        ))}
      </div>
    </section>
  )
}

function DocumentDetailView() {
  const { documentId } = useParams()
  const [document, setDocument] = useState<DocumentDetail | null>(null)
  const [draft, setDraft] = useState('')
  const [events, setEvents] = useState<ProgressEvent[]>([])

  useEffect(() => {
    if (!documentId) return
    getDocument(documentId).then((result) => {
      setDocument(result)
      setDraft(JSON.stringify(result.reviewed_data ?? result.extracted_data ?? {}, null, 2))
    })
  }, [documentId])

  useEffect(() => {
    if (!documentId) return
    return subscribeToProgress(documentId, (event) => {
      setEvents((current) => [event, ...current].slice(0, 8))
      setDocument((current) => current ? { ...current, status: event.status, progress_percent: event.progress_percent, progress_step: event.progress_step } : current)
    })
  }, [documentId])

  async function saveReview() {
    if (!documentId || !document) return
    const parsed = JSON.parse(draft) as Record<string, unknown>
    const updated = await updateDocument(documentId, parsed)
    setDocument(updated)
  }

  async function finalize() {
    if (!documentId) return
    await finalizeDocument(documentId)
    setDocument((current) => current ? { ...current, status: 'finalized' } : current)
  }

  async function retry() {
    if (!documentId) return
    await retryDocument(documentId)
  }

  if (!document) {
    return <section className="panel">Loading document…</section>
  }

  return (
    <section className="detail-grid">
      <div className="panel">
        <div className="detail-header">
          <div>
            <p className="eyebrow">Document detail</p>
            <h2>{document.original_filename}</h2>
            <p className="muted">{document.progress_step}</p>
          </div>
          <div className={statusClass(document.status)}>{document.status}</div>
        </div>
        <div className="progress-track large">
          <div className="progress-fill" style={{ width: `${document.progress_percent}%` }} />
        </div>
        <textarea value={draft} onChange={(event) => setDraft(event.target.value)} rows={18} />
        <div className="actions">
          <button className="secondary" onClick={saveReview}>Save review</button>
          <button className="primary" onClick={finalize}>Finalize</button>
          <button className="secondary" onClick={retry} disabled={document.status !== 'failed'}>Retry failed job</button>
          <a className="secondary link-button" href={exportDocument(document.id, 'json')}>Export JSON</a>
          <a className="secondary link-button" href={exportDocument(document.id, 'csv')}>Export CSV</a>
        </div>
      </div>
      <aside className="panel">
        <h3>Live events</h3>
        <div className="event-list">
          {events.map((event) => (
            <div key={`${event.event}-${event.progress_step}-${event.progress_percent}`} className="event-item">
              <strong>{event.event}</strong>
              <span>{event.message}</span>
              <small>{event.progress_step} · {event.progress_percent}%</small>
            </div>
          ))}
        </div>
        <details style={{marginTop:16}}>
          <summary>Raw API JSON</summary>
          <pre style={{whiteSpace: 'pre-wrap', maxHeight: 360, overflow: 'auto', background: '#fff', padding: 12, borderRadius: 8, marginTop: 8}}>
            {document ? JSON.stringify(document, null, 2) : 'loading...'}
          </pre>
        </details>
      </aside>
    </section>
  )
}

function HomePage() {
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="brand">Document Workflow</p>
          <p className="muted">FastAPI, Celery, Redis Pub/Sub, PostgreSQL, React</p>
        </div>
        <nav>
          <Link to="/">Upload</Link>
          <Link to="/dashboard">Dashboard</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<UploadView />} />
        <Route path="/dashboard" element={<DashboardView />} />
        <Route path="/documents/:documentId" element={<DocumentDetailView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  )
}

export default HomePage
