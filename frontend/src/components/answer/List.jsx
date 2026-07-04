import { useEffect, useState } from 'react'
import Row from './Row'
import AnswerModal from './AnswerModal'
import { SERVER_URL } from '../../config'

async function fetchAnswers(name) {
  const params = new URLSearchParams()
  if (name) params.set('name', name)
  const res = await fetch(`${SERVER_URL}/api/answers?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load answers')
  return res.json()
}

async function deleteAnswer(id) {
  const res = await fetch(`${SERVER_URL}/api/answers/${id}`, { method: 'DELETE', credentials: 'include' })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || 'Failed to delete answer')
  }
}

export default function List({ name = '' }) {
  const [answers, setAnswers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editAnswer, setEditAnswer] = useState(null)
  const [scrollY, setScrollY] = useState(0)

  const load = () => {
    setLoading(true)
    fetchAnswers(name).then(setAnswers).finally(() => setLoading(false))
  }

  useEffect(load, [name])

  const openEdit = answer => {
    setScrollY(window.scrollY)
    setEditAnswer(answer)
  }

  const closeEdit = () => {
    setEditAnswer(null)
    requestAnimationFrame(() => window.scrollTo(0, scrollY))
  }

  const handleSaved = () => {
    load()
    closeEdit()
  }

  const handleDelete = async id => {
    if (!window.confirm('Delete this answer?')) return
    try {
      await deleteAnswer(id)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  if (loading) return <div className="answer-spinner">Loading…</div>

  return (
    <div className="answers">
      {error && <div className="text-danger small mb-2">{error}</div>}
      {answers.length === 0 ? (
        <div className="text-muted small">No answers yet.</div>
      ) : (
        answers.map(answer => (
          <Row key={answer.id} answer={answer} onEdit={openEdit} onDelete={handleDelete} />
        ))
      )}
      {editAnswer && (
        <AnswerModal answer={editAnswer} onSaved={handleSaved} onClose={closeEdit} />
      )}
    </div>
  )
}
