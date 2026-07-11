import { useEffect, useState } from 'react'
import GroupSection from './GroupSection'
import DocumentModal from './DocumentModal'
import { useAuth } from '../../context/AuthContext'
import { SERVER_URL } from '../../config'

async function fetchDocuments(name, groupId) {
  const params = new URLSearchParams()
  if (name) params.set('name', name)
  if (groupId) params.set('group_id', groupId)
  const res = await fetch(`${SERVER_URL}/api/documents?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load documents')
  return res.json()
}

function groupByGroup(documents) {
  const groups = new Map()
  for (const document of documents) {
    if (!groups.has(document.group_id)) {
      groups.set(document.group_id, { id: document.group_id, name: document.group_name, documents: [] })
    }
    groups.get(document.group_id).documents.push(document)
  }
  return [...groups.values()].sort((a, b) => a.name.localeCompare(b.name))
}

async function deleteDocument(id) {
  const res = await fetch(`${SERVER_URL}/api/documents/${id}`, { method: 'DELETE', credentials: 'include' })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || 'Failed to delete document')
  }
}

export default function List({ name = '', groupId = null }) {
  const { user } = useAuth()
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [openDocument, setOpenDocument] = useState(null)
  const [scrollY, setScrollY] = useState(0)

  const load = () => {
    setLoading(true)
    fetchDocuments(name, groupId).then(setDocuments).catch(e => setError(e.message)).finally(() => setLoading(false))
  }

  useEffect(load, [name, groupId])

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

  const groups = groupByGroup(documents)

  return (
    <div className="documents">
      {error && <div className="text-danger small mb-2">{error}</div>}
      {documents.length === 0 ? (
        <div className="text-muted small">No documents yet.</div>
      ) : (
        groups.map(group => (
          <GroupSection
            key={group.id}
            group={group}
            currentUserId={user?.id}
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
