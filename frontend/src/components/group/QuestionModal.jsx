import { useState } from 'react'
import { Modal, Form, Button, Alert } from 'react-bootstrap'
import { SERVER_URL } from '../../config'
import AssignedAnswersSection from './AssignedAnswersSection'

async function saveQuestion(groupId, question, values) {
  const isEdit = Boolean(question?.id)
  const res = await fetch(
    isEdit ? `${SERVER_URL}/api/questions/${question.id}` : `${SERVER_URL}/api/questions`,
    {
      method: isEdit ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(isEdit ? values : { ...values, group_id: groupId }),
    }
  )
  const data = await res.json()
  if (!res.ok) throw Object.assign(new Error(data.error), { values: data.values })
  return data
}

export default function QuestionModal({ groupId, question, onSaved, onClose }) {
  const [values, setValues] = useState({
    text: question?.text || '',
    description: question?.description || '',
  })
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async e => {
    e.preventDefault()
    e.stopPropagation()
    setSaving(true)
    setError(null)
    try {
      await saveQuestion(groupId, question, values)
      onSaved()
    } catch (err) {
      setError(err.message)
      if (err.values) setValues(v => ({ ...v, ...err.values }))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal show onHide={onClose} dialogClassName="question-modal" centered>
      <Modal.Header closeButton>
        <Modal.Title>{question ? 'Edit question' : 'Add question'}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit}>
        <Modal.Body className="question-modal-body">
          {error && <Alert variant="danger">{error}</Alert>}
          <Form.Group className="mb-3">
            <Form.Label>Text</Form.Label>
            <Form.Control
              value={values.text}
              onChange={e => setValues(v => ({ ...v, text: e.target.value }))}
              autoFocus
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={values.description}
              onChange={e => setValues(v => ({ ...v, description: e.target.value }))}
            />
          </Form.Group>
          {question?.id ? (
            <AssignedAnswersSection questionId={question.id} />
          ) : (
            <div className="text-muted small">Save the question first to assign answers.</div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button type="button" variant="outline-secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={saving}>Save</Button>
        </Modal.Footer>
      </Form>
    </Modal>
  )
}
