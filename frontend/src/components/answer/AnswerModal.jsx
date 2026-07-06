import { useState } from 'react'
import { Modal, Form, Button, Alert } from 'react-bootstrap'
import { SERVER_URL } from '../../config'

async function saveAnswer(answer, values) {
  const isEdit = Boolean(answer?.id)
  const res = await fetch(
    isEdit ? `${SERVER_URL}/api/answers/${answer.id}` : `${SERVER_URL}/api/answers`,
    {
      method: isEdit ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(values),
    }
  )
  const data = await res.json()
  if (!res.ok) throw Object.assign(new Error(data.error), { values: data.values })
  return data
}

export default function AnswerModal({ answer, onSaved, onClose }) {
  const [values, setValues] = useState({
    short_desc: answer?.short_desc || '',
    description: answer?.description || '',
    link: answer?.link || '',
  })
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async e => {
    e.preventDefault()
    e.stopPropagation()
    setSaving(true)
    setError(null)
    try {
      await saveAnswer(answer, values)
      onSaved()
    } catch (err) {
      setError(err.message)
      if (err.values) setValues(v => ({ ...v, ...err.values }))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal show onHide={onClose} dialogClassName="answer-modal" centered>
      <Modal.Header closeButton>
        <Modal.Title>{answer ? 'Edit answer' : 'Add answer'}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit}>
        <Modal.Body className="answer-modal-body">
          {error && <Alert variant="danger">{error}</Alert>}
          <Form.Group className="mb-3">
            <Form.Label>Short description</Form.Label>
            <Form.Control
              className="form-input"
              value={values.short_desc}
              onChange={e => setValues(v => ({ ...v, short_desc: e.target.value }))}
              autoFocus
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              className="form-input"
              value={values.description}
              onChange={e => setValues(v => ({ ...v, description: e.target.value }))}
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Link</Form.Label>
            <Form.Control
              className="form-input"
              value={values.link}
              onChange={e => setValues(v => ({ ...v, link: e.target.value }))}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button type="button" variant="outline-secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={saving}>Save</Button>
        </Modal.Footer>
      </Form>
    </Modal>
  )
}
