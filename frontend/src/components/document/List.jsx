import { useEffect, useState } from 'react'
import Row from './Row'
import DocumentModal from './DocumentModal'
import { useAuth } from '../../context/AuthContext'
import { SERVER_URL } from '../../config'

async function fetchDocuments(name) {
  const params = new URLSearchParams()
  if (name) params.set('name', name)
  const res = await fetch(`${SERVER_URL}/api/documents?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load documents')
  return res.json()
}

async function deleteDocument(id) {
  const res = await fetch(`${SERVER_URL}/api/documents/${id}`, { method: 'DELETE', credentials: 'include' })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || 'Failed to delete document')
  }
}

export default function List({ name = '' }) {
  const { user } = useAuth()
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [openDocument, setOpenDocument] = useState(null)
  const [scrollY, setScrollY] = useState(0)

  const load = () => {
    setLoading(true)
    fetchDocuments(name).then(setDocuments).finally(() => setLoading(false))
  }

  useEffect(load, [name])

  const openEdit = document => {
    setScrollY(window.scrollY)
    setOpenDocument(document)
  }

  const closeEdit = () => {
    setOpenDocument(null)
    requestAnimationFrame(() => window.scrollTo(0, scrollY))
  }

  const handleSaved = () => {
    load()
    closeEdit()
  }

  const handleDelete = async id => {
    if (!window.confirm('Delete this document?')) return
    try {
      await deleteDocument(id)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  if (loading) return <div className="document-spinner">Loading…</div>

  return (
    <div className="documents">
      {error && <div className="text-danger small mb-2">{error}</div>}
      {documents.length === 0 ? (
        <div className="text-muted small">No documents yet.</div>
      ) : (
        documents.map(document => (
          <Row
            key={document.id}
            document={document}
            isOwner={document.user_id === user?.id}
            onEdit={openEdit}
            onDelete={handleDelete}
          />
        ))
      )}
      {openDocument && (
        <DocumentModal
          document={openDocument}
          readOnly={openDocument.user_id !== user?.id}
          onSaved={handleSaved}
          onClose={closeEdit}
        />
      )}
    </div>
  )
}
