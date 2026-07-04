import { useEffect, useState } from 'react'
import { Modal, Form, Button } from 'react-bootstrap'
import { SERVER_URL } from '../../config'

async function fetchAssigned(questionId) {
  const res = await fetch(`${SERVER_URL}/api/questions/${questionId}/answers`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load assigned answers')
  return res.json()
}

async function fetchUnassigned(questionId, name) {
  const params = new URLSearchParams()
  if (name) params.set('name', name)
  const res = await fetch(
    `${SERVER_URL}/api/questions/${questionId}/answers/unassigned?${params.toString()}`,
    { credentials: 'include' }
  )
  if (!res.ok) throw new Error('Failed to load unassigned answers')
  return res.json()
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

async function unassign(questionId, answerId) {
  const res = await fetch(`${SERVER_URL}/api/questions/${questionId}/answers/${answerId}/unassign`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to unassign answer')
}

export default function AssignedAnswersModal({ questionId, onChange, onClose }) {
  const [assigned, setAssigned] = useState([])
  const [unassigned, setUnassigned] = useState([])
  const [filter, setFilter] = useState('')
  const [error, setError] = useState(null)

  const load = () => {
    fetchAssigned(questionId).then(setAssigned)
    fetchUnassigned(questionId, filter).then(setUnassigned)
  }

  useEffect(load, [questionId, filter])

  const handleAssign = async answerId => {
    try {
      await assign(questionId, answerId)
      load()
      onChange?.()
    } catch (e) {
      setError(e.message)
    }
  }

  const handleUnassign = async answerId => {
    try {
      await unassign(questionId, answerId)
      load()
      onChange?.()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <Modal show onHide={onClose} dialogClassName="assigned-answers-modal" centered>
      <Modal.Header closeButton>
        <Modal.Title>Assigned answers</Modal.Title>
      </Modal.Header>
      <Modal.Body className="assigned-answers-modal-body">
        {error && <div className="text-danger small mb-2">{error}</div>}

        <h6>Assigned</h6>
        {assigned.length === 0 ? (
          <div className="text-muted small mb-3">No answers assigned yet.</div>
        ) : (
          <div className="mb-3">
            {assigned.map(a => (
              <div key={a.id} className="assigned-answer-row">
                <span className="answer-row-title">{a.short_desc}</span>
                <Button variant="outline-danger" size="sm" onClick={() => handleUnassign(a.id)}>Remove</Button>
              </div>
            ))}
          </div>
        )}

        <h6>Add answer</h6>
        <Form.Control
          className="form-input mb-2"
          placeholder="Filter by name"
          list="unassigned-answer-suggestions"
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
        <datalist id="unassigned-answer-suggestions">
          {unassigned.map(a => (
            <option key={a.id} value={a.short_desc} />
          ))}
        </datalist>
        {unassigned.length === 0 ? (
          <div className="text-muted small">No unassigned answers.</div>
        ) : (
          unassigned.map(a => (
            <div key={a.id} className="answer-row">
              <span className="answer-row-title">{a.short_desc}</span>
              <Button variant="outline-primary" size="sm" onClick={() => handleAssign(a.id)}>Add</Button>
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
