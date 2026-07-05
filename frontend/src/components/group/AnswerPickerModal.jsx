import { useEffect, useState } from 'react'
import { Modal, Form, Button } from 'react-bootstrap'
import { SERVER_URL } from '../../config'

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

export default function AnswerPickerModal({ questionId, onAssigned, onClose }) {
  const [unassigned, setUnassigned] = useState([])
  const [filter, setFilter] = useState('')
  const [error, setError] = useState(null)

  const load = () => {
    fetchUnassigned(questionId, filter).then(setUnassigned).catch(e => setError(e.message))
  }

  useEffect(load, [questionId, filter])

  const handleAssign = async answerId => {
    try {
      await assign(questionId, answerId)
      load()
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
        <Form.Control
          className="form-input mb-2"
          placeholder="Filter by name"
          list="unassigned-answer-suggestions"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          autoFocus
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
