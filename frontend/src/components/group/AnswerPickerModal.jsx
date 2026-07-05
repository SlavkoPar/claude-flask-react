import { useState } from 'react'
import { Modal, Button } from 'react-bootstrap'
import { SERVER_URL } from '../../config'
import AsyncAutocomplete from '../common/AsyncAutocomplete'

async function fetchUnassigned(questionId, name) {
  const params = new URLSearchParams()
  if (name) params.set('name', name)
  const res = await fetch(
    `${SERVER_URL}/api/questions/${questionId}/answers/unassigned?${params.toString()}`,
    { credentials: 'include' }
  )
  if (!res.ok) throw new Error('Failed to load unassigned answers')
  const data = await res.json()
  return data.map(a => ({ id: a.id, label: a.short_desc }))
}

async function assign(questionId, answerId) {
  const res = await fetch(`${SERVER_URL}/api/questions/${questionId}/answers/assign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ answer_id: answerId }),
  })
  if (!res.ok) throw new Error('Failed to assign answer')
}

export default function AnswerPickerModal({ questionId, onAssigned, onClose }) {
  const [unassigned, setUnassigned] = useState([])
  const [error, setError] = useState(null)

  const handleAssign = async answerId => {
    try {
      await assign(questionId, answerId)
      setUnassigned(list => list.filter(a => a.id !== answerId))
      onAssigned?.()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <Modal show onHide={onClose} dialogClassName="answer-picker-modal" centered>
      <Modal.Header closeButton>
        <Modal.Title>Assign answer</Modal.Title>
      </Modal.Header>
      <Modal.Body className="answer-picker-modal-body">
        {error && <div className="text-danger small mb-2">{error}</div>}
        <AsyncAutocomplete
          className="form-input mb-2"
          placeholder="Filter by name"
          fetchOptions={query => fetchUnassigned(questionId, query)}
          onResults={setUnassigned}
        />
        {unassigned.length === 0 ? (
          <div className="text-muted small">No unassigned answers.</div>
        ) : (
          unassigned.map(a => (
            <div key={a.id} className="answer-row">
              <span className="answer-row-title">{a.label}</span>
              <Button variant="outline-primary" size="sm" onClick={() => handleAssign(a.id)}>Assign</Button>
            </div>
          ))
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button type="button" variant="outline-secondary" onClick={onClose}>Close</Button>
      </Modal.Footer>
    </Modal>
  )
}
